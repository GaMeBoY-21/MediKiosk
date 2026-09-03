# Owner: Tharun
"""Physician console: queue, case review, verification, FHIR.

POST /verify is the canonical action and holds all the logic. The confirm,
reject and PUT routes are thin aliases that delegate to it, because the console
already calls those three; keeping one code path means one audit call site.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app import fixtures, models
from app.database import get_db
from app.fhir import build_fhir_bundle
from app.routers.auth import require_clinician
from app.routers.session import load_session
from app.routers.summary import _build_summary, current_red_flags
from app.schemas import (
    ClinicalSummary,
    DocumentRecord,
    FlatSummary,
    PhysicianCaseResponse,
    PhysicianPatient,
    PhysicianQueueItem,
    SessionStatus,
    VerifyAction,
    VerifyRequest,
    VerifyResponse,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/physician", tags=["physician"])


# Worst first, matching app/ai_bridge.py's ranking.
_SEVERITY_ORDER = {"critical": 0, "high": 1, "moderate": 2, "low": 3}


def _worst_flag_label(flags: List[Dict[str, Any]]) -> str | None:
    """Label of the most severe flag on a session, or None.

    The queue row shows one flag. Showing whichever fired first would let a
    critical hide behind an earlier moderate.
    """
    if not flags:
        return None
    worst = min(flags, key=lambda f: _SEVERITY_ORDER.get(f.get("severity", "low"), 99))
    return worst.get("label")


def _flatten(summary: ClinicalSummary) -> FlatSummary:
    """ClinicalSummary -> the seven flat keys the console renders.

    The rich model stays canonical; this is the console's view of it.
    """
    sections = summary.sections or {}
    return FlatSummary(
        chief_complaint=summary.chief_complaint or "",
        hpi=summary.hpi_narrative or "",
        past_history=sections.get("past_history", ""),
        drugs_allergies=sections.get("drugs_allergies", ""),
        family=sections.get("family", ""),
        personal=sections.get("personal", ""),
        ros=sections.get("ros", ""),
    )


def _bundle_for(db: DbSession, row: models.Session, summary: ClinicalSummary) -> Dict[str, Any]:
    """Build the FHIR bundle for one session.

    Structured history comes from the clinical record when it exists; the demo
    history stands in until ai/ populates it. Conditions, medications and
    allergies are built from those lists, never parsed out of the prose sections.
    """
    record = (
        db.query(models.ClinicalRecord)
        .filter(models.ClinicalRecord.session_id == row.session_id)
        .one_or_none()
    )
    history = (record.history if record and record.history else None) or fixtures.DEMO_HISTORY

    return build_fhir_bundle(
        summary,
        patient_id=row.session_id,
        history=history,
        patient={
            "name": row.patient_name or fixtures.DEMO_PATIENT["name"],
            "age": row.age or fixtures.DEMO_PATIENT["age"],
            "sex": row.sex or fixtures.DEMO_PATIENT["sex"],
            "abha": row.abha_id or fixtures.DEMO_PATIENT["abha"],
        },
    )


def _load_summary(db: DbSession, row: models.Session) -> ClinicalSummary:
    record = (
        db.query(models.ClinicalRecord)
        .filter(models.ClinicalRecord.session_id == row.session_id)
        .one_or_none()
    )
    if record is not None and record.summary:
        summary = ClinicalSummary.model_validate(record.summary)
        # Live flags win over the snapshot - see current_red_flags().
        summary.red_flags = current_red_flags(db, row.session_id) or summary.red_flags
        return summary
    return _build_summary(row, db)


def _case_response(db: DbSession, row: models.Session) -> PhysicianCaseResponse:
    summary = _load_summary(db, row)

    mocked: List[str] = []
    if not row.patient_name:
        mocked.append("name")
    if row.age is None:
        mocked.append("age")
    if not row.sex:
        mocked.append("sex")
    if not row.abha_id:
        mocked.append("abha")

    return PhysicianCaseResponse(
        session_id=row.session_id,
        token=row.token,
        room=row.room,
        patient=PhysicianPatient(
            name=row.patient_name or fixtures.DEMO_PATIENT["name"],
            age=row.age or fixtures.DEMO_PATIENT["age"],
            sex=row.sex or fixtures.DEMO_PATIENT["sex"],
            abha=row.abha_id or fixtures.DEMO_PATIENT["abha"],
        ),
        summary=_flatten(summary),
        documents=summary.document_timeline,
        red_flags=current_red_flags(db, row.session_id),
        low_confidence_fields=summary.low_confidence_fields,
        mocked_fields=mocked,
        fhir=_bundle_for(db, row, summary),
        verified_by=summary.verified_by,
        verified_at=summary.verified_at,
    )


# /queue must be declared before /{session_id}, or "queue" is captured as an id.
@router.get("/queue", response_model=List[PhysicianQueueItem])
def physician_queue(db: DbSession = Depends(get_db), claims: dict = Depends(require_clinician)):
    """Waiting patients, red-flagged first.

    Ordering is the whole point of this screen: a doctor with 90 seconds should
    never have to scan for the urgent row.
    """
    rows = (
        db.query(models.Session)
        .filter(models.Session.status != SessionStatus.rejected.value)
        .order_by(models.Session.created_at)
        .all()
    )

    items: List[PhysicianQueueItem] = []
    for row in rows:
        record = (
            db.query(models.ClinicalRecord)
            .filter(models.ClinicalRecord.session_id == row.session_id)
            .one_or_none()
        )
        flags = (record.red_flags if record else None) or []
        history = (record.history if record else None) or {}
        stored = (record.summary if record else None) or {}

        # The patient's actual words, not a fixture. Prefer the generated
        # summary's one-liner, fall back to the extracted field.
        complaint = stored.get("chief_complaint") or history.get("chief_complaint")

        items.append(
            PhysicianQueueItem(
                session_id=row.session_id,
                token=row.token,
                # Demographics are still demo values; the case view names them
                # in mocked_fields. Left as the row's own (possibly empty)
                # values here rather than inventing a name per queue row.
                name=row.patient_name or history.get("patient_name"),
                age=row.age if row.age is not None else history.get("age"),
                sex=row.sex or history.get("sex"),
                complaint=str(complaint) if complaint else None,
                # Worst flag, not merely the first: a critical must not be
                # hidden behind a high that happened to be recorded earlier.
                red_flag=_worst_flag_label(flags),
                waiting_since=row.created_at.strftime("%H:%M") if row.created_at else None,
            )
        )

    # No demo rows. An empty queue means no patient has finished an intake —
    # which is the truth, and far better than a doctor scanning invented
    # patients. The console renders its own empty state.
    items.sort(key=lambda i: (i.red_flag is None, i.waiting_since or ""))
    return items


@router.get("/token/{token}", response_model=PhysicianCaseResponse)
def fetch_case_by_token(token: str, db: DbSession = Depends(get_db), claims: dict = Depends(require_clinician)):
    """Open one patient by the token printed on the kiosk Done screen."""
    wanted = token.strip().upper()
    rows = (
        db.query(models.Session)
        .filter(models.Session.token == wanted, models.Session.status != SessionStatus.rejected.value)
        .order_by(models.Session.created_at.desc())
        .all()
    )
    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown patient token {wanted}")
    if len(rows) > 1:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"patient token {wanted} is not unique; select from the queue",
        )
    row = rows[0]
    models.write_audit(db, action="physician.read_by_token", actor=claims.get("sub", "physician"), session_id=row.session_id)
    db.commit()
    return _case_response(db, row)


@router.get("/{session_id}", response_model=PhysicianCaseResponse)
def fetch_case(session_id: str, db: DbSession = Depends(get_db), claims: dict = Depends(require_clinician)):
    """Everything the console renders for one patient, FHIR bundle included."""
    row = load_session(db, session_id)

    models.write_audit(db, action="physician.read", actor=claims.get("sub", "physician"), session_id=session_id)
    db.commit()
    return _case_response(db, row)


@router.post("/{session_id}/verify", response_model=VerifyResponse)
def verify_case(session_id: str, payload: VerifyRequest, db: DbSession = Depends(get_db), claims: dict = Depends(require_clinician)):
    """Accept, amend or reject a draft record. The canonical write path.

    Nothing leaves this system until action=accept lands here — that is what the
    console's unverified-draft banner promises the doctor.
    """
    row = load_session(db, session_id)
    record = (
        db.query(models.ClinicalRecord)
        .filter(models.ClinicalRecord.session_id == session_id)
        .one_or_none()
    )
    if record is None:
        record = models.ClinicalRecord(
            session_id=session_id, history={}, summary=_build_summary(row, db).model_dump(mode="json")
        )
        db.add(record)
        db.flush()

    summary = ClinicalSummary.model_validate(record.summary or {})
    now = datetime.now(timezone.utc)

    if payload.action is VerifyAction.amend:
        # Amendments edit the draft; they do not verify it.
        sections = dict(summary.sections or {})
        for key, value in payload.amendments.items():
            if key == "chief_complaint":
                summary.chief_complaint = value
            elif key == "hpi":
                summary.hpi_narrative = value
            else:
                sections[key] = value
        summary.sections = sections
        row.status = SessionStatus.awaiting_physician.value

    elif payload.action is VerifyAction.accept:
        summary.verified_by = payload.physician_id or "physician"
        summary.verified_at = now
        record.verified_by = summary.verified_by
        record.verified_at = now
        row.status = SessionStatus.verified.value

    elif payload.action is VerifyAction.reject:
        summary.verified_by = None
        summary.verified_at = None
        row.status = SessionStatus.rejected.value

    record.summary = summary.model_dump(mode="json")
    models.write_audit(
        db,
        action=f"physician.{payload.action.value}",
        actor=payload.physician_id or "physician",
        session_id=session_id,
        detail={"reason": payload.reason, "amended": sorted(payload.amendments)},
    )
    db.commit()

    return VerifyResponse(
        ok=True,
        status=SessionStatus(row.status),
        verified_by=summary.verified_by,
        verified_at=summary.verified_at,
    )


# ------------------------------------------------------------------ aliases
# The console already calls these three. They delegate to verify_case so there
# is exactly one place where a record is accepted, amended or rejected.


@router.post("/{session_id}/confirm", response_model=VerifyResponse)
def confirm_case(session_id: str, db: DbSession = Depends(get_db), claims: dict = Depends(require_clinician)):
    """Alias for verify(accept)."""
    return verify_case(session_id, VerifyRequest(action=VerifyAction.accept), db)


@router.post("/{session_id}/reject", response_model=VerifyResponse)
def reject_case(session_id: str, payload: Dict[str, Any] | None = None, db: DbSession = Depends(get_db), claims: dict = Depends(require_clinician)):
    """Alias for verify(reject)."""
    reason = (payload or {}).get("reason")
    return verify_case(session_id, VerifyRequest(action=VerifyAction.reject, reason=reason), db)


@router.put("/{session_id}", response_model=VerifyResponse)
def amend_case(session_id: str, payload: Dict[str, str], db: DbSession = Depends(get_db), claims: dict = Depends(require_clinician)):
    """Alias for verify(amend). The console PUTs one edited field at a time."""
    amendments = {k: str(v) for k, v in (payload or {}).items() if k != "action"}
    return verify_case(session_id, VerifyRequest(action=VerifyAction.amend, amendments=amendments), db)


@router.get("/{session_id}/fhir")
def fetch_fhir(session_id: str, db: DbSession = Depends(get_db), claims: dict = Depends(require_clinician)) -> Dict[str, Any]:
    """The FHIR R4 bundle as raw JSON, for the console's collapsible panel."""
    row = load_session(db, session_id)
    summary = _load_summary(db, row)

    models.write_audit(db, action="fhir.read", actor=claims.get("sub", "physician"), session_id=session_id)
    db.commit()
    return _bundle_for(db, row, summary)

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

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app import fixtures, models
from app.database import get_db
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


def _safe_fhir(summary: ClinicalSummary, patient_id: str) -> Dict[str, Any]:
    """Build the FHIR bundle, tolerating app/fhir.py not being written yet.

    TODO(block 5): drop the guard once build_fhir_bundle is implemented. Until
    then the console's FHIR panel shows an empty Bundle rather than 500-ing the
    whole case view.

    TypeError is caught alongside NotImplementedError because the current stub
    still has the scaffold's one-argument signature.
    """
    from app.fhir import build_fhir_bundle

    try:
        return build_fhir_bundle(summary, patient_id=patient_id)
    except (NotImplementedError, TypeError):
        log.info("fhir builder not implemented yet; returning empty bundle")
        return {"resourceType": "Bundle", "type": "document", "entry": []}


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


# /queue must be declared before /{session_id}, or "queue" is captured as an id.
@router.get("/queue", response_model=List[PhysicianQueueItem])
def physician_queue(db: DbSession = Depends(get_db)):
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
        items.append(
            PhysicianQueueItem(
                session_id=row.session_id,
                token=row.token,
                name=row.patient_name,
                age=row.age,
                sex=row.sex,
                complaint=fixtures.DEMO_CHIEF_COMPLAINT,
                red_flag=flags[0].get("label") if flags else None,
                waiting_since=row.created_at.strftime("%H:%M") if row.created_at else None,
            )
        )

    # Demo rows so the console is never empty before a kiosk run.
    # TODO(block 4): drop once real sessions populate the queue.
    if not items:
        items = [PhysicianQueueItem(**p) for p in fixtures.DEMO_QUEUE]

    items.sort(key=lambda i: (i.red_flag is None, i.waiting_since or ""))
    return items


@router.get("/{session_id}", response_model=PhysicianCaseResponse)
def fetch_case(session_id: str, db: DbSession = Depends(get_db)):
    """Everything the console renders for one patient, FHIR bundle included."""
    row = load_session(db, session_id)
    summary = _load_summary(db, row)

    models.write_audit(db, action="physician.read", actor="physician", session_id=session_id)
    db.commit()

    return PhysicianCaseResponse(
        session_id=session_id,
        patient=PhysicianPatient(
            name=row.patient_name or fixtures.DEMO_PATIENT["name"],
            age=row.age or fixtures.DEMO_PATIENT["age"],
            sex=row.sex or fixtures.DEMO_PATIENT["sex"],
            abha=row.abha_id or fixtures.DEMO_PATIENT["abha"],
        ),
        summary=_flatten(summary),
        documents=summary.document_timeline or [DocumentRecord(**d) for d in fixtures.DEMO_DOCUMENTS],
        red_flags=summary.red_flags,
        fhir=_safe_fhir(summary, session_id),
        verified_by=summary.verified_by,
        verified_at=summary.verified_at,
    )


@router.post("/{session_id}/verify", response_model=VerifyResponse)
def verify_case(session_id: str, payload: VerifyRequest, db: DbSession = Depends(get_db)):
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
def confirm_case(session_id: str, db: DbSession = Depends(get_db)):
    """Alias for verify(accept)."""
    return verify_case(session_id, VerifyRequest(action=VerifyAction.accept), db)


@router.post("/{session_id}/reject", response_model=VerifyResponse)
def reject_case(session_id: str, payload: Dict[str, Any] | None = None, db: DbSession = Depends(get_db)):
    """Alias for verify(reject)."""
    reason = (payload or {}).get("reason")
    return verify_case(session_id, VerifyRequest(action=VerifyAction.reject, reason=reason), db)


@router.put("/{session_id}", response_model=VerifyResponse)
def amend_case(session_id: str, payload: Dict[str, str], db: DbSession = Depends(get_db)):
    """Alias for verify(amend). The console PUTs one edited field at a time."""
    amendments = {k: str(v) for k, v in (payload or {}).items() if k != "action"}
    return verify_case(session_id, VerifyRequest(action=VerifyAction.amend, amendments=amendments), db)


@router.get("/{session_id}/fhir")
def fetch_fhir(session_id: str, db: DbSession = Depends(get_db)) -> Dict[str, Any]:
    """The FHIR R4 bundle as raw JSON, for the console's collapsible panel."""
    row = load_session(db, session_id)
    summary = _load_summary(db, row)

    models.write_audit(db, action="fhir.read", actor="physician", session_id=session_id)
    db.commit()
    return _safe_fhir(summary, session_id)

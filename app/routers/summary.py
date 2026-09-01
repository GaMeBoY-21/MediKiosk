# Owner: Tharun
"""Summary generation and retrieval."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from typing import List

from app import ai_bridge, fixtures, models
from app.database import get_db
from app.routers.auth import require_clinician
from app.routers.session import load_session
from app.schemas import ClinicalSummary, DocumentRecord, ExtractedField, FieldSource, RedFlag
from app.session_store import store

log = logging.getLogger(__name__)
router = APIRouter(prefix="/summary", tags=["summary"])


def _build_summary(row: models.Session, db: DbSession | None = None) -> ClinicalSummary:
    """Assemble the draft summary.

    verified_by stays None: this is a draft until a physician accepts it, and
    the console's 'Unverified draft' banner keys off exactly that.
    """
    state = store.get(row.session_id)

    extracted_fields = [
        ExtractedField(
            name=name,
            value=value,
            confidence=(state.field_confidence.get(name, 1.0) if state else 1.0),
            source=FieldSource.speech,
        )
        for name, value in (state.extracted.items() if state else {}.items())
    ]

    red_flags: List[RedFlag] = []
    if state and state.red_flags:
        red_flags = [RedFlag.model_validate(f) for f in state.red_flags]
    elif db is not None:
        record = (
            db.query(models.ClinicalRecord)
            .filter(models.ClinicalRecord.session_id == row.session_id)
            .one_or_none()
        )
        if record and record.red_flags:
            red_flags = [RedFlag.model_validate(f) for f in record.red_flags]

    documents: List[DocumentRecord] = []
    if db is not None:
        documents = [
            DocumentRecord(
                doc_id=d.doc_id,
                type=d.doc_type,
                captured_at=d.captured_at,
                status=d.status,
                extracted=d.extracted or {},
                title=d.title,
                date=d.doc_date,
                findings=d.findings or [],
            )
            for d in db.query(models.DocumentUpload)
            .filter(models.DocumentUpload.session_id == row.session_id)
            .order_by(models.DocumentUpload.captured_at)
            .all()
        ]
    if not documents:
        # ai.documents.extract isn't wired live yet (not part of this pass) —
        # this is the one piece of _build_summary still canned.
        documents = [DocumentRecord(**d) for d in fixtures.DEMO_DOCUMENTS]

    # Genuinely live — no fallback. chief_complaint, hpi_narrative and
    # sections all come from what the patient actually said this session.
    summary = ai_bridge.generate_summary(extracted_fields, documents)
    summary.red_flags = red_flags
    summary.token = row.token or fixtures.DEMO_TOKEN
    summary.room = row.room or fixtures.DEMO_ROOM
    return summary


def current_red_flags(db: DbSession, session_id: str) -> List[RedFlag]:
    """Red flags as of right now, from the clinical record.

    Always read live rather than from a stored summary. A flag raised after the
    summary was generated must still reach the doctor — the snapshot would show
    none, while the queue row shows one, and the doctor would trust the case
    view over the list.
    """
    record = (
        db.query(models.ClinicalRecord)
        .filter(models.ClinicalRecord.session_id == session_id)
        .one_or_none()
    )
    if record is None or not record.red_flags:
        return []
    return [RedFlag.model_validate(f) for f in record.red_flags]


def _persist(db: DbSession, session_id: str, summary: ClinicalSummary) -> None:
    record = (
        db.query(models.ClinicalRecord)
        .filter(models.ClinicalRecord.session_id == session_id)
        .one_or_none()
    )
    payload = summary.model_dump(mode="json")
    if record is None:
        record = models.ClinicalRecord(session_id=session_id, history={}, summary=payload)
        db.add(record)
    else:
        record.summary = payload


@router.post("/{session_id}/generate", response_model=ClinicalSummary)
def generate_summary(session_id: str, db: DbSession = Depends(get_db)):
    """Build the summary and store it as an unverified draft."""
    row = load_session(db, session_id)

    summary = _build_summary(row, db)
    _persist(db, session_id, summary)
    models.write_audit(db, action="summary.generate", actor="system", session_id=session_id)
    db.commit()

    return summary


@router.get("/{session_id}", response_model=ClinicalSummary)
def get_summary(session_id: str, db: DbSession = Depends(get_db), claims: dict = Depends(require_clinician)):
    """Fetch the stored summary. Generates one on first read if absent."""
    row = load_session(db, session_id)

    record = (
        db.query(models.ClinicalRecord)
        .filter(models.ClinicalRecord.session_id == session_id)
        .one_or_none()
    )

    if record is None or not record.summary:
        summary = _build_summary(row, db)
        _persist(db, session_id, summary)
    else:
        summary = ClinicalSummary.model_validate(record.summary)
        # Overlay live flags: one raised after this summary was generated must
        # still be visible.
        summary.red_flags = current_red_flags(db, session_id) or summary.red_flags

    models.write_audit(db, action="summary.read", actor=claims.get("sub", "physician"), session_id=session_id)
    db.commit()
    return summary

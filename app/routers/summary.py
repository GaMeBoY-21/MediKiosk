# Owner: Tharun
"""Summary generation and retrieval."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app import fixtures, models
from app.database import get_db
from app.routers.session import load_session
from app.schemas import ClinicalSummary, DocumentRecord

log = logging.getLogger(__name__)
router = APIRouter(prefix="/summary", tags=["summary"])


def _build_summary(row: models.Session) -> ClinicalSummary:
    """Assemble the draft summary.

    verified_by stays None: this is a draft until a physician accepts it, and
    the console's 'Unverified draft' banner keys off exactly that.
    """
    # TODO(block 4): ai.summary.generator.generate_summary(clinical_record).
    return ClinicalSummary(
        chief_complaint=fixtures.DEMO_CHIEF_COMPLAINT,
        hpi_narrative=fixtures.DEMO_HPI_NARRATIVE,
        sections=dict(fixtures.DEMO_SECTIONS),
        document_timeline=[DocumentRecord(**d) for d in fixtures.DEMO_DOCUMENTS],
        red_flags=[],
        verified_by=None,
        verified_at=None,
        token=row.token or fixtures.DEMO_TOKEN,
        room=row.room or fixtures.DEMO_ROOM,
    )


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

    summary = _build_summary(row)
    _persist(db, session_id, summary)
    models.write_audit(db, action="summary.generate", actor="system", session_id=session_id)
    db.commit()

    return summary


@router.get("/{session_id}", response_model=ClinicalSummary)
def get_summary(session_id: str, db: DbSession = Depends(get_db)):
    """Fetch the stored summary. Generates one on first read if absent."""
    row = load_session(db, session_id)

    record = (
        db.query(models.ClinicalRecord)
        .filter(models.ClinicalRecord.session_id == session_id)
        .one_or_none()
    )

    if record is None or not record.summary:
        summary = _build_summary(row)
        _persist(db, session_id, summary)
    else:
        summary = ClinicalSummary.model_validate(record.summary)

    models.write_audit(db, action="summary.read", actor="physician", session_id=session_id)
    db.commit()
    return summary

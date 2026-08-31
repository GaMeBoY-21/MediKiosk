# Owner: Tharun
"""Session lifecycle: start, consent, end."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app import ai_bridge, fixtures, models
from app.database import get_db
from app.schemas import (
    ConsentRecord,
    ConsentRequest,
    ConsentResponse,
    InterviewNode,
    SessionEndResponse,
    SessionStartRequest,
    SessionStartResponse,
    SessionStatus,
)
from app.session_store import store

log = logging.getLogger(__name__)
router = APIRouter(prefix="/session", tags=["session"])


def load_session(db: DbSession, session_id: str) -> models.Session:
    """Fetch a session row or 404. Shared by every router."""
    row = db.get(models.Session, session_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown session {session_id}")
    return row


@router.post("/start", response_model=SessionStartResponse)
def start_session(payload: SessionStartRequest | None = None, db: DbSession = Depends(get_db)):
    """Open a session and hand back the opening question.

    The first node ships with the response so the kiosk can render the interview
    without a second round trip.
    """
    body = payload or SessionStartRequest()
    session_id = f"mk-{uuid.uuid4().hex[:12]}"

    # A brand new session has no fields filled and no follow-ups asked yet,
    # so this resolves to the state machine's very first node. Resolved
    # against state.follow_up_counts directly (not a throwaway dict) so the
    # follow-up this counts as is actually recorded, not lost.
    state = store.create(session_id, body.language.value)
    node = ai_bridge.next_node(state.extracted, state.follow_up_counts, body.language.value)

    row = models.Session(
        session_id=session_id,
        language=body.language.value,
        status=SessionStatus.in_progress.value,
        current_node=node["node_id"] if node else None,
        token=fixtures.DEMO_TOKEN,
        room=fixtures.DEMO_ROOM,
    )
    db.add(row)
    models.write_audit(db, action="session.start", actor="kiosk", session_id=session_id)
    db.commit()

    state.current_node = node["node_id"] if node else None
    if node:
        state.rendered_nodes[node["node_id"]] = node
    store.save(state)

    # Opportunistic sweep: no scheduler needed for a kiosk that sees a few
    # hundred sessions a day, and it keeps abandoned transcripts from lingering.
    store.purge_expired()

    return SessionStartResponse(
        session_id=session_id,
        language=body.language,
        status=SessionStatus.in_progress,
        started_at=row.created_at or datetime.now(timezone.utc),
        first_question=InterviewNode(**node) if node else None,
    )


@router.post("/{session_id}/consent", response_model=ConsentResponse)
def record_consent(session_id: str, payload: ConsentRequest, db: DbSession = Depends(get_db)):
    """Store the three consent toggles.

    Recorded per purpose, so refusing document reading does not refuse the
    interview. Replaces any earlier consent row for this session.
    """
    load_session(db, session_id)

    existing = (
        db.query(models.ConsentRecord)
        .filter(models.ConsentRecord.session_id == session_id)
        .one_or_none()
    )
    if existing is not None:
        db.delete(existing)

    row = models.ConsentRecord(
        session_id=session_id,
        record_history=payload.record_history,
        read_documents=payload.read_documents,
        link_abha=payload.link_abha,
        language=payload.language.value,
        method="audio_guided",
    )
    db.add(row)
    models.write_audit(
        db,
        action="consent.record",
        actor="kiosk",
        session_id=session_id,
        detail={
            "record_history": payload.record_history,
            "read_documents": payload.read_documents,
            "link_abha": payload.link_abha,
        },
    )
    db.commit()
    db.refresh(row)

    return ConsentResponse(
        ok=True,
        consent=ConsentRecord(
            record_history=row.record_history,
            read_documents=row.read_documents,
            link_abha=row.link_abha,
            timestamp=row.timestamp,
            language=payload.language,
            method=row.method,
        ),
    )


@router.post("/{session_id}/end", response_model=SessionEndResponse)
def end_session(session_id: str, db: DbSession = Depends(get_db)):
    """Close the session and purge its transcripts.

    Transcripts live only in the in-process store, so purging is a memory
    eviction. Nothing verbatim was ever written to disk.
    """
    row = load_session(db, session_id)
    row.status = SessionStatus.awaiting_physician.value
    row.ended_at = datetime.now(timezone.utc)

    # Evicts the transcripts. They only ever existed in memory.
    purged = store.purge(session_id)

    models.write_audit(
        db,
        action="session.end",
        actor="kiosk",
        session_id=session_id,
        detail={"transcripts_purged": purged},
    )
    db.commit()

    return SessionEndResponse(ok=True, session_id=session_id, transcripts_purged=True)

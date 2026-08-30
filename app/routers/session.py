# Owner: Tharun
"""Session lifecycle endpoints: start session, record consent, end session."""

from fastapi import APIRouter

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/start")
def start_session():
    """Start a new kiosk intake session.

    TODO: create Session record, return session_id.
    """
    raise NotImplementedError


@router.post("/{session_id}/consent")
def record_consent(session_id: str):
    """Record patient consent for a session.

    TODO: create ConsentRecord.
    """
    raise NotImplementedError


@router.post("/{session_id}/end")
def end_session(session_id: str):
    """End a kiosk intake session.

    TODO: mark session ended, finalize state.
    """
    raise NotImplementedError

# Owner: Tharun
"""Physician console endpoints: fetch, edit, confirm, reject."""

from fastapi import APIRouter

router = APIRouter(prefix="/physician", tags=["physician"])


@router.get("/{session_id}")
def fetch_case(session_id: str):
    """Fetch a session's summary and clinical record for physician review.

    TODO: implement lookup.
    """
    raise NotImplementedError


@router.put("/{session_id}")
def edit_case(session_id: str):
    """Edit the clinical record or summary for a session.

    TODO: implement update, write AuditLog entry.
    """
    raise NotImplementedError


@router.post("/{session_id}/confirm")
def confirm_case(session_id: str):
    """Confirm a session's clinical record.

    TODO: implement, write AuditLog entry.
    """
    raise NotImplementedError


@router.post("/{session_id}/reject")
def reject_case(session_id: str):
    """Reject a session's clinical record.

    TODO: implement, write AuditLog entry.
    """
    raise NotImplementedError

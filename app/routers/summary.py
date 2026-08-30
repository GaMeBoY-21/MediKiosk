# Owner: Tharun
"""Summary endpoints: generate summary, fetch summary."""

from fastapi import APIRouter

router = APIRouter(prefix="/summary", tags=["summary"])


@router.post("/{session_id}/generate")
def generate_summary(session_id: str):
    """Generate a clinical summary for a session.

    TODO: call into ai.summary.generator.
    """
    raise NotImplementedError


@router.get("/{session_id}")
def get_summary(session_id: str):
    """Fetch the generated summary for a session.

    TODO: implement lookup.
    """
    raise NotImplementedError

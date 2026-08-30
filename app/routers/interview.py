# Owner: Tharun
"""Interview endpoints: submit answer -> next question."""

from fastapi import APIRouter

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/{session_id}/answer")
def submit_answer(session_id: str):
    """Submit an answer and receive the next interview question.

    TODO: call into ai.interview state machine.
    """
    raise NotImplementedError

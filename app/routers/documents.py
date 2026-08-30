# Owner: Tharun
"""Document upload endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/{session_id}/upload")
def upload_document(session_id: str):
    """Upload a document for a session and extract structured data.

    TODO: save file, call into ai.documents.extract.
    """
    raise NotImplementedError

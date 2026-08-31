# Owner: Tharun
"""Document upload and status.

Upload acknowledges the moment the bytes are on disk. Extraction runs afterwards
in a background task. The patient is standing at a kiosk with a queue behind
them and must never wait on OCR.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.orm import Session as DbSession

from app import ai_bridge, models
from app.database import SessionLocal, get_db
from app.routers.session import load_session
from app.schemas import (
    DocumentFinding,
    DocumentListResponse,
    DocumentRecord,
    DocumentStatus,
    DocumentType,
    DocumentUploadResponse,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = Path("uploads")


def _to_schema(row: models.DocumentUpload) -> DocumentRecord:
    """ORM row -> API model, including the console's timeline fields."""
    return DocumentRecord(
        doc_id=row.doc_id,
        type=DocumentType(row.doc_type),
        captured_at=row.captured_at,
        status=DocumentStatus(row.status),
        extracted=row.extracted or {},
        title=row.title,
        date=row.doc_date,
        findings=[DocumentFinding(**f) for f in (row.findings or [])],
    )


def _extract_in_background(doc_id: str) -> None:
    """Run document extraction after the upload response has already gone out.

    Opens its own database session: the request's session is closed by the time
    this runs.
    """
    db = SessionLocal()
    try:
        row = db.get(models.DocumentUpload, doc_id)
        if row is None:
            return
        row.status = DocumentStatus.processing.value
        db.commit()

        record = None
        if row.storage_path:
            try:
                record = ai_bridge.extract_document(Path(row.storage_path).read_bytes(), doc_id)
            except OSError:
                log.exception("could not read %s", row.storage_path)

        if record is not None:
            # Reassign rather than mutate: SQLAlchemy does not track in-place
            # edits to JSON columns.
            row.extracted = record.extracted or {}
            row.findings = [f.model_dump(mode="json") for f in record.findings]
            row.title = record.title or row.title
            row.doc_date = record.date or row.doc_date
            row.status = record.status.value
            log.info("extracted %d findings from %s", len(record.findings), doc_id)
        else:
            # The provider could not be reached. Stay queued rather than claim
            # a false 'done' — the console must never show findings we did not
            # actually read, and this way the document can be retried.
            row.status = DocumentStatus.queued.value

        models.write_audit(
            db, action="document.extract", actor="system", session_id=row.session_id,
            detail={"doc_id": doc_id, "status": row.status},
        )
        db.commit()
    except Exception:
        log.exception("extraction failed for %s", doc_id)
        db.rollback()
    finally:
        db.close()


@router.post("/{session_id}/upload", response_model=DocumentUploadResponse)
async def upload_document(
    session_id: str,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: DbSession = Depends(get_db),
):
    """Accept one photographed document and acknowledge immediately."""
    load_session(db, session_id)

    doc_id = f"doc-{uuid.uuid4().hex[:12]}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "page.jpg").suffix or ".jpg"
    path = UPLOAD_DIR / f"{doc_id}{suffix}"
    path.write_bytes(await file.read())

    row = models.DocumentUpload(
        doc_id=doc_id,
        session_id=session_id,
        doc_type=DocumentType.other.value,
        status=DocumentStatus.queued.value,
        storage_path=str(path),
        title=file.filename,
    )
    db.add(row)
    models.write_audit(
        db, action="document.upload", actor="kiosk", session_id=session_id,
        detail={"doc_id": doc_id, "filename": file.filename},
    )
    db.commit()

    background.add_task(_extract_in_background, doc_id)

    # document_id duplicates doc_id because client.js reads that name.
    return DocumentUploadResponse(
        doc_id=doc_id, document_id=doc_id, status=DocumentStatus.queued
    )


@router.get("/{session_id}", response_model=DocumentListResponse)
def list_documents(session_id: str, db: DbSession = Depends(get_db)):
    """List this session's documents with current extraction status."""
    load_session(db, session_id)

    rows = (
        db.query(models.DocumentUpload)
        .filter(models.DocumentUpload.session_id == session_id)
        .order_by(models.DocumentUpload.captured_at)
        .all()
    )
    models.write_audit(db, action="document.list", actor="kiosk", session_id=session_id)
    db.commit()

    return DocumentListResponse(session_id=session_id, documents=[_to_schema(r) for r in rows])

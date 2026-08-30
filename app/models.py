# Owner: Tharun
"""ORM tables.

Two privacy properties are load-bearing for what we claim about this system, so
they are enforced here rather than left to convention:

1. RAW AUDIO IS NEVER STORED. There is no audio column on any table, and no
   code path that writes one. The microphone stream is transcribed in the
   browser and the audio is discarded there.

2. RAW TRANSCRIPTS ARE NEVER PERSISTED. Transcripts live only in the in-process
   session store (app/session_store.py) for the length of the interview and are
   purged when the session ends. What reaches this database is the structured
   record extracted from them, never the patient's verbatim words.

3. audit_log IS APPEND-ONLY. Enforced three ways: no update/delete helper
   exists, an ORM before_flush guard raises on any attempt, and a database
   trigger rejects UPDATE and DELETE on both Postgres and SQLite.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    DDL,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, SessionLocal

# JSONB on Postgres, plain JSON on the SQLite fallback.
JSONType = JSON().with_variant(JSONB, "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Session(Base):
    """One kiosk encounter.

    Identity columns hold only what we are allowed to keep: an ABHA number if
    the patient linked one, and at most the last four Aadhaar digits. There is
    deliberately no column for a full Aadhaar number.
    """

    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="in_progress", nullable=False)
    current_node: Mapped[str | None] = mapped_column(String(64), nullable=True)

    token: Mapped[str | None] = mapped_column(String(16), nullable=True)
    room: Mapped[str | None] = mapped_column(String(16), nullable=True)

    abha_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    aadhaar_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    patient_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    consent = relationship("ConsentRecord", back_populates="session", uselist=False)
    clinical = relationship("ClinicalRecord", back_populates="session", uselist=False)
    documents = relationship("DocumentUpload", back_populates="session")


class ConsentRecord(Base):
    """The three consent toggles, stored per purpose rather than as one flag."""

    __tablename__ = "consent_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False
    )

    record_history: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_documents: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    link_abha: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    method: Mapped[str] = mapped_column(String(32), default="audio_guided", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session = relationship("Session", back_populates="consent")


class ClinicalRecord(Base):
    """The structured history and generated summary.

    `history` and `summary` hold extracted, structured data only. No verbatim
    transcript is written here — see the module docstring.
    """

    __tablename__ = "clinical_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("sessions.session_id", ondelete="CASCADE"), unique=True
    )

    history: Mapped[dict] = mapped_column(JSONType, default=dict)
    summary: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    red_flags: Mapped[list] = mapped_column(JSONType, default=list)

    verified_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    session = relationship("Session", back_populates="clinical")


class DocumentUpload(Base):
    """A photographed prescription or report.

    The image is written to disk and referenced by path; bytes are not stored
    in the database.
    """

    __tablename__ = "documents"

    doc_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False
    )

    doc_type: Mapped[str] = mapped_column(String(32), default="other", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="queued", nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    doc_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    extracted: Mapped[dict] = mapped_column(JSONType, default=dict)
    findings: Mapped[list] = mapped_column(JSONType, default=list)

    session = relationship("Session", back_populates="documents")


class AuditLog(Base):
    """Append-only trail of every read and write of clinical data.

    There is no update or delete path to this table anywhere in the codebase,
    and the database rejects both. Rows are the evidence that a given actor
    touched a given patient's record at a given time.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[dict] = mapped_column(JSONType, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )


# ------------------------------------------------- append-only enforcement


_PG_GUARD = DDL(
    """
    CREATE OR REPLACE FUNCTION medikiosk_audit_immutable() RETURNS trigger AS $$
    BEGIN
        RAISE EXCEPTION 'audit_log is append-only';
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER audit_log_immutable
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION medikiosk_audit_immutable();
    """
)

_SQLITE_GUARD_UPDATE = DDL(
    "CREATE TRIGGER IF NOT EXISTS audit_log_no_update BEFORE UPDATE ON audit_log "
    "BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;"
)

_SQLITE_GUARD_DELETE = DDL(
    "CREATE TRIGGER IF NOT EXISTS audit_log_no_delete BEFORE DELETE ON audit_log "
    "BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;"
)

event.listen(AuditLog.__table__, "after_create", _PG_GUARD.execute_if(dialect="postgresql"))
event.listen(AuditLog.__table__, "after_create", _SQLITE_GUARD_UPDATE.execute_if(dialect="sqlite"))
event.listen(AuditLog.__table__, "after_create", _SQLITE_GUARD_DELETE.execute_if(dialect="sqlite"))


class AuditLogImmutable(RuntimeError):
    """Raised when code tries to modify or delete an audit row."""


@event.listens_for(SessionLocal, "before_flush")
def _block_audit_mutation(session, _flush_context, _instances):
    """Fail loudly in Python before the database has to.

    The DB trigger is the real guarantee; this exists so the error names the
    offending code path instead of surfacing as a driver exception.
    """
    for obj in session.dirty:
        if isinstance(obj, AuditLog) and session.is_modified(obj):
            raise AuditLogImmutable("audit_log rows cannot be updated")
    for obj in session.deleted:
        if isinstance(obj, AuditLog):
            raise AuditLogImmutable("audit_log rows cannot be deleted")


def write_audit(
    db,
    *,
    action: str,
    actor: str = "system",
    session_id: str | None = None,
    detail: dict | None = None,
) -> AuditLog:
    """Append one audit row. The only supported way to touch audit_log.

    Call this on every read or write of clinical data. It does not commit —
    the caller's transaction owns the boundary, so the audit row and the change
    it describes land together or not at all.
    """
    row = AuditLog(
        session_id=session_id,
        actor=actor,
        action=action,
        detail=detail or {},
    )
    db.add(row)
    return row

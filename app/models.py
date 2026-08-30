# Owner: Tharun
"""SQLAlchemy ORM table definitions.

TODO: define real columns/relationships for each table below.
"""


class Session:
    """Represents a single kiosk intake session."""

    # TODO: id, patient identifiers, started_at, ended_at, status
    pass


class ConsentRecord:
    """Records patient consent captured at the start of a session."""

    # TODO: session_id, consent_text, accepted_at
    pass


class ClinicalRecord:
    """Structured clinical data extracted during the interview."""

    # TODO: session_id, fields captured, source
    pass


class DocumentUpload:
    """Metadata for a document uploaded during a session."""

    # TODO: session_id, file_path, extracted_data
    pass


class AuditLog:
    """Audit trail entry for physician review actions."""

    # TODO: session_id, actor, action, timestamp
    pass

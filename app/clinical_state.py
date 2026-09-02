# Owner: Tharun
"""Reading and writing a session's clinical state.

Lives outside the routers because two of them need it: the interview loop
writes fields extracted from speech, and the session router writes fields the
kiosk collected on its own screens. Putting these in app/routers/interview.py
and importing them from app/routers/session.py would be a cycle, since the
interview router already imports load_session from the session router.
"""

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session as DbSession

from app import models
from app.schemas import ExtractedField, FieldSource, RedFlag


def understanding(state) -> List[ExtractedField]:
    """Every field understood so far, for the kiosk's understanding panel.

    Cumulative, because the panel accumulates across the interview rather than
    resetting each turn. Rebuilt from session state on every response so a
    field corrected later shows its corrected value.

    Structured fields only. `state.transcripts` holds the patient's verbatim
    words and must never leave the server in this payload — the whole point of
    keeping them in memory is that they are not distributed.
    """
    from ai.interview.display import humanise, inherited_label

    return [
        ExtractedField(
            name=name,
            value=value,
            # Best to worst: the label of the option the patient tapped, kept
            # when the answer was filed; the label of another field holding
            # the same answer, for the ones reconcile.py derives; and last the
            # value opened out, so the panel is never handed a raw token.
            display=(
                state.field_display.get(name)
                or inherited_label(name, value, state.extracted, state.field_display)
                or humanise(value)
            ),
            # A real float. The panel hedges anything below 0.7, which it
            # cannot do from a boolean. Defaults to 1.0 only for values that
            # predate confidence tracking.
            confidence=float(state.field_confidence.get(name, 1.0)),
            source=FieldSource(state.field_source.get(name, FieldSource.speech.value)),
        )
        for name, value in state.extracted.items()
    ]


def _record_for(db: DbSession, session_id: str) -> models.ClinicalRecord:
    record = (
        db.query(models.ClinicalRecord)
        .filter(models.ClinicalRecord.session_id == session_id)
        .one_or_none()
    )
    if record is None:
        record = models.ClinicalRecord(session_id=session_id, history={}, red_flags=[])
        db.add(record)
        db.flush()
    return record


def persist_extracted_fields(db: DbSession, session_id: str, extracted: dict) -> None:
    """Merge newly extracted fields into the clinical record's structured
    history. This is the only place a patient's answer reaches the database —
    session state is in-memory only."""
    record = _record_for(db, session_id)
    # Reassign rather than mutate: SQLAlchemy does not track in-place JSON edits.
    history = dict(record.history or {})
    history.update(extracted)
    record.history = history


def persist_red_flag(db: DbSession, session_id: str, red_flag: RedFlag) -> None:
    """Store the flag on the clinical record so the queue can sort by it."""
    record = _record_for(db, session_id)
    existing = list(record.red_flags or [])
    if not any(f.get("rule_id") == red_flag.rule_id for f in existing):
        existing.append(red_flag.model_dump(mode="json"))
    record.red_flags = existing

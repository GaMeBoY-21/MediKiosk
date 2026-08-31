# Owner: Tharun
"""Interview: submit an answer, get the next question.

Red flags are evaluated inline on the answer request and returned on the same
response. They never wait for the summary — a patient reporting breathlessness
must see the emergency screen on their next tap, not at the end of the interview.

Transcripts go to the in-process session store only. Nothing verbatim is written
to the database; what persists is the structured extraction.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app import ai_bridge, fixtures, models
from app.database import get_db
from app.routers.session import load_session
from app.schemas import (
    AnswerRequest,
    AnswerResponse,
    ExtractedField,
    FieldSource,
    Language,
    NodeType,
    Progress,
    QuestionOption,
    TerminalReason,
)
from app.session_store import store

log = logging.getLogger(__name__)
router = APIRouter(prefix="/interview", tags=["interview"])


def _understanding(state) -> list[ExtractedField]:
    """Every field understood so far, for the kiosk's understanding panel.

    Cumulative, because the panel accumulates across the interview rather than
    resetting each turn. Rebuilt from session state on every response so a
    field corrected later shows its corrected value.

    Structured fields only. `state.transcripts` holds the patient's verbatim
    words and must never leave the server in this payload — the whole point of
    keeping them in memory is that they are not distributed.
    """
    return [
        ExtractedField(
            name=name,
            value=value,
            # A real float. The panel hedges anything below 0.7, which it
            # cannot do from a boolean. Defaults to 1.0 only for values that
            # predate confidence tracking.
            confidence=float(state.field_confidence.get(name, 1.0)),
            source=FieldSource(state.field_source.get(name, FieldSource.speech.value)),
        )
        for name, value in state.extracted.items()
    ]


def _to_response(node: dict | None, answered: int, red_flag=None, state=None) -> AnswerResponse:
    """Build the one response shape that covers question / done / red-flag.

    `options` is always populated, [] when the node takes free text only. The
    frontend's rendering breaks if the key is ever missing.
    """
    progress = Progress(answered=answered, total=ai_bridge.estimated_total_nodes())
    extracted = _understanding(state) if state is not None else []

    if red_flag is not None:
        # done=True, not False: the interview really has stopped, and the kiosk
        # had no state for "no question, but not finished either". The frontend
        # branches on red_flag first regardless, so the emergency screen wins.
        return AnswerResponse(
            red_flag=red_flag,
            options=[],
            progress=progress,
            done=True,
            terminal_reason=TerminalReason.red_flag,
            extracted=extracted,
        )

    if node is None:
        return AnswerResponse(
            done=True,
            options=[],
            progress=progress,
            terminal_reason=TerminalReason.completed,
            extracted=extracted,
        )

    return AnswerResponse(
        node_id=node["node_id"],
        question=node["question"],
        options=[QuestionOption(**o) for o in node.get("options", [])],
        allow_free_text=node.get("allow_free_text", True),
        node_type=NodeType(node.get("node_type", NodeType.free_text.value)),
        progress=progress,
        done=False,
        phase=node.get("phase") or None,
        extracted=extracted,
    )


@router.post("/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(session_id: str, payload: AnswerRequest, db: DbSession = Depends(get_db)):
    """Record an answer and return the next question.

    Order matters. Extraction and the safety check run before the state machine
    is consulted, so a red flag short-circuits the interview rather than being
    queued behind another question.
    """
    row = load_session(db, session_id)

    state = store.record_answer(
        session_id, payload.node_id, payload.transcript, payload.selected_option
    )
    state.language = payload.language.value

    # Which field the question we asked was trying to fill. Recorded when the
    # question was generated; a tapped option is filed straight into it
    # without a model call.
    target_field = (state.rendered_nodes.get(payload.node_id) or {}).get("target_field")

    # Extraction and the next question come back from ONE model call. They
    # used to be two serial calls, so every tap paid both latencies and spent
    # two requests from a small daily quota.
    extracted_fields, node = ai_bridge.answer_turn(
        payload.node_id,
        payload.transcript or "",
        payload.selected_option,
        payload.selected_options,
        target_field,
        state.extracted,
        state.follow_up_counts,
        payload.language.value,
    )
    extracted = {f.name: f.value for f in extracted_fields}
    if extracted:
        state.extracted.update(extracted)
        for f in extracted_fields:
            state.field_confidence[f.name] = f.confidence
            state.field_source[f.name] = f.source.value
        _persist_extracted_fields(db, session_id, extracted)
    store.save(state)

    # Deterministic, synchronous, no model call, no waiting on the summary.
    # Evaluated on the extracted fields (already English), not the raw
    # transcript, so this fires identically in all seven languages.
    red_flag = ai_bridge.check_red_flags(state.extracted)

    if red_flag is not None:
        state.red_flags.append(red_flag.model_dump(mode="json"))
        store.save(state)
        _persist_red_flag(db, session_id, red_flag)
        models.write_audit(
            db,
            action="interview.red_flag",
            actor="kiosk",
            session_id=session_id,
            detail={"rule_id": red_flag.rule_id, "node_id": payload.node_id},
        )
        db.commit()
        log.warning("red flag %s on session %s", red_flag.rule_id, session_id)
        return _to_response(None, state.answered_count(), red_flag=red_flag, state=state)

    state.current_node = node["node_id"] if node else None
    if node:
        state.rendered_nodes[node["node_id"]] = node
    store.save(state)

    row.current_node = state.current_node
    models.write_audit(
        db,
        action="interview.answer",
        actor="kiosk",
        session_id=session_id,
        detail={
            "node_id": payload.node_id,
            "answered_with": "option" if payload.selected_option else "speech",
            "fields_extracted": sorted(extracted) if extracted else [],
        },
    )
    db.commit()

    return _to_response(node, state.answered_count(), state=state)


def _persist_extracted_fields(db: DbSession, session_id: str, extracted: dict) -> None:
    """Merge newly extracted fields into the clinical record's structured
    history. This is the only place a spoken answer's structured value
    actually reaches the database — state.extracted is in-memory only."""
    record = (
        db.query(models.ClinicalRecord)
        .filter(models.ClinicalRecord.session_id == session_id)
        .one_or_none()
    )
    if record is None:
        record = models.ClinicalRecord(session_id=session_id, history={}, red_flags=[])
        db.add(record)
        db.flush()
    # Reassign rather than mutate: SQLAlchemy does not track in-place JSON edits.
    history = dict(record.history or {})
    history.update(extracted)
    record.history = history


def _persist_red_flag(db: DbSession, session_id: str, red_flag) -> None:
    """Store the flag on the clinical record so the queue can sort by it."""
    record = (
        db.query(models.ClinicalRecord)
        .filter(models.ClinicalRecord.session_id == session_id)
        .one_or_none()
    )
    if record is None:
        record = models.ClinicalRecord(session_id=session_id, history={}, red_flags=[])
        db.add(record)
        db.flush()
    existing = list(record.red_flags or [])
    if not any(f.get("rule_id") == red_flag.rule_id for f in existing):
        existing.append(red_flag.model_dump(mode="json"))
    # Reassign rather than mutate: SQLAlchemy does not track in-place JSON edits.
    record.red_flags = existing


@router.get("/{session_id}/node/{node_id}", response_model=AnswerResponse)
def get_node(
    session_id: str,
    node_id: str,
    lang: Language = Language.en,
    db: DbSession = Depends(get_db),
):
    """Re-render one past question, with its option tiles intact.

    This is what the Confirm screen's edit pencil needs: jumping back to an
    earlier answer has to restore the tiles, not drop the patient into a
    voice-only prompt. ai.interview.followup generates a question fresh each
    time it's asked, so replaying one verbatim means replaying the exact
    dict that was rendered for it originally, from state.rendered_nodes —
    not asking ai/ to generate it again, which could word it differently.
    fixtures.render_node is only a fallback for a node rendered before this
    session's state existed (e.g. a process restart).
    """
    load_session(db, session_id)

    state = store.get(session_id)
    node = (state.rendered_nodes.get(node_id) if state else None) or fixtures.render_node(
        node_id, lang.value
    )
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown node {node_id}")

    answered = state.answered_count() if state else 0
    return _to_response(node, answered, state=state)

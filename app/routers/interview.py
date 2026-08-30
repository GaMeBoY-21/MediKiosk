# Owner: Tharun
"""Interview: submit an answer, get the next question.

Red flags are evaluated inline on the answer request and returned on the same
response. They never wait for the summary — a patient reporting breathlessness
must see the emergency screen on their next tap, not at the end of the interview.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app import fixtures, models
from app.database import get_db
from app.routers.session import load_session
from app.schemas import (
    AnswerRequest,
    AnswerResponse,
    Language,
    NodeType,
    Progress,
    QuestionOption,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/interview", tags=["interview"])


def _to_response(node: dict | None, answered: int, red_flag=None) -> AnswerResponse:
    """Build the one response shape that covers question / done / red-flag.

    `options` is always populated, [] when the node takes free text only. The
    frontend's rendering breaks if the key is ever missing.
    """
    if red_flag is not None:
        return AnswerResponse(
            red_flag=red_flag,
            options=[],
            progress=Progress(answered=answered, total=len(fixtures.NODE_ORDER)),
        )

    if node is None:
        return AnswerResponse(
            done=True,
            options=[],
            progress=Progress(answered=answered, total=len(fixtures.NODE_ORDER)),
        )

    return AnswerResponse(
        node_id=node["node_id"],
        question=node["question"],
        options=[QuestionOption(**o) for o in node["options"]],
        allow_free_text=node["allow_free_text"],
        node_type=NodeType(node["node_type"]),
        progress=Progress(answered=answered, total=len(fixtures.NODE_ORDER)),
        done=False,
    )


@router.post("/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(session_id: str, payload: AnswerRequest, db: DbSession = Depends(get_db)):
    """Record an answer and return the next question.

    Order matters: the safety check runs before the state machine is consulted,
    so a red flag short-circuits the interview rather than being queued behind
    another question.
    """
    row = load_session(db, session_id)

    # Deterministic, synchronous, no model call.
    red_flag = fixtures.evaluate_red_flags(
        payload.node_id, payload.selected_option, payload.transcript
    )

    answered = fixtures.NODE_ORDER.index(payload.node_id) + 1 if payload.node_id in fixtures.NODE_ORDER else 0

    if red_flag is not None:
        models.write_audit(
            db,
            action="interview.red_flag",
            actor="kiosk",
            session_id=session_id,
            detail={"rule_id": red_flag.rule_id, "node_id": payload.node_id},
        )
        db.commit()
        log.warning("red flag %s on session %s", red_flag.rule_id, session_id)
        return _to_response(None, answered, red_flag=red_flag)

    # TODO(block 4): ai.interview.state_machine.transition() decides this.
    next_id = fixtures.next_node_id(payload.node_id)
    row.current_node = next_id
    models.write_audit(
        db,
        action="interview.answer",
        actor="kiosk",
        session_id=session_id,
        detail={"node_id": payload.node_id, "answered_with": "option" if payload.selected_option else "speech"},
    )
    db.commit()

    node = fixtures.render_node(next_id, payload.language.value) if next_id else None
    return _to_response(node, answered)


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
    voice-only prompt.
    """
    load_session(db, session_id)

    node = fixtures.render_node(node_id, lang.value)
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown node {node_id}")

    answered = fixtures.NODE_ORDER.index(node_id) if node_id in fixtures.NODE_ORDER else 0
    return _to_response(node, answered)

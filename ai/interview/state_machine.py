# Owner: Nikki
"""Interview state machine: transitions and current-node resolution.

Deterministic: a node ends when its required fields are filled or its
follow-up cap is hit — never on a fixed question count. The LLM has no vote
here; it only fills `fields` (via ai.interview.extraction) and phrases
questions (via ai.interview.followup). This module decides what happens
next.

`session_state` is a plain dict shaped like:
    {
        "fields": {<field_name>: <value>, ...},
        "follow_up_counts": {<node_id>: <int>, ...},
        "field_ask_counts": {<field_name>: <int>, ...},
    }

`field_ask_counts` is the per-field cap. `follow_up_counts` caps a whole
stage; that was too coarse to stop the kiosk asking the SAME question twice
inside a stage with eight follow-ups to spend.
"""

import logging

from ai.interview.nodes import NODE_ORDER, InterviewNode, get_node
from ai.interview.reconcile import derive_fields

log = logging.getLogger(__name__)

# How many times one field may be put to the patient before the interview
# gives up on it and moves on with it unfilled.
#
# Two. Once, and a mis-heard answer is never recovered; three, and a patient
# who has already answered as well as they can is being interrogated. A missing
# field is recoverable — the physician asks in the consultation, and the
# summary shows the gap. A kiosk stuck on one question is not: the patient
# walks away and the whole intake is lost.
MAX_FIELD_ASKS = 2


def field_ask_counts(session_state: dict) -> dict:
    return session_state.setdefault("field_ask_counts", {})


def is_field_capped(session_state: dict, field_name: str) -> bool:
    """True once this field has been asked MAX_FIELD_ASKS times and is still
    empty. The interview stops asking and carries on without it."""
    return field_ask_counts(session_state).get(field_name, 0) >= MAX_FIELD_ASKS


def _is_field_settled(field_name: str, session_state: dict) -> bool:
    """Filled, or asked about enough times that we stop asking."""
    return field_name in session_state.get("fields", {}) or is_field_capped(
        session_state, field_name
    )


def unfilled_fields(node: InterviewNode, session_state: dict) -> list:
    """This node's fields that are still worth asking about.

    Excludes both filled fields and capped ones, so a field we have given up
    on is never offered to the model as something to ask again.
    """
    all_fields = list(node.required_fields) + list(node.optional_fields)
    return [f for f in all_fields if not _is_field_settled(f, session_state)]


def _is_node_satisfied(node_id: str, session_state: dict) -> bool:
    node = get_node(node_id)
    follow_up_counts = session_state.get("follow_up_counts", {})
    if follow_up_counts.get(node_id, 0) >= node.max_follow_ups:
        return True
    return all(
        _is_field_settled(field_name, session_state) for field_name in node.required_fields
    )


def next_node(session_state: dict) -> InterviewNode | None:
    """The node the patient should be asked about next, or None if the
    interview is complete. Walks NODE_ORDER and returns the first node whose
    required fields aren't yet filled and whose follow-up cap isn't hit."""
    for node_id in NODE_ORDER:
        if not _is_node_satisfied(node_id, session_state):
            return get_node(node_id)
    return None


def is_complete(session_state: dict) -> bool:
    """True once every node in NODE_ORDER is satisfied. Tharun's API signals
    the end of the interview with next: null when this is true."""
    return next_node(session_state) is None


def record_follow_up(session_state: dict, node_id: str) -> dict:
    """Increment the follow-up counter for a node after a question is asked
    in it. Call this once per question, not per field."""
    session_state.setdefault("follow_up_counts", {})
    counts = session_state["follow_up_counts"]
    counts[node_id] = counts.get(node_id, 0) + 1
    return session_state


def record_field_ask(session_state: dict, field_name: str) -> dict:
    """Count one question put to the patient about `field_name`.

    Called when a question is rendered, not when it is answered — an
    unanswered ask is exactly what the cap exists to count. Logged on the way
    past the cap so a field the kiosk gave up on is visible in the logs
    rather than silently absent from the record.
    """
    if not field_name:
        return session_state
    counts = field_ask_counts(session_state)
    counts[field_name] = counts.get(field_name, 0) + 1
    if counts[field_name] >= MAX_FIELD_ASKS and field_name not in session_state.get("fields", {}):
        log.warning(
            "asked %r %d times without an answer; moving on with it unfilled",
            field_name,
            counts[field_name],
        )
    return session_state


def clear_field_asks(session_state: dict, field_names) -> dict:
    """Reset the ask counter for fields that have just been answered.

    The cap is on CONSECUTIVE unanswered asks. A field answered, then corrected
    and asked about again later, starts from zero — it is not the stuck loop
    this guards against.
    """
    counts = field_ask_counts(session_state)
    for name in field_names:
        counts.pop(name, None)
    return session_state


def apply_extracted_fields(session_state: dict, extracted_fields: dict) -> dict:
    """Merge newly extracted fields into session state, then reconcile.

    extracted_fields should already have low-confidence/omitted fields
    filtered out by ai.interview.extraction — this just merges what's given.

    Reconciliation runs here, after the merge and before any caller asks the
    state machine what is still unfilled. That ordering is the whole point:
    "back pain" has to have filled symptom_site by the time next_node() looks,
    or the patient gets asked where the pain is.
    """
    session_state.setdefault("fields", {})
    session_state["fields"].update(extracted_fields)
    session_state["fields"].update(derive_fields(session_state["fields"]))
    clear_field_asks(session_state, session_state["fields"].keys())
    return session_state

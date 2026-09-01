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
    }
"""

from ai.interview.nodes import NODE_ORDER, InterviewNode, get_node


# How many times one field may be asked about before the interview gives up on
# it and moves on. Two, not more: a field that has not filled after a second
# attempt is usually one the model has already recorded under another name, and
# no amount of rephrasing will fill it. A missing field is recoverable — the
# physician asks in the consultation. A kiosk stuck asking "where is the pain?"
# eight times is not: the patient concludes it is broken and walks away.
MAX_FIELD_ASKS = 2


def is_abandoned(field_name: str, session_state: dict) -> bool:
    """True once a field has been asked about MAX_FIELD_ASKS times unfilled."""
    if field_name in session_state.get("fields", {}):
        return False
    return session_state.get("field_ask_counts", {}).get(field_name, 0) >= MAX_FIELD_ASKS


def record_field_ask(session_state: dict, field_name: str) -> dict:
    """Note that a question was asked targeting `field_name`.

    Called once per generated question. Without this the node-level
    max_follow_ups cap is the only limit, which allows the same field to be
    re-asked up to eight times inside one node.
    """
    if not field_name:
        return session_state
    session_state.setdefault("field_ask_counts", {})
    counts = session_state["field_ask_counts"]
    counts[field_name] = counts.get(field_name, 0) + 1
    return session_state


def _is_node_satisfied(node_id: str, session_state: dict) -> bool:
    node = get_node(node_id)
    fields = session_state.get("fields", {})
    follow_up_counts = session_state.get("follow_up_counts", {})
    if follow_up_counts.get(node_id, 0) >= node.max_follow_ups:
        return True
    # A field counts as settled when it is filled OR when we have given up on
    # it, so one unfillable field can no longer hold the whole node open.
    return all(
        field_name in fields or is_abandoned(field_name, session_state)
        for field_name in node.required_fields
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


def apply_extracted_fields(session_state: dict, extracted_fields: dict) -> dict:
    """Merge newly extracted fields into session state.

    extracted_fields should already have low-confidence/omitted fields
    filtered out by ai.interview.extraction — this just merges what's given.
    """
    session_state.setdefault("fields", {})
    session_state["fields"].update(extracted_fields)
    return session_state

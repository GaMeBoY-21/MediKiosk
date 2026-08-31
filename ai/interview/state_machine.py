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


def _is_node_satisfied(node_id: str, session_state: dict) -> bool:
    node = get_node(node_id)
    fields = session_state.get("fields", {})
    follow_up_counts = session_state.get("follow_up_counts", {})
    if follow_up_counts.get(node_id, 0) >= node.max_follow_ups:
        return True
    return all(field_name in fields for field_name in node.required_fields)


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

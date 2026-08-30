# Owner: Nikki
"""Interview state machine: transitions and current-node resolution."""


def get_current_node(session_state: dict) -> dict:
    """Resolve the current node for a session's interview state.

    TODO: implement.
    """
    raise NotImplementedError


def transition(session_state: dict, answer: str) -> dict:
    """Apply an answer and transition to the next node.

    TODO: implement.
    """
    raise NotImplementedError

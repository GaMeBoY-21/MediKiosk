# Owner: Tharun
"""In-process session state store.

TODO: replace with Redis-backed store for multi-worker deployments.
"""


def get_session(session_id: str):
    """Fetch in-memory state for a session.

    TODO: implement lookup.
    """
    raise NotImplementedError


def set_session(session_id: str, state: dict):
    """Store in-memory state for a session.

    TODO: implement storage.
    """
    raise NotImplementedError


def clear_session(session_id: str):
    """Remove in-memory state for a session.

    TODO: implement removal.
    """
    raise NotImplementedError

# Owner: Tharun
"""In-process session state with a TTL.

This is where raw transcripts live, and the only place they ever live. They are
held in memory for the length of the interview and evicted on end or expiry, so
a patient's verbatim words never reach disk. app/models.py stores the structured
record extracted from them, never the words themselves.

Structured for a Redis swap: every read goes through get(), every write through
save(), and nothing outside this module touches _STATES. Replacing the dict with
a Redis hash means reimplementing this class, not editing the routers.
Deliberately NOT adding Redis now.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.config import settings

log = logging.getLogger(__name__)


@dataclass
class SessionState:
    """Everything the interview needs between requests.

    `transcripts` is the sensitive field. It is never serialised to the
    database and is dropped by purge().
    """

    session_id: str
    language: str = "en"
    current_node: Optional[str] = None
    answers: List[Dict[str, Any]] = field(default_factory=list)
    transcripts: Dict[str, str] = field(default_factory=dict)
    extracted: Dict[str, Any] = field(default_factory=dict)
    red_flags: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

    def answered_count(self) -> int:
        return len(self.answers)


class SessionStore:
    """Thread-safe in-process store. One instance per process.

    FastAPI runs sync endpoints on a threadpool, so every mutation takes the
    lock. A Redis implementation would drop the lock and keep the interface.
    """

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._lock = threading.RLock()
        self._states: Dict[str, SessionState] = {}

    def create(self, session_id: str, language: str = "en") -> SessionState:
        with self._lock:
            state = SessionState(session_id=session_id, language=language)
            self._states[session_id] = state
            return state

    def get(self, session_id: str) -> Optional[SessionState]:
        """Fetch live state, expiring it first if it has gone stale."""
        with self._lock:
            state = self._states.get(session_id)
            if state is None:
                return None
            if time.time() - state.last_seen > self._ttl:
                self._evict(session_id)
                log.info("session %s expired after %ss idle", session_id, self._ttl)
                return None
            state.last_seen = time.time()
            return state

    def get_or_create(self, session_id: str, language: str = "en") -> SessionState:
        """Survive a process restart mid-interview without 500-ing the kiosk."""
        return self.get(session_id) or self.create(session_id, language)

    def save(self, state: SessionState) -> None:
        with self._lock:
            state.last_seen = time.time()
            self._states[state.session_id] = state

    def record_answer(
        self,
        session_id: str,
        node_id: str,
        transcript: Optional[str],
        selected_option: Optional[str],
    ) -> SessionState:
        """Append an answer, keeping the transcript in memory only."""
        state = self.get_or_create(session_id)
        with self._lock:
            state.answers.append(
                {"node_id": node_id, "selected_option": selected_option, "has_speech": bool(transcript)}
            )
            if transcript:
                state.transcripts[node_id] = transcript
            state.last_seen = time.time()
        return state

    def purge(self, session_id: str) -> bool:
        """Drop all state for a session, transcripts included. Called on end."""
        with self._lock:
            existed = session_id in self._states
            self._evict(session_id)
            if existed:
                log.info("purged session %s", session_id)
            return existed

    def purge_expired(self) -> int:
        """Evict every session idle for longer than the TTL."""
        cutoff = time.time() - self._ttl
        with self._lock:
            stale = [sid for sid, st in self._states.items() if st.last_seen < cutoff]
            for sid in stale:
                self._evict(sid)
        if stale:
            log.info("purged %d expired sessions", len(stale))
        return len(stale)

    def _evict(self, session_id: str) -> None:
        """Overwrite transcripts before dropping the reference.

        Belt and braces: clearing the dict means the strings stop being
        reachable immediately rather than waiting on garbage collection.
        """
        state = self._states.pop(session_id, None)
        if state is not None:
            state.transcripts.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._states)


store = SessionStore(ttl_seconds=settings.SESSION_TTL_SECONDS)

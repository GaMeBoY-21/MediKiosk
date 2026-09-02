# Owner: Nikki
"""A pool of (API key, model) combinations, tried in order, failing over on quota.

Gemini's free tier is metered per Google Cloud PROJECT and per MODEL. Five keys
from five different accounts are therefore five independent allowances, and a
second model doubles each of them: five keys times two models is ten separate
daily pools rather than one. Both axes are used here.

The ordering is keys-first within a model:

    key1/primary, key2/primary, ... key5/primary,
    key1/fallback, key2/fallback, ... key5/fallback

Keys are the more plentiful axis and cost nothing in quality; the fallback
model is a different model and may answer differently, so it is the last
resort rather than the second one.

Three rules that matter more than they look:

  Exhausted is forever (for this process). A daily quota does not come back
  during a demo, so returning to a spent combination only spends the patient's
  time. The set is deliberately not time-based.

  Failover is immediate, with no retry of the spent combination. The previous
  code retried a quota error twice with the server's own backoff, which cost
  about 45 seconds per call to arrive at the same failure. Moving to the next
  key takes one call.

  A non-quota failure never burns a key. A network blip or a malformed
  response says nothing about the allowance, and treating it as exhaustion
  would throw away four working keys on a bad wifi moment.

Keys are never logged, not even truncated: a partial key is still a secret and
this output goes to a terminal that will be on a projector. Combinations are
identified by index only — "key 3 of 5".
"""

import logging
import re
import threading

from ai.adapters.base import AllProvidersExhausted

log = logging.getLogger(__name__)

# The env vars a key may arrive in, in order. GEMINI_API_KEY is the original
# single-key setting and stays working as key 1 so nothing breaks before the
# numbered ones are filled in.
NUMBERED_KEY_VARS = tuple(f"GEMINI_API_KEY_{n}" for n in range(1, 6))
LEGACY_KEY_VAR = "GEMINI_API_KEY"


def is_quota_error(exc: Exception) -> bool:
    """Whether this failure means "allowance spent" rather than "call failed".

    Matched on the message because the SDK raises its own exception types and
    the useful signal (RESOURCE_EXHAUSTED, the 429, the quota id) is in the
    text. Kept deliberately narrow: anything not clearly a quota problem is
    treated as a transient failure, because the cost of guessing wrong is
    retiring a key that still had allowance left.
    """
    message = str(exc).lower()
    return (
        "resource_exhausted" in message
        or "resource exhausted" in message
        # Word-bounded: a bare "429" also appears inside session ids and
        # timestamps, and a false positive here retires a key that was fine.
        or re.search(r"\b429\b", message) is not None
        or "quota" in message
        or "rate limit" in message
    )


def is_auth_error(exc: Exception) -> bool:
    """Whether this failure means "this key will never work".

    A typo'd, revoked or wrong-project key fails with 400 API_KEY_INVALID or a
    401/403, and it will fail that way every time. Treating it as a transient
    error meant one bad key in slot 1 failed every request while four good keys
    sat unused — indistinguishable, from the front of the room, from a total
    outage. It is a different fault from a spent quota and is logged
    differently, but the response is the same: retire it and move on.
    """
    message = str(exc).lower()
    return (
        "api_key_invalid" in message
        or "api key not valid" in message
        or "unauthenticated" in message
        or "permission_denied" in message
        # Word-bounded for the same reason as the 429 above.
        or re.search(r"\b(401|403)\b", message) is not None
    )


def collect_keys(env: dict) -> list[str]:
    """The configured keys, in order, with blanks and duplicates dropped.

    Absent or empty entries are skipped silently: filling in three of the five
    slots is a normal state, not a misconfiguration to complain about.

    Duplicates are dropped because two slots holding the same key are one
    allowance wearing two hats, and counting it twice would make the pool look
    healthier than it is at exactly the moment that matters.
    """
    found: list[str] = []
    for var in NUMBERED_KEY_VARS:
        value = (env.get(var) or "").strip()
        if value and value not in found:
            found.append(value)
    if not found:
        legacy = (env.get(LEGACY_KEY_VAR) or "").strip()
        if legacy:
            found.append(legacy)
    return found


def collect_models(env: dict) -> list[str]:
    """Primary model then fallback, blanks dropped, order preserved."""
    models: list[str] = []
    for var in ("GEMINI_MODEL", "GEMINI_MODEL_FALLBACK"):
        value = (env.get(var) or "").strip()
        if value and value not in models:
            models.append(value)
    return models


class Combination:
    """One (key, model) pair. Identified in logs by index, never by key."""

    __slots__ = ("key_index", "key", "model_name", "exhausted", "reason", "state")

    def __init__(self, key_index: int, key: str, model_name: str):
        self.key_index = key_index  # 1-based, matches GEMINI_API_KEY_<n>
        self.key = key
        self.model_name = model_name
        # `exhausted` means "retired, do not use again", whatever the cause.
        # `state` says which cause, because a typo and a spent quota need
        # different things done about them.
        self.exhausted = False
        self.state = "ok"  # ok | exhausted | invalid
        self.reason = ""

    @property
    def label(self) -> str:
        return f"key {self.key_index} + {self.model_name}"

    def describe(self, total_keys: int) -> dict:
        return {
            "key_index": self.key_index,
            "key_label": f"key {self.key_index} of {total_keys}",
            "model": self.model_name,
            "exhausted": self.exhausted,
            "state": self.state,
            "reason": self.reason or None,
        }


class GeminiKeyPool:
    """Ordered (key, model) combinations with sticky, one-way failover.

    `model_factory(api_key, model_name)` builds whatever the caller wants to
    call — the real SDK model in production, a stub in tests. Injected rather
    than imported so the failover logic can be tested without a key, which is
    the whole point of building this before the keys exist.
    """

    def __init__(self, keys, models, model_factory):
        self._factory = model_factory
        self._lock = threading.Lock()
        self._built: dict[tuple[int, str], object] = {}
        self.total_keys = len(keys)
        # Model-major, keys inner: every key on the primary before the fallback.
        self._combinations = [
            Combination(index, key, model)
            for model in models
            for index, key in enumerate(keys, start=1)
        ]
        self._cursor = 0

    # ---------------------------------------------------------------- state

    @property
    def combinations(self) -> list[Combination]:
        return list(self._combinations)

    @property
    def active(self):
        """The combination currently in use, or None when all are spent."""
        for combo in self._combinations[self._cursor :]:
            if not combo.exhausted:
                return combo
        return None

    def status(self) -> dict:
        """Everything the health endpoint needs, and no key material."""
        active = self.active
        return {
            "keys_configured": self.total_keys,
            "models": sorted({c.model_name for c in self._combinations}, key=self._model_order),
            "pools_total": len(self._combinations),
            "pools_exhausted": sum(1 for c in self._combinations if c.state == "exhausted"),
            # Counted apart from exhausted: a spent quota is waited out, a bad
            # key is edited in app/.env. Reading one as the other on a demo
            # morning sends you looking in the wrong place.
            "pools_invalid": sum(1 for c in self._combinations if c.state == "invalid"),
            "pools_remaining": sum(1 for c in self._combinations if not c.exhausted),
            "keys_invalid": sorted(
                {c.key_index for c in self._combinations if c.state == "invalid"}
            ),
            "active": active.describe(self.total_keys) if active else None,
            "combinations": [c.describe(self.total_keys) for c in self._combinations],
        }

    def _model_order(self, name: str) -> int:
        for i, c in enumerate(self._combinations):
            if c.model_name == name:
                return i
        return 0

    # ------------------------------------------------------------ execution

    def execute(self, call):
        """Run `call(model)` on the active combination, failing over on quota.

        Stays on whichever combination worked: the cursor only ever moves
        forward, and only when something is actually spent. A request that
        succeeds on key 3 does not send the next request back to key 1 to
        rediscover that keys 1 and 2 are empty.
        """
        if not self._combinations:
            raise AllProvidersExhausted(0, "no Gemini API keys are configured")

        last_detail = ""
        while True:
            combo = self.active
            if combo is None:
                raise AllProvidersExhausted(len(self._combinations), last_detail)

            try:
                return call(self._model_for(combo))
            except Exception as exc:
                if is_quota_error(exc):
                    last_detail = _short(exc)
                    self._retire(combo, last_detail, "exhausted")
                elif is_auth_error(exc):
                    last_detail = _short(exc)
                    # A rejected key is rejected on every model, so retire the
                    # whole key rather than discovering the same typo again on
                    # the fallback model later.
                    self._retire_key(combo, last_detail)
                else:
                    # Neither an allowance nor a credential problem. The key is
                    # fine; let the caller see the real failure rather than
                    # silently spending four more keys on the same bad network.
                    raise

    def _model_for(self, combo: Combination):
        cache_key = (combo.key_index, combo.model_name)
        with self._lock:
            model = self._built.get(cache_key)
            if model is None:
                model = self._factory(combo.key, combo.model_name)
                self._built[cache_key] = model
            return model

    def _retire_key(self, combo: Combination, detail: str) -> None:
        """Retire every combination using this key: the key itself is bad."""
        index = combo.key_index
        for other in self._combinations:
            if other.key_index == index and not other.exhausted:
                other.exhausted = True
                other.state = "invalid"
                other.reason = detail
                self._built.pop((other.key_index, other.model_name), None)
        self._advance()
        nxt = self.active
        if nxt is None:
            log.error(
                "key %d invalid, skipping; no usable key/model combinations remain",
                index,
            )
        else:
            # Deliberately NOT the same wording as an exhausted key: one is a
            # typo to fix in app/.env, the other is a quota to wait out.
            log.warning(
                "key %d invalid, skipping to key %d (of %d) on %s",
                index,
                nxt.key_index,
                self.total_keys,
                nxt.model_name,
            )

    def _advance(self) -> None:
        while self._cursor < len(self._combinations) and self._combinations[self._cursor].exhausted:
            self._cursor += 1

    def _retire(self, combo: Combination, detail: str, state: str = "exhausted") -> None:
        combo.exhausted = True
        combo.state = state
        combo.reason = detail
        # Drop the built model: it holds a key we will not use again.
        self._built.pop((combo.key_index, combo.model_name), None)
        self._advance()

        nxt = self.active
        if nxt is None:
            log.error(
                "%s exhausted; that was the last of %d key/model combinations",
                combo.label,
                len(self._combinations),
            )
        elif nxt.model_name != combo.model_name:
            log.warning(
                "key %d exhausted on %s; every key is spent on that model, "
                "switching to the fallback model %s with key %d",
                combo.key_index,
                combo.model_name,
                nxt.model_name,
                nxt.key_index,
            )
        else:
            log.warning(
                "key %d exhausted, switching to key %d (of %d) on %s",
                combo.key_index,
                nxt.key_index,
                self.total_keys,
                nxt.model_name,
            )


def _short(exc: Exception, limit: int = 120) -> str:
    """A one-line reason for the status endpoint. Never contains a key."""
    text = " ".join(str(exc).split())
    text = re.sub(r"(?i)(key|api[_-]?key)\s*[=:]\s*\S+", r"\1=<redacted>", text)
    return text[:limit]

# Owner: Nikki
"""Gemini implementation of LLMAdapter and VisionAdapter."""

import json
import os
import re
import time

import google.generativeai as genai

from ai.adapters.base import (
    LLMAdapter,
    MalformedOutputError,
    MissingConfigError,
    RateLimitError,
    VisionAdapter,
)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)

_MAX_ATTEMPTS = 2
# Longest server-requested wait we will actually sit through inside a request.
# Beyond this, failing fast beats making a patient watch a frozen kiosk.
_MAX_RETRY_WAIT_SECONDS = 20.0

# There is deliberately NO default model. Google retires model names without
# warning — gemini-1.5-flash, the previous default here, started returning 404
# and every call in the app died with it. A default would have quietly rotted
# again; an unset GEMINI_MODEL now fails immediately and says so.
_MODEL_HINT = (
    "Set GEMINI_MODEL in app/.env. Model names retire without notice, so this "
    "is deliberately not defaulted — run ListModels to see what your key can "
    "currently reach."
)
_API_KEY_HINT = "Set GEMINI_API_KEY in app/.env."


def _strip_markdown_fences(text: str) -> str:
    """Strip ```json ... ``` or ``` ... ``` fences a model tends to wrap JSON in."""
    return _FENCE_RE.sub("", text).strip()


def _parse_json(text: str) -> dict:
    cleaned = _strip_markdown_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise MalformedOutputError(f"could not parse Gemini output as JSON: {exc}") from exc


def _is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "429" in message or "rate limit" in message or "quota" in message or "resource exhausted" in message


def _retry_after_seconds(exc: Exception) -> float | None:
    """The server's own requested wait, if it sent one.

    google-api-core puts a retry_delay on the exception; it also appears in the
    message text as `retry_delay { seconds: N }`. Prefer this over guessing:
    our old fixed 1+2+4 backoff gave up after 7s while the server was asking
    for 16.8s, so every retry was wasted and the call failed anyway.
    """
    delay = getattr(exc, "retry_delay", None)
    seconds = getattr(delay, "seconds", None)
    if isinstance(seconds, (int, float)) and seconds > 0:
        return float(seconds)
    match = re.search(r"retry_delay\s*{\s*seconds:\s*(\d+)", str(exc))
    return float(match.group(1)) if match else None


def _call_with_retry(fn):
    """Call fn(), retrying only on rate-limit errors.

    Two attempts, not four. The binding limit is a per-DAY quota, so sitting
    in a backoff loop is pure dead time on a request a patient is waiting on:
    if the daily allowance is gone, no amount of retrying inside one request
    will get it back. The single retry exists for a genuine per-minute burst,
    and it waits exactly as long as the server asked.
    """
    last_exc: Exception | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            return fn()
        except Exception as exc:  # the provider SDK raises its own exception types
            if not _is_rate_limit_error(exc):
                raise
            last_exc = exc
            if attempt < _MAX_ATTEMPTS - 1:
                wait = _retry_after_seconds(exc)
                if wait is None or wait > _MAX_RETRY_WAIT_SECONDS:
                    # No hint, or a wait far longer than a patient will stand
                    # at a kiosk: fail now and surface it.
                    break
                time.sleep(wait)
    raise RateLimitError(
        f"Gemini rate limit exceeded after {_MAX_ATTEMPTS} attempts: {last_exc}"
    ) from last_exc


def _resolve(value: str | None, env_var: str, hint: str) -> str:
    """Take an explicit value, else the environment, else fail by name.

    Never `os.environ[...]` directly: a bare KeyError names the variable only
    in a traceback, and the caller cannot tell configuration from a bug.
    """
    resolved = value or os.environ.get(env_var)
    if not resolved:
        raise MissingConfigError(env_var, hint)
    return resolved


def _build_model(model_name: str | None, api_key: str | None):
    """Configure the SDK and construct a model, or fail naming what is missing."""
    genai.configure(api_key=_resolve(api_key, "GEMINI_API_KEY", _API_KEY_HINT))
    return genai.GenerativeModel(_resolve(model_name, "GEMINI_MODEL", _MODEL_HINT))


class GeminiLLMAdapter(LLMAdapter):
    """Gemini-backed text generation adapter."""

    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        self._model = _build_model(model_name, api_key)

    def complete(self, prompt: str) -> str:
        response = _call_with_retry(lambda: self._model.generate_content(prompt))
        return response.text

    def complete_json(self, prompt: str) -> dict:
        response = _call_with_retry(lambda: self._model.generate_content(prompt))
        return _parse_json(response.text)


class GeminiVisionAdapter(VisionAdapter):
    """Gemini-backed vision extraction adapter."""

    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        self._model = _build_model(model_name, api_key)

    def extract_from_image(self, image_bytes: bytes, prompt: str) -> dict:
        image_part = {"mime_type": "image/jpeg", "data": image_bytes}
        response = _call_with_retry(lambda: self._model.generate_content([prompt, image_part]))
        return _parse_json(response.text)

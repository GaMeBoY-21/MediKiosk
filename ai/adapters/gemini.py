# Owner: Nikki
"""Gemini implementation of LLMAdapter and VisionAdapter."""

import json
import logging
import os
import re
import threading

import google.generativeai as genai

from ai.adapters.base import (
    LLMAdapter,
    MalformedOutputError,
    MissingConfigError,
    VisionAdapter,
)
from ai.adapters.keypool import (
    LEGACY_KEY_VAR,
    NUMBERED_KEY_VARS,
    GeminiKeyPool,
    collect_keys,
    collect_models,
)

log = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)

# There is deliberately NO default model. Google retires model names without
# warning — gemini-1.5-flash, the previous default here, started returning 404
# and every call in the app died with it. A default would have quietly rotted
# again; an unset GEMINI_MODEL now fails immediately and says so.
_MODEL_HINT = (
    "Set GEMINI_MODEL in app/.env. Model names retire without notice, so this "
    "is deliberately not defaulted — run ListModels to see what your key can "
    "currently reach."
)
_API_KEY_HINT = (
    "Set GEMINI_API_KEY, or GEMINI_API_KEY_1..GEMINI_API_KEY_5 for the key "
    "pool, in app/.env."
)


def _strip_markdown_fences(text: str) -> str:
    """Strip ```json ... ``` or ``` ... ``` fences a model tends to wrap JSON in."""
    return _FENCE_RE.sub("", text).strip()


def _parse_json(text: str) -> dict:
    cleaned = _strip_markdown_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise MalformedOutputError(f"could not parse Gemini output as JSON: {exc}") from exc


def _resolve(value: str | None, env_var: str, hint: str) -> str:
    """Take an explicit value, else the environment, else fail by name.

    Never `os.environ[...]` directly: a bare KeyError names the variable only
    in a traceback, and the caller cannot tell configuration from a bug.
    """
    resolved = value or os.environ.get(env_var)
    if not resolved:
        raise MissingConfigError(env_var, hint)
    return resolved


# google.generativeai keeps the API key in module-level global state, so the
# key in force is whatever was configured LAST — not whatever was configured
# when a model object was built. Switching keys therefore has to happen
# immediately before the call, and two calls with different keys must not
# interleave. One lock around configure-and-call is enough for a kiosk, where
# there is one patient at a time, and is the only version of this that is
# certainly correct.
_SDK_LOCK = threading.Lock()


class _KeyedModel:
    """One (key, model) pair, applied at call time rather than at build time."""

    def __init__(self, api_key: str, model_name: str):
        self._key = api_key
        self._name = model_name

    def generate_content(self, payload):
        with _SDK_LOCK:
            genai.configure(api_key=self._key)
            return genai.GenerativeModel(self._name).generate_content(payload)


def _model_factory(api_key: str, model_name: str) -> _KeyedModel:
    return _KeyedModel(api_key, model_name)


# The keys live in app/.env, which pydantic-settings loads into `settings` --
# it does NOT put them into os.environ. Reading the process environment alone
# therefore found nothing and reported an unconfigured pool on a machine that
# was working perfectly. Settings first, real environment second, so an env
# var can still override for a one-off run.
_POOL_VARS = (
    *NUMBERED_KEY_VARS,
    LEGACY_KEY_VAR,
    "GEMINI_MODEL",
    "GEMINI_MODEL_FALLBACK",
)


def _env_mapping() -> dict:
    env = {}
    try:
        from app.config import settings
    except Exception:  # ai/ must still work with no app/ importable
        settings = None
    for name in _POOL_VARS:
        value = getattr(settings, name, None) if settings is not None else None
        env[name] = value or os.environ.get(name)
    return env


_pool_singleton: GeminiKeyPool | None = None
_pool_lock = threading.Lock()


def get_pool(env: dict | None = None, model_factory=None) -> GeminiKeyPool:
    """The process-wide key pool. Built once, then shared.

    Shared between the text and vision adapters on purpose: they draw on the
    same allowance, so a key spent by one is spent for the other, and finding
    that out twice costs two wasted calls.
    """
    global _pool_singleton
    if env is None and model_factory is None:
        with _pool_lock:
            if _pool_singleton is None:
                _pool_singleton = _build_pool(_env_mapping(), _model_factory)
            return _pool_singleton
    # Explicit env/factory: a caller building its own pool (tests).
    return _build_pool(env if env is not None else _env_mapping(), model_factory or _model_factory)


def _build_pool(env, model_factory) -> GeminiKeyPool:
    keys = collect_keys(env)
    if not keys:
        raise MissingConfigError("GEMINI_API_KEY", _API_KEY_HINT)
    models = collect_models(env)
    if not models:
        raise MissingConfigError("GEMINI_MODEL", _MODEL_HINT)
    log.info(
        "Gemini key pool: %d key(s) x %d model(s) = %d quota pool(s) [%s]",
        len(keys),
        len(models),
        len(keys) * len(models),
        ", ".join(models),
    )
    return GeminiKeyPool(keys, models, model_factory)


def reset_pool() -> None:
    """Drop the singleton. For tests and for a config reload."""
    global _pool_singleton
    with _pool_lock:
        _pool_singleton = None


class GeminiLLMAdapter(LLMAdapter):
    """Gemini-backed text generation adapter, backed by the key pool."""

    def __init__(self, model_name: str | None = None, api_key: str | None = None, pool=None):
        # An explicit key or model still works and pins a single-combination
        # pool, so existing callers and one-off scripts behave as before.
        if pool is not None:
            self._pool = pool
        elif api_key or model_name:
            keys = [_resolve(api_key, "GEMINI_API_KEY", _API_KEY_HINT)]
            models = [_resolve(model_name, "GEMINI_MODEL", _MODEL_HINT)]
            self._pool = GeminiKeyPool(keys, models, _model_factory)
        else:
            self._pool = get_pool()

    @property
    def pool(self) -> GeminiKeyPool:
        return self._pool

    def complete(self, prompt: str) -> str:
        return self._pool.execute(lambda m: m.generate_content(prompt)).text

    def complete_json(self, prompt: str) -> dict:
        response = self._pool.execute(lambda m: m.generate_content(prompt))
        return _parse_json(response.text)


class GeminiVisionAdapter(VisionAdapter):
    """Gemini-backed vision extraction adapter, backed by the same key pool."""

    def __init__(self, model_name: str | None = None, api_key: str | None = None, pool=None):
        if pool is not None:
            self._pool = pool
        elif api_key or model_name:
            keys = [_resolve(api_key, "GEMINI_API_KEY", _API_KEY_HINT)]
            models = [_resolve(model_name, "GEMINI_MODEL", _MODEL_HINT)]
            self._pool = GeminiKeyPool(keys, models, _model_factory)
        else:
            self._pool = get_pool()

    def extract_from_image(self, image_bytes: bytes, prompt: str) -> dict:
        image_part = {"mime_type": "image/jpeg", "data": image_bytes}
        response = self._pool.execute(lambda m: m.generate_content([prompt, image_part]))
        return _parse_json(response.text)

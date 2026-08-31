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
    RateLimitError,
    VisionAdapter,
)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)

_MAX_ATTEMPTS = 4
_BASE_DELAY_SECONDS = 1.0
_DEFAULT_MODEL = "gemini-1.5-flash"


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


def _call_with_retry(fn):
    """Call fn(), retrying with exponential backoff only on rate-limit errors."""
    last_exc: Exception | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            return fn()
        except Exception as exc:  # the provider SDK raises its own exception types
            if not _is_rate_limit_error(exc):
                raise
            last_exc = exc
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_BASE_DELAY_SECONDS * (2**attempt))
    raise RateLimitError(f"Gemini rate limit exceeded after {_MAX_ATTEMPTS} attempts") from last_exc


def _configure(api_key: str | None) -> None:
    genai.configure(api_key=api_key or os.environ["GEMINI_API_KEY"])


class GeminiLLMAdapter(LLMAdapter):
    """Gemini-backed text generation adapter."""

    def __init__(self, model_name: str = _DEFAULT_MODEL, api_key: str | None = None):
        _configure(api_key)
        self._model = genai.GenerativeModel(model_name)

    def complete(self, prompt: str) -> str:
        response = _call_with_retry(lambda: self._model.generate_content(prompt))
        return response.text

    def complete_json(self, prompt: str) -> dict:
        response = _call_with_retry(lambda: self._model.generate_content(prompt))
        return _parse_json(response.text)


class GeminiVisionAdapter(VisionAdapter):
    """Gemini-backed vision extraction adapter."""

    def __init__(self, model_name: str = _DEFAULT_MODEL, api_key: str | None = None):
        _configure(api_key)
        self._model = genai.GenerativeModel(model_name)

    def extract_from_image(self, image_bytes: bytes, prompt: str) -> dict:
        image_part = {"mime_type": "image/jpeg", "data": image_bytes}
        response = _call_with_retry(lambda: self._model.generate_content([prompt, image_part]))
        return _parse_json(response.text)

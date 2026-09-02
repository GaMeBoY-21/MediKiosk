# Owner: Nikki
"""Abstract adapter interfaces for LLM and vision providers.

Everything else in ai/ calls these interfaces, never a provider SDK directly.
This keeps the rest of the AI layer swappable and testable without Gemini.
"""

from abc import ABC, abstractmethod


class LLMAdapterError(Exception):
    """Base error for LLM/vision adapter failures."""


class MalformedOutputError(LLMAdapterError):
    """Raised when a provider's response can't be parsed as expected JSON."""


class RateLimitError(LLMAdapterError):
    """Raised when a provider is still rate-limiting us after retries are exhausted."""


class AllProvidersExhausted(LLMAdapterError):
    """Every (key, model) combination in the pool has hit its quota.

    Deliberately NOT a RateLimitError. RateLimitError means "this provider is
    busy, the request failed" — something a caller might sensibly retry.
    This means there is nothing left to retry with until a quota window rolls
    over, which for the daily limit is tomorrow. The two need different
    handling and, at a kiosk, different words on the screen.
    """

    def __init__(self, tried: int, detail: str = ""):
        self.tried = tried
        message = f"all {tried} Gemini key/model combinations are exhausted"
        if detail:
            message = f"{message}: {detail}"
        super().__init__(message)


class MissingConfigError(LLMAdapterError):
    """Raised when a required setting is absent.

    Always names the missing variable. A bare KeyError from os.environ tells
    whoever is standing at the kiosk nothing about which value to set.
    """

    def __init__(self, variable: str, hint: str = ""):
        self.variable = variable
        message = f"{variable} is not set"
        if hint:
            message = f"{message}. {hint}"
        super().__init__(message)


class LLMAdapter(ABC):
    """Interface for a text-generation LLM provider."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Return a free-text completion for the given prompt."""
        raise NotImplementedError

    @abstractmethod
    def complete_json(self, prompt: str) -> dict:
        """Return a parsed JSON object for the given prompt.

        The prompt is responsible for constraining the model to a JSON
        schema. Raises MalformedOutputError if the response can't be parsed
        as JSON — never returns None on a bad response.
        """
        raise NotImplementedError


class VisionAdapter(ABC):
    """Interface for a vision-capable model provider."""

    @abstractmethod
    def extract_from_image(self, image_bytes: bytes, prompt: str) -> dict:
        """Extract structured data from an image given a prompt.

        Raises MalformedOutputError if the response can't be parsed as JSON.
        """
        raise NotImplementedError

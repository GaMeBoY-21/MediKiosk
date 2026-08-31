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

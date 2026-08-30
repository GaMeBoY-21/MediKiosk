# Owner: Nikki
"""Abstract adapter interfaces for LLM and vision providers."""

from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    """Interface for a text-generation LLM provider."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a text response for the given prompt.

        TODO: implement per-provider.
        """
        raise NotImplementedError


class VisionAdapter(ABC):
    """Interface for a vision-capable model provider."""

    @abstractmethod
    def extract(self, image_bytes: bytes, prompt: str) -> dict:
        """Extract structured data from an image given a prompt.

        TODO: implement per-provider.
        """
        raise NotImplementedError

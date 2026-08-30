# Owner: Nikki
"""Gemini implementation of LLMAdapter and VisionAdapter."""

from ai.adapters.base import LLMAdapter, VisionAdapter


class GeminiLLMAdapter(LLMAdapter):
    """Gemini-backed text generation adapter."""

    def generate(self, prompt: str) -> str:
        """TODO: call google-generativeai text generation."""
        raise NotImplementedError


class GeminiVisionAdapter(VisionAdapter):
    """Gemini-backed vision extraction adapter."""

    def extract(self, image_bytes: bytes, prompt: str) -> dict:
        """TODO: call google-generativeai vision extraction."""
        raise NotImplementedError

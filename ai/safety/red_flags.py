# Owner: Nikki
"""Deterministic red-flag rules. No LLM calls in this module."""

# TODO: populate with deterministic symptom/keyword -> red-flag mappings.
RED_FLAG_RULES: dict = {}


def check_red_flags(fields: dict) -> list:
    """Check extracted fields against RED_FLAG_RULES.

    TODO: implement deterministic rule matching.
    """
    raise NotImplementedError

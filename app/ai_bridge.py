# Owner: Tharun
"""The single boundary between app/ and ai/.

Nikki owns ai/. Every function there is currently a stub that raises
NotImplementedError, and will be for a while yet. Each call is wrapped here so
that a missing, half-built or crashing AI function degrades to the deterministic
fallback in app/fixtures.py instead of taking the API down mid-demo.

The rule: nothing in app/routers imports ai/ directly. If a new AI capability is
needed, add a wrapper here.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app import fixtures
from app.config import settings
from app.schemas import FlagSeverity, RedFlag

log = logging.getLogger(__name__)

# Logged once per capability so a demo does not scroll with the same warning.
_warned: set[str] = set()


def _degrade(capability: str, exc: Exception) -> None:
    if capability not in _warned:
        _warned.add(capability)
        kind = "not implemented" if isinstance(exc, NotImplementedError) else type(exc).__name__
        log.warning("ai.%s unavailable (%s) - using deterministic fallback", capability, kind)


# Fixtures still drive the live question set (Block 4 swaps that over to
# ai.interview.nodes), so extraction is scoped to the single clinical field
# each fixtures node is actually asking about. Names match
# ai.interview.nodes' own field names, so this stays compatible once the
# node graph swap happens.
_FIXTURE_NODE_FIELDS: Dict[str, str] = {
    "duration": "symptom_duration",
    "severity": "symptom_severity",
    "pattern": "symptom_timing",
    "associated": "associated_symptoms",
    "medicines": "current_medications",
    "conditions": "past_medical_conditions",
}

_llm_singleton = None  # type: ignore[var-annotated]


def _llm():
    """Lazy singleton so a missing GEMINI_API_KEY fails on first real use,
    not at import time, and so we don't re-configure the SDK per request."""
    global _llm_singleton
    if _llm_singleton is None:
        from ai.adapters.gemini import GeminiLLMAdapter

        _llm_singleton = GeminiLLMAdapter(api_key=settings.GEMINI_API_KEY)
    return _llm_singleton


def next_node(current_node: Optional[str], language: str) -> Optional[Dict[str, Any]]:
    """Resolve the next interview node.

    Tries ai.interview.state_machine; falls back to the fixed node order.
    """
    try:
        from ai.interview import state_machine

        node = state_machine.transition({"current_node": current_node, "language": language}, "")
        if node:
            return node
    except Exception as exc:  # noqa: BLE001 - any failure must degrade, not raise
        _degrade("interview.state_machine", exc)

    next_id = fixtures.next_node_id(current_node)
    return fixtures.render_node(next_id, language) if next_id else None


def extract_fields(node_id: str, transcript: str) -> Dict[str, Any]:
    """Turn free speech into structured fields via ai.interview.extraction.

    No fallback: this is the one capability that is genuinely live. A
    failure here (missing GEMINI_API_KEY, a malformed model response that
    survives ai/'s own handling, ai/ being broken) is a real failure and
    must be visible, not silently swallowed into canned output.
    """
    if not transcript:
        return {}

    from ai.interview import extraction
    from ai.interview.nodes import InterviewNode

    field_name = _FIXTURE_NODE_FIELDS.get(node_id, node_id)
    node = InterviewNode(id=node_id, phase_label=node_id, required_fields=(), optional_fields=(field_name,))

    extracted = extraction.extract_fields(transcript, node, _llm())
    return extraction.fields_to_dict(extracted)


def check_red_flags(
    node_id: str,
    selected_option: Optional[str],
    transcript: Optional[str],
    extracted: Optional[Dict[str, Any]] = None,
) -> Optional[RedFlag]:
    """Evaluate safety rules synchronously.

    This path never calls a model and never waits on the summary. The local
    deterministic rules run FIRST and win, so the emergency screen appears on
    the patient's next tap whatever state ai/ is in. ai.safety is consulted only
    to add flags the local rules did not already catch — it is itself a rules
    dict, not an LLM.
    """
    local = fixtures.evaluate_red_flags(node_id, selected_option, transcript)
    if local is not None:
        return local

    try:
        from ai.safety import red_flags as ai_red_flags

        fields = dict(extracted or {})
        fields.setdefault("node_id", node_id)
        if selected_option:
            fields.setdefault(node_id, selected_option)

        found: List[Any] = ai_red_flags.check_red_flags(fields) or []
        if found:
            first = found[0]
            if isinstance(first, RedFlag):
                return first
            if isinstance(first, dict):
                return RedFlag(
                    rule_id=first.get("rule_id", "AI_RULE"),
                    label=first.get("label", "safety rule triggered"),
                    severity=FlagSeverity(first.get("severity", FlagSeverity.high.value)),
                    triggered_by=first.get("triggered_by", [node_id]),
                )
    except Exception as exc:  # noqa: BLE001
        _degrade("safety.red_flags", exc)

    return None


def generate_summary(clinical_record: Dict[str, Any]) -> Optional[str]:
    """Narrative HPI for the physician. None falls back to the canned narrative."""
    try:
        from ai.summary import generator

        return generator.generate_summary(clinical_record) or None
    except Exception as exc:  # noqa: BLE001
        _degrade("summary.generator", exc)
        return None


def extract_document(image_bytes: bytes) -> Dict[str, Any]:
    """Read a photographed document. Empty dict leaves the doc queued."""
    try:
        from ai.documents import extract

        return extract.extract_document(image_bytes) or {}
    except Exception as exc:  # noqa: BLE001
        _degrade("documents.extract", exc)
        return {}

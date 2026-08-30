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
from app.schemas import FlagSeverity, RedFlag

log = logging.getLogger(__name__)

# Logged once per capability so a demo does not scroll with the same warning.
_warned: set[str] = set()


def _degrade(capability: str, exc: Exception) -> None:
    if capability not in _warned:
        _warned.add(capability)
        kind = "not implemented" if isinstance(exc, NotImplementedError) else type(exc).__name__
        log.warning("ai.%s unavailable (%s) - using deterministic fallback", capability, kind)


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


def extract_fields(transcript: str) -> Dict[str, Any]:
    """Turn free speech into structured fields. Empty dict when unavailable."""
    if not transcript:
        return {}
    try:
        from ai.interview import extraction

        return extraction.extract_fields(transcript) or {}
    except Exception as exc:  # noqa: BLE001
        _degrade("interview.extraction", exc)
        return {}


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

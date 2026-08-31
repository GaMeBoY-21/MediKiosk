# Owner: Tharun
"""The single boundary between app/ and ai/.

The rule: nothing in app/routers imports ai/ directly. If a new AI capability
is needed, add a wrapper here.

ai/ is built, so most of this no longer degrades to a fallback. Two different
policies live side by side, deliberately:

  - check_red_flags has NO fallback and no try/except. It is a safety layer;
    if it breaks the request must 500 so we find out immediately rather than
    from a canned answer in front of a judge.
  - next_node / extract_fields / generate_summary have no fallback either,
    because their output depends on what the patient actually said — there is
    nothing meaningful to fall back TO.
  - extract_document still degrades, and is still wired to a signature that
    does not exist (see below).

KNOWN BUG, still live: extract_document() calls
ai.documents.extract.extract_document(image_bytes) but the real function takes
(image_bytes, doc_id, vision) and returns a DocumentRecord, not a dict. The
try/except swallows the TypeError, so every upload silently yields {}. Left as
found — fixing it is its own piece of work, not a red-flag change.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.config import settings
from app.schemas import ClinicalSummary, DocumentRecord, ExtractedField, FlagSeverity, RedFlag

log = logging.getLogger(__name__)

# Logged once per capability so a demo does not scroll with the same warning.
_warned: set[str] = set()


def _degrade(capability: str, exc: Exception) -> None:
    if capability not in _warned:
        _warned.add(capability)
        kind = "not implemented" if isinstance(exc, NotImplementedError) else type(exc).__name__
        log.warning("ai.%s unavailable (%s) - using deterministic fallback", capability, kind)


_llm_singleton = None  # type: ignore[var-annotated]


def _llm():
    """Lazy singleton so a missing GEMINI_API_KEY fails on first real use,
    not at import time, and so we don't re-configure the SDK per request."""
    global _llm_singleton
    if _llm_singleton is None:
        from ai.adapters.gemini import GeminiLLMAdapter

        _llm_singleton = GeminiLLMAdapter(api_key=settings.GEMINI_API_KEY)
    return _llm_singleton


def estimated_total_nodes() -> int:
    """Rough progress denominator for Progress.total.

    The real interview has no fixed length — a chest-pain complaint runs the
    full HPI branch, a rash gets three questions and moves on — so this is
    only ever a best estimate (the node count, not the question count), never
    an exact total.
    """
    from ai.interview.nodes import NODE_ORDER

    return len(NODE_ORDER)


def next_node(
    fields: Dict[str, Any], follow_up_counts: Dict[str, int], language: str
) -> Optional[Dict[str, Any]]:
    """Resolve and render the next interview question, live from ai/.

    No fallback: which node comes next depends on which fields are already
    filled, so there is no fixed order left to fall back to. `follow_up_counts`
    is mutated in place — the caller's SessionState.follow_up_counts is the
    same dict, so the increment for the node just asked persists.

    Returns None when the interview is complete (state_machine.next_node
    returns no further node), otherwise a dict shaped like the old
    fixtures.render_node() output: {node_id, question, options, allow_free_text,
    node_type}.
    """
    from ai.interview import followup
    from ai.interview.state_machine import next_node as sm_next_node, record_follow_up

    session_state = {"fields": fields, "follow_up_counts": follow_up_counts}
    node = sm_next_node(session_state)
    if node is None:
        return None

    record_follow_up(session_state, node.id)

    question_text, options = followup.generate_followup(node, fields, language, _llm())

    return {
        "node_id": node.id,
        "question": question_text,
        "options": [{"value": o.value, "label": o.label} for o in options],
        "allow_free_text": True,
        "node_type": "single_choice" if options else "free_text",
    }


def extract_fields(node_id: str, transcript: str) -> List[ExtractedField]:
    """Turn free speech into structured fields via ai.interview.extraction.

    Returns the full ExtractedField list rather than a flat {name: value}
    dict, so the caller can keep each field's confidence alongside its value
    — the summary needs that to hedge low-confidence fields instead of
    asserting every value with equal certainty.

    No fallback: this is genuinely live. A failure here (missing
    GEMINI_API_KEY, a malformed model response that survives ai/'s own
    handling, ai/ being broken) is a real failure and must be visible, not
    silently swallowed into canned output.
    """
    if not transcript:
        return []

    from ai.interview import extraction
    from ai.interview.nodes import InterviewNode, get_node

    try:
        node = get_node(node_id)
    except KeyError:
        # Not one of ai.interview.nodes' own ids (e.g. a node from an older
        # session, or a caller passing something ad hoc). Scope extraction to
        # a single field named after the node itself rather than refusing.
        node = InterviewNode(id=node_id, phase_label=node_id, required_fields=(), optional_fields=(node_id,))

    return extraction.extract_fields(transcript, node, _llm())


# Worst-first, so a critical always wins over a high when several rules fire
# at once and the response can only carry one flag.
_SEVERITY_RANK: Dict[FlagSeverity, int] = {
    FlagSeverity.critical: 0,
    FlagSeverity.high: 1,
    FlagSeverity.moderate: 2,
    FlagSeverity.low: 3,
}


def check_red_flags(extracted: Dict[str, Any]) -> Optional[RedFlag]:
    """Evaluate safety rules synchronously against the session's extracted fields.

    Deliberately NO try/except and no fallback. A safety layer that fails
    silently is worse than one that fails loudly: if this raises, the request
    must 500 so the failure is seen immediately, not discovered from a canned
    answer during a demo.

    Evaluated on extracted fields, never on the raw transcript. Extraction
    already translates every value into English clinical terms, so a Hindi
    speaker and an English speaker describing the same symptom produce the
    same fields and therefore the same flags. Matching English literals
    against raw speech was the old bug — it silently no-op'd for six of the
    seven languages.

    Never calls a model and never touches the network: ai.safety.red_flags is
    pure Python, so this stays fast enough to run inline on every answer.
    """
    from ai.safety.red_flags import evaluate

    found = evaluate(extracted)
    if not found:
        return None
    return min(found, key=lambda f: _SEVERITY_RANK.get(f.severity, 99))


def generate_summary(
    extracted_fields: List[ExtractedField], document_timeline: List[DocumentRecord]
) -> ClinicalSummary:
    """Physician-facing clinical summary, genuinely generated from the
    session's extracted fields and document timeline. No fallback: red_flags,
    token and room are not ai/'s to set, so the caller fills those in after.
    """
    from ai.summary import generator

    return generator.generate_summary(extracted_fields, document_timeline, _llm())


def extract_document(image_bytes: bytes) -> Dict[str, Any]:
    """Read a photographed document. Empty dict leaves the doc queued."""
    try:
        from ai.documents import extract

        return extract.extract_document(image_bytes) or {}
    except Exception as exc:  # noqa: BLE001
        _degrade("documents.extract", exc)
        return {}

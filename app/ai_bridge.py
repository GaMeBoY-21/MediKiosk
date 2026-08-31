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
import re
from typing import Any, Dict, List, Optional

from app.config import settings
from app.schemas import (
    ClinicalSummary,
    DocumentRecord,
    ExtractedField,
    FieldSource,
    FlagSeverity,
    RedFlag,
)

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

        _llm_singleton = GeminiLLMAdapter(
            model_name=settings.GEMINI_MODEL, api_key=settings.GEMINI_API_KEY
        )
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

    target_field, question_text, options = followup.generate_followup(
        node, fields, language, _llm()
    )
    return _render(node.id, question_text, options, target_field)


_AGE_RE = re.compile(r"\d{1,3}")

# Fields whose schema type is stricter than the prose a patient speaks.
# Identity.age is Optional[int], but a patient says "54 years" / "पैंतालीस साल"
# and extraction faithfully returns "54 years". Coerce here, at the boundary,
# rather than loosening the schema to accept prose — the schema is the contract
# the physician console and the FHIR bundle both read.
def _coerce_age(value: Any) -> Any:
    """"54 years" -> 54. Anything with no parseable number is dropped.

    Returning None (rather than the prose) means the field is omitted, which
    is the honest outcome: better an absent age than a string the console
    cannot render and FHIR cannot encode. The patient's exact words are still
    in the transcript.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 0 <= value <= 130 else None
    match = _AGE_RE.search(str(value))
    if not match:
        return None
    age = int(match.group())
    return age if 0 <= age <= 130 else None


_COERCERS = {"age": _coerce_age}


def _coerce_fields(fields: List[ExtractedField]) -> List[ExtractedField]:
    """Apply per-field type coercion, dropping values that cannot be coerced."""
    out: List[ExtractedField] = []
    for f in fields:
        coercer = _COERCERS.get(f.name)
        if coercer is None:
            out.append(f)
            continue
        coerced = coercer(f.value)
        if coerced is None:
            log.info("dropping %s=%r: could not coerce to the schema type", f.name, f.value)
            continue
        out.append(f.model_copy(update={"value": coerced}))
    return out


def _render(node_id: str, question: str, options, target_field: str = "") -> Dict[str, Any]:
    """Shape a question the way the frontend expects it.

    `target_field` is internal: the session store keeps it so that when the
    patient taps one of these options, the tapped value can be filed under
    the right field without another model call. It is not part of the
    AnswerResponse the kiosk renders.
    """
    return {
        "node_id": node_id,
        "question": question,
        "options": [{"value": o.value, "label": o.label} for o in options],
        "allow_free_text": True,
        "node_type": "single_choice" if options else "free_text",
        "target_field": target_field,
    }


def _node_if_current_completes(fields: Dict[str, Any], node, follow_up_counts: Dict[str, int]):
    """Which node the state machine WOULD pick if `node` were fully answered.

    Computed here, by the state machine, before the LLM is called — so the
    branch the model is handed is one we already sanctioned. Uses copies so
    the real session state is untouched.
    """
    from ai.interview.state_machine import next_node as sm_next_node

    hypothetical = dict(fields)
    for field_name in node.required_fields:
        hypothetical.setdefault(field_name, "__assumed__")
    return sm_next_node({"fields": hypothetical, "follow_up_counts": dict(follow_up_counts)})


def answer_turn(
    node_id: str,
    transcript: str,
    selected_option: Optional[str],
    target_field: Optional[str],
    fields: Dict[str, Any],
    follow_up_counts: Dict[str, int],
    language: str,
) -> tuple[List[ExtractedField], Optional[Dict[str, Any]]]:
    """Extract this answer AND get the next question, normally in ONE call.

    Replaces the old extract_fields() + next_node() pair on the answer path,
    which cost two serial round trips per tap — the patient waited for both,
    and both counted against a small daily quota.

    The state machine stays authoritative. It decides the current node and
    precomputes the one legal onward branch; the model is told that branch
    rather than choosing it. Afterwards we re-run the state machine on the
    merged fields, and if the model answered for a different node than the one
    we actually landed on, its question is discarded and a correct one is
    generated (costing the second call we normally save).

    Returns (extracted fields, rendered next question or None when finished).
    """
    from ai.interview import followup
    from ai.interview.nodes import InterviewNode, get_node
    from ai.interview.state_machine import next_node as sm_next_node, record_follow_up
    from ai.interview.turn import run_turn

    try:
        node = get_node(node_id)
    except KeyError:
        node = InterviewNode(
            id=node_id, phase_label=node_id, required_fields=(), optional_fields=(node_id,)
        )

    # The patient tapped a tile instead of speaking. The tapped value is
    # already a canonical English token chosen from options we generated, so
    # there is nothing to transcribe, translate or infer: build the field
    # directly, at full confidence, with no model call and no quota spent.
    #
    # This path used to produce nothing at all, which meant a touch-only
    # patient finished the interview with an empty history AND — because red
    # flags are evaluated on extracted fields — no safety coverage whatsoever.
    if not transcript:
        tapped: List[ExtractedField] = []
        if selected_option and target_field:
            tapped = _coerce_fields(
                [
                    ExtractedField(
                        name=target_field,
                        value=selected_option,
                        confidence=1.0,
                        source=FieldSource.touch,
                    )
                ]
            )
        elif selected_option:
            # An option came back but we no longer know which field it fills
            # (e.g. the session state was lost to a restart). Say so loudly —
            # silently dropping a clinical answer is what this block exists to
            # stop.
            log.warning(
                "tapped option %r on node %r discarded: no target field recorded",
                selected_option,
                node_id,
            )

        merged_taps = dict(fields)
        merged_taps.update({f.name: f.value for f in tapped})
        return tapped, next_node(merged_taps, follow_up_counts, language)

    advance_node = _node_if_current_completes(fields, node, follow_up_counts)
    result = run_turn(transcript, node, advance_node, fields, language, _llm())

    coerced = _coerce_fields(result.fields)
    merged = dict(fields)
    merged.update({f.name: f.value for f in coerced})

    session_state = {"fields": merged, "follow_up_counts": follow_up_counts}
    actual = sm_next_node(session_state)
    if actual is None:
        return coerced, None

    record_follow_up(session_state, actual.id)

    # Trust the model's question only if it wrote it for the node we actually
    # landed on, and it actually produced one.
    if result.asking_about == actual.id and result.question:
        return coerced, _render(
            actual.id, result.question, result.options, result.target_field
        )

    log.info(
        "turn: regenerating question (model asked about %r, state machine says %r)",
        result.asking_about,
        actual.id,
    )
    target_field, question_text, options = followup.generate_followup(
        actual, merged, language, _llm()
    )
    return coerced, _render(actual.id, question_text, options, target_field)


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

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
  - extract_document degrades ONLY on a provider failure (LLMAdapterError),
    because a document can be re-read later. A TypeError or AttributeError is
    a bug in our code and propagates. It used to catch bare Exception, which
    swallowed a wrong-arity call and made every upload silently yield {}.
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
    """Lazy singleton so a missing key fails on first real use, not at import.

    Deliberately constructed with NO explicit key or model: passing them pins
    the adapter to that single pair and bypasses the failover pool entirely,
    which is how the pool came to exist and then never be used. Unset, the
    adapter draws on the shared pool built from GEMINI_API_KEY_1..5 (or the
    single GEMINI_API_KEY) and GEMINI_MODEL / GEMINI_MODEL_FALLBACK.
    """
    global _llm_singleton
    if _llm_singleton is None:
        from ai.adapters.gemini import GeminiLLMAdapter

        _llm_singleton = GeminiLLMAdapter()
    return _llm_singleton


_vision_singleton = None  # type: ignore[var-annotated]


def _vision():
    """Vision adapter singleton. Same model id as text — the Gemini flash
    models are multimodal, so one GEMINI_MODEL setting covers both."""
    global _vision_singleton
    if _vision_singleton is None:
        from ai.adapters.gemini import GeminiVisionAdapter

        # Same reasoning as _llm(): no explicit key or model, so both adapters
        # share one pool and a key spent by one is known to be spent by the other.
        _vision_singleton = GeminiVisionAdapter()
    return _vision_singleton


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
    fields: Dict[str, Any],
    follow_up_counts: Dict[str, int],
    language: str,
    field_ask_counts: Optional[Dict[str, int]] = None,
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
    from ai.interview.state_machine import (
        next_node as sm_next_node,
        record_field_ask,
        record_follow_up,
    )

    session_state = _session_state(fields, follow_up_counts, field_ask_counts)
    node = sm_next_node(session_state)
    if node is None:
        return None

    record_follow_up(session_state, node.id)

    target_field, question_text, question_en, options = followup.generate_followup(
        node, fields, language, _llm(), capped_fields=_capped_fields(fields, field_ask_counts)
    )
    # Counted when the question is RENDERED, not when it comes back answered —
    # an ask that gets no answer is exactly what the cap is there to count.
    record_field_ask(session_state, target_field)
    return _render(
        node.id,
        question_text,
        options,
        target_field,
        _is_multi(node, target_field),
        node.phase_key,
        question_en,
    )


def _session_state(
    fields: Dict[str, Any],
    follow_up_counts: Dict[str, int],
    field_ask_counts: Optional[Dict[str, int]],
) -> Dict[str, Any]:
    """The dict shape ai.interview.state_machine reads.

    Both counter dicts are passed by reference, not copied: the caller's
    SessionState holds the same objects, so an increment recorded here
    persists to the next request instead of being thrown away with this one.
    """
    return {
        "fields": fields,
        "follow_up_counts": follow_up_counts,
        "field_ask_counts": field_ask_counts if field_ask_counts is not None else {},
    }


def _capped_fields(
    fields: Dict[str, Any], field_ask_counts: Optional[Dict[str, int]]
) -> List[str]:
    """Fields asked about MAX_FIELD_ASKS times and still empty.

    The interview has given up on these. They must not be offered back to the
    model as something to ask about, or the cap buys nothing — the model just
    asks again and the loop the cap exists to break carries on.
    """
    from ai.interview.state_machine import MAX_FIELD_ASKS

    return [
        name
        for name, count in (field_ask_counts or {}).items()
        if count >= MAX_FIELD_ASKS and name not in fields
    ]


def reconcile_fields(fields: Dict[str, Any]) -> List[ExtractedField]:
    """Fields implied by ones already captured, as ExtractedField.

    Runs after every extraction and after seeding, BEFORE the state machine
    is asked what is still missing. "back pain" fills symptom_site=back here,
    so the kiosk never asks a patient where the pain is when they have
    already said. Deterministic — a lookup table in ai/knowledge/, not a
    model call.

    Marked source=derived and confidence 1.0: the table is exact, but the
    physician's console can still tell a value the patient said from one the
    kiosk worked out.
    """
    from ai.interview.reconcile import derive_fields

    return [
        ExtractedField(name=name, value=value, confidence=1.0, source=FieldSource.derived)
        for name, value in derive_fields(fields).items()
    ]


_AGE_RE = re.compile(r"\d{1,3}")

# Fields whose schema type is stricter than the prose a patient speaks.
# Identity.age is Optional[int], but a patient says "54 years" / "पैंतालीस साल"
# and extraction faithfully returns "54 years". Coerce here, at the boundary,
# rather than loosening the schema to accept prose — the schema is the contract
# the physician console and the FHIR bundle both read.
# Units that mean this is NOT a number of years. "7 months" must never be
# stored as 7 — that is an infant recorded as a schoolchild.
_SUB_YEAR_RE = re.compile(r"\b(month|months|week|weeks|day|days|mah[ie]ne|din)\b", re.IGNORECASE)


def _coerce_age(value: Any) -> Any:
    """"54 years" -> 54. Anything else is dropped rather than guessed at.

    Identity.age is a whole number of years. An age given in months, weeks or
    days cannot be squeezed into that without lying: "7 months" parsed as 7
    would put an infant into the record as a seven-year-old, and every
    downstream reader — console, FHIR bundle, physician — would believe it.
    There is nowhere in the schema to put a sub-year age, so we refuse it
    loudly instead of inventing a plausible number.

    Returning None omits the field. Better an absent age the physician asks
    about than a confident wrong one they do not think to question. The
    patient's exact words survive in the transcript either way.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 0 <= value <= 130 else None

    text = str(value)
    if _SUB_YEAR_RE.search(text):
        log.warning(
            "refusing to coerce age %r: expressed in months/weeks/days, and the "
            "schema only holds whole years. Field dropped rather than guessed.",
            text,
        )
        return None

    match = _AGE_RE.search(text)
    if not match:
        return None
    age = int(match.group())
    return age if 0 <= age <= 130 else None


_COERCERS = {"age": _coerce_age}


def coerce_known_value(name: str, value: Any) -> Any:
    """Coerce one already-structured value to its schema type.

    Same rules as extracted speech: a value the kiosk collected on its own
    screen still has to satisfy Identity.age being an int. Returns None when
    the value cannot be coerced, and the caller drops it.
    """
    coercer = _COERCERS.get(name)
    return coercer(value) if coercer else value


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


def _attach_display(fields: List[ExtractedField], options=None) -> None:
    """Give every field a patient-readable display string, in place.

    Only a GENUINE label is set here — one written in the patient's language
    for an option that was actually on screen. A field with nothing better
    keeps display=None and the fallback happens in one place
    (clinical_state.understanding), which can also see what the other fields
    were labelled and let a derived field borrow from the answer it came from.

    Only `display` is touched. `value` is what every rule reads and is left
    exactly as it arrived.
    """
    from ai.interview.display import label_for

    for f in fields:
        if f.display:
            continue
        f.display = label_for(f.value, options)


def _render(
    node_id: str,
    question: str,
    options,
    target_field: str = "",
    multi: bool = False,
    phase: str = "",
    question_en: Optional[str] = None,
) -> Dict[str, Any]:
    """Shape a question the way the frontend expects it.

    `target_field` is internal: the session store keeps it so that when the
    patient taps one of these options, the tapped value can be filed under
    the right field without another model call. It is not part of the
    AnswerResponse the kiosk renders.
    """
    return {
        "node_id": node_id,
        "question": question,
        # None when the patient's language is English, so the kiosk renders one
        # line rather than the same sentence twice.
        "question_en": question_en,
        "options": [
            {"value": o.value, "label": o.label, "label_en": o.label_en} for o in options
        ],
        "allow_free_text": True,
        "node_type": ("multi_choice" if multi else "single_choice") if options else "free_text",
        "target_field": target_field,
        "multi_select": bool(multi and options),
        "phase": phase,
    }


def _is_multi(node, target_field: str) -> bool:
    return bool(target_field) and target_field in getattr(node, "multi_select_fields", ())


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
    selected_options: Optional[List[str]],
    target_field: Optional[str],
    fields: Dict[str, Any],
    follow_up_counts: Dict[str, int],
    language: str,
    field_ask_counts: Optional[Dict[str, int]] = None,
    asked_options: Optional[List[Dict[str, Any]]] = None,
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
    from ai.interview.display import label_for
    from ai.interview.nodes import InterviewNode, get_node
    from ai.interview.state_machine import (
        next_node as sm_next_node,
        record_field_ask,
        record_follow_up,
    )
    from ai.interview.turn import run_turn

    try:
        node = get_node(node_id)
    except KeyError:
        node = InterviewNode(
            id=node_id,
            phase_key=node_id,
            phase_label=node_id,
            required_fields=(),
            optional_fields=(node_id,),
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
        # A multi_choice node sends several values; a single_choice node
        # sends one. Store a list for multi-select so the red-flag rules
        # and the summary both see every symptom the patient picked, not
        # just the first.
        picked = list(selected_options or ([selected_option] if selected_option else []))
        value: Any = picked if len(picked) > 1 else (picked[0] if picked else None)
        if picked and target_field:
            tapped = _coerce_fields(
                [
                    ExtractedField(
                        name=target_field,
                        value=value,
                        confidence=1.0,
                        source=FieldSource.touch,
                        # The patient's own language, already written: this is
                        # the label on the tile they touched. Losing it here is
                        # what left the panel showing "1_day".
                        display=label_for(value, asked_options),
                    )
                ]
            )
        elif picked:
            # An option came back but we no longer know which field it fills
            # (e.g. the session state was lost to a restart). Say so loudly —
            # silently dropping a clinical answer is what this block exists to
            # stop.
            log.warning(
                "tapped option(s) %r on node %r discarded: no target field recorded",
                picked,
                node_id,
            )

        merged_taps = dict(fields)
        merged_taps.update({f.name: f.value for f in tapped})
        # Reconcile before the state machine is consulted, on the tap path
        # too: tapping the "back" tile answers "where?" just as saying it does.
        derived = reconcile_fields(merged_taps)
        merged_taps.update({f.name: f.value for f in derived})
        return tapped + derived, next_node(
            merged_taps, follow_up_counts, language, field_ask_counts
        )

    capped = _capped_fields(fields, field_ask_counts)
    advance_node = _node_if_current_completes(fields, node, follow_up_counts)
    result = run_turn(
        transcript,
        node,
        advance_node,
        fields,
        language,
        _llm(),
        capped_fields=capped,
        asked_field=target_field or "",
    )

    coerced = _coerce_fields(result.fields)
    _attach_display(coerced, asked_options)
    merged = dict(fields)
    merged.update({f.name: f.value for f in coerced})

    # Reconciliation goes HERE — after the merge, before the state machine
    # decides what is still unfilled. Any later and the patient gets asked
    # where the pain is when they already said "back pain".
    derived = reconcile_fields(merged)
    merged.update({f.name: f.value for f in derived})
    coerced = coerced + derived

    session_state = _session_state(merged, follow_up_counts, field_ask_counts)
    actual = sm_next_node(session_state)
    if actual is None:
        return coerced, None

    record_follow_up(session_state, actual.id)

    # Trust the model's question only if it wrote it for the node we actually
    # landed on, it produced one, and the field it is filling is genuinely
    # still open after reconciliation. That last clause is what stops the
    # re-ask: the model chose its target before we derived symptom_site from
    # "back pain", so its question can be asking for something we now have.
    still_open = result.target_field and result.target_field not in merged
    if result.asking_about == actual.id and result.question and still_open:
        record_field_ask(session_state, result.target_field)
        return coerced, _render(
            actual.id,
            result.question,
            result.options,
            result.target_field,
            _is_multi(actual, result.target_field),
            actual.phase_key,
            result.question_en,
        )

    log.info(
        "turn: regenerating question (model asked about %r targeting %r, state "
        "machine says %r, target still open: %s)",
        result.asking_about,
        result.target_field,
        actual.id,
        bool(still_open),
    )
    target_field, question_text, question_en, options = followup.generate_followup(
        actual, merged, language, _llm(), capped_fields=_capped_fields(merged, field_ask_counts)
    )
    record_field_ask(session_state, target_field)
    return coerced, _render(
        actual.id,
        question_text,
        options,
        target_field,
        _is_multi(actual, target_field),
        actual.phase_key,
        question_en,
    )


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
        node = InterviewNode(
            id=node_id,
            phase_key=node_id,
            phase_label=node_id,
            required_fields=(),
            optional_fields=(node_id,),
        )

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


def extract_document(image_bytes: bytes, doc_id: str) -> Optional[DocumentRecord]:
    """Read a photographed prescription or lab report.

    Returns a DocumentRecord, or None when the provider could not be reached
    and the document should stay queued for a retry.

    The except here is deliberately narrow. It used to be `except Exception`,
    which swallowed the TypeError from calling this with the wrong number of
    arguments — so every upload silently produced {} and the console showed a
    patient no prior results at all, with nothing in the logs to say why. A
    programming error must now crash; only a genuine provider failure degrades.
    """
    from ai.adapters.base import LLMAdapterError
    from ai.documents import extract

    try:
        return extract.extract_document(image_bytes, doc_id, _vision())
    except LLMAdapterError as exc:
        # Provider-side: rate limited, unreachable, or unparseable output.
        # Worth retrying later, so leave the document queued.
        _degrade("documents.extract", exc)
        return None

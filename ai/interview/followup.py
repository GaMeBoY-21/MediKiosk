# Owner: Nikki
"""Adaptive follow-up question generation, constrained to the current node's
scope. The LLM only phrases the question here — the state machine already
decided we're still in this node, and only this node's unfilled fields are
ever offered up as something to ask about.

This module deliberately does not return a node_id or node_type: assembling
those into a full InterviewNode / AnswerResponse is the state machine's job,
not this one's.
"""

import logging
from pathlib import Path

from app.schemas import QuestionOption

from ai.adapters.base import LLMAdapter, MalformedOutputError
from ai.interview.nodes import InterviewNode
from ai.knowledge.danger_symptoms import (
    danger_options,
    describe_danger_options,
    english_danger_options,
)

log = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "followup.txt"

MIN_OPTIONS = 2
# Six, not five: the ROS screening question offers five symptoms plus a
# "none" tile. At five, _parse_options silently returned [] for that one
# question, so the interview's only multi-select rendered as an
# unanswerable free-text box.
MAX_OPTIONS = 6


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text()


def _unanswered_fields(
    node: InterviewNode, filled_fields: dict, capped_fields=()
) -> list[str]:
    """This node's fields still worth asking about.

    Capped fields are excluded as well as filled ones. A field the state
    machine has already given up on must never be offered back to the model,
    or the cap buys nothing — the model just asks about it again.
    """
    capped = set(capped_fields or ())
    all_fields = list(node.required_fields) + list(node.optional_fields)
    return [f for f in all_fields if f not in filled_fields and f not in capped]


def describe_filled(filled_fields: dict) -> str:
    """Every field already captured, with its value, one per line.

    Names alone were not enough. The model was told "chief_complaint is
    answered" and asked "where is the pain?" anyway, because nothing in the
    prompt let it see that the answer WAS "back pain". It cannot avoid
    re-asking for something it cannot see.
    """
    if not filled_fields:
        return "(nothing captured yet)"
    lines = []
    for name in sorted(filled_fields):
        value = filled_fields[name]
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(item) for item in value)
        lines.append(f"- {name}: {value}")
    return "\n".join(lines)


# The one field whose options are a safety decision rather than a wording
# choice. For a patient answering by touch these tiles are the only danger
# signs they can report at all.
DANGER_FIELD = "associated_symptoms"


def enforce_danger_options(
    target_field: str,
    filled_fields: dict,
    model_options: list[QuestionOption],
    language: str = "en",
) -> list[QuestionOption]:
    """Rebuild the associated_symptoms options from ai/knowledge/danger_symptoms.

    The model translates; it does not choose. A back-pain patient was offered
    "breathlessness" because the prompt asked the model to work out which
    warning signs went with the complaint, and it worked it out wrongly. Asking
    more firmly would not have fixed that — the list has to come from a table,
    and the model's answer has to be checked against it, which is what this
    does.

    The model's labels are kept where they match a value we asked for (that is
    the translation, the one part it is good at). Anything it invented is
    dropped; anything it omitted comes back from ai/knowledge/danger_symptoms'
    own translation table, in the patient's language — the fallback is used
    exactly when the model misbehaved, and handing a Hindi-only patient a list
    of danger signs in English is the same as not offering them at all.

    The English label is carried through as well. Rebuilding the list here
    discarded whatever `label_en` the model had supplied, which made this the
    one question in the whole interview with no English under its tiles — on
    the screen where a relative or a nurse reading over the patient's shoulder
    is most likely to be the one who spots the warning sign.
    """
    if target_field != DANGER_FIELD:
        return model_options

    translated = {o.value: o.label for o in model_options}
    required = danger_options(filled_fields, language)
    # value -> English label, straight from the table. Not the model's: these
    # are safety strings and the English is ours to state.
    english = dict(english_danger_options(filled_fields))

    invented = sorted(set(translated) - {value for value, _ in required})
    if invented:
        log.warning(
            "discarding model-invented danger symptoms %s; the list is not the "
            "model's to choose",
            invented,
        )
    missing = [value for value, _ in required if value not in translated]
    if missing:
        log.warning(
            "model omitted danger symptoms %s; using our own translations for them",
            missing,
        )

    out = []
    for value, fallback in required:
        label = translated.get(value) or fallback
        label_en = english.get(value)
        out.append(
            QuestionOption(
                value=value,
                label=label,
                # Same rule as every other option: nothing to show twice when
                # the label already IS the English.
                label_en=None if label_en == label else label_en,
            )
        )
    return out


def _bare(target_field: str, node: InterviewNode, filled_fields: dict, language: str):
    """Fallback when the model gave us nothing usable.

    The question comes back empty and the kiosk falls back to the stage label,
    which it already renders in the patient's language. Returning the stage
    label from here instead would put English prose on the screen: the label
    held on the node is English on purpose, for the model's prompt.

    The danger tiles do NOT fall back to nothing: they come from the table
    either way, so a model failure on this one question cannot leave a
    touch-only patient with no way to report a warning sign.

    EVERY early return in generate_followup goes through here, precisely so
    that none of them can skip enforce_danger_options.
    """
    return (
        target_field,
        "",
        None,
        enforce_danger_options(target_field, filled_fields, [], language),
    )


def _parse_options(raw_options) -> list[QuestionOption]:
    if not isinstance(raw_options, list):
        return []
    options: list[QuestionOption] = []
    for item in raw_options:
        if not isinstance(item, dict):
            continue
        value = str(item.get("value", "")).strip()
        label = str(item.get("label", "")).strip()
        if not value or not label:
            continue
        # None, not "", when the model omits it or echoes the same string —
        # the kiosk then renders one line rather than the tile twice.
        label_en = str(item.get("label_en") or "").strip() or None
        options.append(
            QuestionOption(value=value, label=label, label_en=None if label_en == label else label_en)
        )
    return options


def generate_followup(
    node: InterviewNode,
    filled_fields: dict,
    language: str,
    llm: LLMAdapter,
    capped_fields=(),
) -> tuple[str, str, str | None, list[QuestionOption]]:
    """Generate the next follow-up question for the current node.

    Returns (target field, question text, the same question in English, options).

    The target field is what makes touch input work: when a patient taps an
    option instead of speaking, there is no transcript to extract from, so the
    caller stores the tapped value straight into this field. Without it a
    tapped answer has nowhere to go and is silently lost.

    `options` is [] for a genuinely open-ended question — never omitted,
    never None.
    """
    remaining = _unanswered_fields(node, filled_fields, capped_fields)
    if not remaining:
        return _bare("", node, filled_fields, language)

    prompt = _load_prompt_template().format(
        phase_label=node.phase_label,
        node_id=node.id,
        remaining_fields=", ".join(remaining),
        # The WHOLE session's fields, not just this stage's, and with values.
        # A question must not re-ask anything already present in any field.
        already_answered=describe_filled(filled_fields),
        # Resolved from a table before the call, so the model is handed the
        # danger symptoms rather than asked to work out which ones apply.
        danger_symptom_options=describe_danger_options(filled_fields, language),
        language=language,
    )

    try:
        raw = llm.complete_json(prompt)
    except MalformedOutputError:
        return _bare(remaining[0], node, filled_fields, language)

    text = str(raw.get("question", "")).strip()
    if not text:
        return _bare(remaining[0], node, filled_fields, language)

    options = _parse_options(raw.get("options", []))
    if options and not (MIN_OPTIONS <= len(options) <= MAX_OPTIONS):
        log.warning(
            "discarding %d options (outside %d-%d); question falls back to free text",
            len(options), MIN_OPTIONS, MAX_OPTIONS,
        )
        options = []

    target_field = resolve_target_field(raw.get("target_field"), remaining)
    return (
        target_field,
        text,
        english_of(raw.get("question_en"), text),
        enforce_danger_options(target_field, filled_fields, options, language),
    )


def english_of(raw_en, primary: str) -> str | None:
    """The English rendering of a question, or None.

    None whenever there is nothing worth showing twice: the model omitted it,
    or the patient's language IS English so it echoed the same sentence. The
    kiosk then renders a single line.
    """
    english = str(raw_en or "").strip()
    return english or None if english != primary else None


def resolve_target_field(claimed, remaining: list[str]) -> str:
    """Pin the model's claimed target field to one this node is actually missing.

    A tapped option is written straight into whatever field comes back here,
    so a hallucinated or out-of-scope name would silently write clinical data
    under the wrong key. Fall back to the first unanswered field, which is
    what the question is most likely about anyway.
    """
    name = str(claimed or "").strip()
    if name in remaining:
        return name
    return remaining[0] if remaining else ""

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
        options.append(QuestionOption(value=value, label=label))
    return options


def generate_followup(
    node: InterviewNode,
    filled_fields: dict,
    language: str,
    llm: LLMAdapter,
    capped_fields=(),
) -> tuple[str, str, list[QuestionOption]]:
    """Generate the next follow-up question for the current node.

    Returns (target field, question text, tappable options).

    The target field is what makes touch input work: when a patient taps an
    option instead of speaking, there is no transcript to extract from, so the
    caller stores the tapped value straight into this field. Without it a
    tapped answer has nowhere to go and is silently lost.

    `options` is [] for a genuinely open-ended question — never omitted,
    never None.
    """
    remaining = _unanswered_fields(node, filled_fields, capped_fields)
    if not remaining:
        return "", node.phase_label, []

    prompt = _load_prompt_template().format(
        phase_label=node.phase_label,
        node_id=node.id,
        remaining_fields=", ".join(remaining),
        # The WHOLE session's fields, not just this stage's, and with values.
        # A question must not re-ask anything already present in any field.
        already_answered=describe_filled(filled_fields),
        language=language,
    )

    try:
        raw = llm.complete_json(prompt)
    except MalformedOutputError:
        return remaining[0], node.phase_label, []

    text = str(raw.get("question", "")).strip()
    if not text:
        return remaining[0], node.phase_label, []

    options = _parse_options(raw.get("options", []))
    if options and not (MIN_OPTIONS <= len(options) <= MAX_OPTIONS):
        log.warning(
            "discarding %d options (outside %d-%d); question falls back to free text",
            len(options), MIN_OPTIONS, MAX_OPTIONS,
        )
        options = []

    return resolve_target_field(raw.get("target_field"), remaining), text, options


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

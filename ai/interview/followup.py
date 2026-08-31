# Owner: Nikki
"""Adaptive follow-up question generation, constrained to the current node's
scope. The LLM only phrases the question here — the state machine already
decided we're still in this node, and only this node's unfilled fields are
ever offered up as something to ask about.

This module deliberately does not return a node_id or node_type: assembling
those into a full InterviewNode / AnswerResponse is the state machine's job,
not this one's.
"""

from pathlib import Path

from app.schemas import QuestionOption

from ai.adapters.base import LLMAdapter, MalformedOutputError
from ai.interview.nodes import InterviewNode

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "followup.txt"

MIN_OPTIONS = 2
MAX_OPTIONS = 5


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text()


def _unanswered_fields(node: InterviewNode, filled_fields: dict) -> list[str]:
    all_fields = list(node.required_fields) + list(node.optional_fields)
    return [f for f in all_fields if f not in filled_fields]


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
    node: InterviewNode, filled_fields: dict, language: str, llm: LLMAdapter
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
    remaining = _unanswered_fields(node, filled_fields)
    if not remaining:
        return "", node.phase_label, []

    prompt = _load_prompt_template().format(
        phase_label=node.phase_label,
        node_id=node.id,
        remaining_fields=", ".join(remaining),
        already_answered=", ".join(filled_fields.keys()) or "none yet",
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
    if not (MIN_OPTIONS <= len(options) <= MAX_OPTIONS):
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

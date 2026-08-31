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
) -> tuple[str, list[QuestionOption]]:
    """Generate the next follow-up question for the current node.

    Returns (question text, tappable options). `options` is [] for a
    genuinely open-ended question — never omitted, never None.
    """
    remaining = _unanswered_fields(node, filled_fields)
    if not remaining:
        return node.phase_label, []

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
        return node.phase_label, []

    text = str(raw.get("question", "")).strip()
    if not text:
        return node.phase_label, []

    options = _parse_options(raw.get("options", []))
    if not (MIN_OPTIONS <= len(options) <= MAX_OPTIONS):
        options = []

    return text, options

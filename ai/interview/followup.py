# Owner: Nikki
"""Adaptive follow-up question generation, constrained to the current node's
scope. The LLM only phrases the question here — the state machine already
decided we're still in this node, and only this node's unfilled fields are
ever offered up as something to ask about."""

from pathlib import Path

from ai.adapters.base import LLMAdapter, MalformedOutputError
from ai.interview.nodes import InterviewNode
from ai.types import FollowUpQuestion

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "followup.txt"

MIN_OPTIONS = 2
MAX_OPTIONS = 5


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text()


def _unanswered_fields(node: InterviewNode, filled_fields: dict) -> list[str]:
    all_fields = list(node.required_fields) + list(node.optional_fields)
    return [f for f in all_fields if f not in filled_fields]


def generate_followup(
    node: InterviewNode, filled_fields: dict, language: str, llm: LLMAdapter
) -> FollowUpQuestion | None:
    """Generate the next follow-up question for the current node.

    Returns None once every field the node cares about is already filled —
    the state machine should already have moved on by then, so this is a
    fallback rather than the normal path.
    """
    remaining = _unanswered_fields(node, filled_fields)
    if not remaining:
        return None

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
        return FollowUpQuestion(text=node.phase_label, options=[])

    text = str(raw.get("question", "")).strip()
    if not text:
        return FollowUpQuestion(text=node.phase_label, options=[])

    options = raw.get("options", [])
    if not isinstance(options, list):
        options = []
    options = [str(option).strip() for option in options if str(option).strip()]
    if not (MIN_OPTIONS <= len(options) <= MAX_OPTIONS):
        options = []

    return FollowUpQuestion(text=text, options=options)

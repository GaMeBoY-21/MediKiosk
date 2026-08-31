# Owner: Nikki
"""Transcript -> structured field extraction.

The LLM only fills the fields the current interview node declares; it does
not decide what to ask next or what stage the interview is in — that's
ai.interview.state_machine's job. Prompts live in files, not strings.
"""

from pathlib import Path

from app.schemas import ExtractedField, FieldSource

from ai.adapters.base import LLMAdapter, MalformedOutputError
from ai.interview.nodes import InterviewNode

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "extraction.txt"

MIN_CONFIDENCE = 0.5


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text()


def _build_prompt(transcript: str, node: InterviewNode) -> str:
    allowed_fields = list(node.required_fields) + list(node.optional_fields)
    return _load_prompt_template().format(
        transcript=transcript,
        node_id=node.id,
        allowed_fields=", ".join(allowed_fields),
    )


def extract_fields(transcript: str, node: InterviewNode, llm: LLMAdapter) -> list[ExtractedField]:
    """Extract the fields `node` cares about from a patient's spoken answer.

    `transcript` may be in any of the seven supported languages; extracted
    values come back as English clinical terms. Fields the model isn't
    confident about are omitted rather than guessed, so the state machine
    knows to ask again.
    """
    allowed_fields = set(node.required_fields) | set(node.optional_fields)
    if not allowed_fields:
        return []

    prompt = _build_prompt(transcript, node)

    try:
        raw = llm.complete_json(prompt)
    except MalformedOutputError:
        return []

    fields_payload = raw.get("fields", [])
    if not isinstance(fields_payload, list):
        return []

    extracted: list[ExtractedField] = []
    for item in fields_payload:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if name not in allowed_fields:
            continue
        value = item.get("value")
        if value is None or value == "":
            continue
        confidence = item.get("confidence")
        if not isinstance(confidence, (int, float)):
            continue
        if confidence < MIN_CONFIDENCE:
            continue
        extracted.append(
            ExtractedField(
                name=name, value=value, confidence=float(confidence), source=FieldSource.speech
            )
        )
    return extracted


def fields_to_dict(extracted_fields: list[ExtractedField]) -> dict:
    """Collapse a list of ExtractedField into a plain {name: value} dict,
    ready for ai.interview.state_machine.apply_extracted_fields."""
    return {f.name: f.value for f in extracted_fields}

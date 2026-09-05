# Owner: Nikki
"""Transcript -> structured field extraction.

The LLM only fills the fields the current interview node declares; it does
not decide what to ask next or what stage the interview is in — that's
ai.interview.state_machine's job. Prompts live in files, not strings.
"""

from pathlib import Path

from app.schemas import ExtractedField, FieldSource

from ai.adapters.base import LLMAdapter, MalformedOutputError
from ai.interview.nodes import NODES, InterviewNode

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


# Stages that hold no clinical content for an opening narration. Identity and
# consent are collected on the kiosk's own screens, documents has its own
# screen, and confirm is a checkbox — none of them is something a patient
# says while describing what is wrong with them.
_NON_CLINICAL_NODES = frozenset({"identity", "consent", "documents", "confirm"})


def narration_fields() -> set[str]:
    """Every field an opening description is allowed to fill.

    The union across the clinical stages, derived from nodes.py rather than
    listed here, so a field added to a node becomes extractable from a
    narration without anyone remembering to update this.
    """
    allowed: set[str] = set()
    for node_id, node in NODES.items():
        if node_id in _NON_CLINICAL_NODES:
            continue
        allowed |= set(node.required_fields) | set(node.optional_fields)
    return allowed


def extract_narration(transcript: str, llm: LLMAdapter) -> list[ExtractedField]:
    """Extract across ALL clinical stages from one free description.

    The interview normally asks about one stage at a time and extracts within
    that stage's scope. This is the opposite end: the patient has told their
    whole story in one go, and "chest pain for two days, it goes to my left
    arm, worse when I walk" is four fields spread over two stages. Scoping
    that to the current node would throw three of them away and then ask the
    patient about each of them anyway.

    This does NOT give the model control of the flow. It returns fields; the
    state machine reads them and decides what remains unanswered. A model that
    hallucinates a field it was not told still has to pass the allow-list
    below, and a model that returns nothing simply leaves everything to be
    asked, which is the behaviour that existed before.
    """
    allowed = narration_fields()
    if not allowed or not (transcript or "").strip():
        return []

    prompt = _load_prompt_template().format(
        transcript=transcript,
        node_id="opening description (the patient's whole story, unprompted)",
        allowed_fields=", ".join(sorted(allowed)),
    )

    try:
        raw = llm.complete_json(prompt)
    except MalformedOutputError:
        # Unusable narration falls through to the ordinary question flow.
        return []

    return _parse_allowed(raw, allowed)


def _parse_allowed(raw: dict, allowed: set[str]) -> list[ExtractedField]:
    """Shared parsing: allow-list, drop blanks, drop low confidence."""
    payload = raw.get("fields", []) if isinstance(raw, dict) else []
    if not isinstance(payload, list):
        return []

    out: list[ExtractedField] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if name not in allowed:
            continue
        value = item.get("value")
        if value is None or value == "":
            continue
        confidence = item.get("confidence")
        if not isinstance(confidence, (int, float)) or confidence < MIN_CONFIDENCE:
            continue
        out.append(
            ExtractedField(
                name=name, value=value, confidence=float(confidence), source=FieldSource.speech
            )
        )
    return out


def fields_to_dict(extracted_fields: list[ExtractedField]) -> dict:
    """Collapse a list of ExtractedField into a plain {name: value} dict,
    ready for ai.interview.state_machine.apply_extracted_fields."""
    return {f.name: f.value for f in extracted_fields}

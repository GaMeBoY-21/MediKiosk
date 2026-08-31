# Owner: Nikki
"""One interview turn in a single LLM call.

extraction.py and followup.py remain the canonical single-purpose functions —
they are what the tests exercise and what any other caller should use. This
module exists only to save a round trip on the hot path: answering a question
used to cost two serial calls (extract, then phrase the next question), so the
patient paid both latencies and we burned two requests against a small daily
quota.

The state machine still owns the flow. The LLM is handed a branch that has
ALREADY been decided — "if these required fields end up filled, ask about node
X, otherwise stay here" — where node X was computed by
ai.interview.state_machine before the call. Afterwards the caller re-runs the
state machine on the merged fields and, if the model asked about the wrong
node, throws the question away and generates the right one. The model can
therefore never move the interview somewhere the state machine did not sanction;
the worst it can do is waste its own question.
"""

from pathlib import Path

from app.schemas import ExtractedField, FieldSource, QuestionOption

from ai.adapters.base import LLMAdapter, MalformedOutputError
from ai.interview.nodes import InterviewNode

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "turn.txt"

MIN_CONFIDENCE = 0.5
MIN_OPTIONS = 2
MAX_OPTIONS = 5


class TurnResult:
    """What one combined call produced.

    `asking_about` is the node the model believes its question belongs to. The
    caller must check it against the state machine before trusting `question`.
    """

    __slots__ = ("fields", "asking_about", "question", "options")

    def __init__(
        self,
        fields: list[ExtractedField],
        asking_about: str,
        question: str,
        options: list[QuestionOption],
    ):
        self.fields = fields
        self.asking_about = asking_about
        self.question = question
        self.options = options

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        names = [f.name for f in self.fields]
        return (
            f"TurnResult(fields={names}, asking_about={self.asking_about!r}, "
            f"question={self.question!r}, options={len(self.options)})"
        )


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text()


def _parse_fields(raw_fields, allowed: set[str]) -> list[ExtractedField]:
    """Same acceptance rules as extraction.extract_fields: in-scope, non-empty,
    confident enough. Anything else is dropped rather than guessed at."""
    if not isinstance(raw_fields, list):
        return []
    out: list[ExtractedField] = []
    for item in raw_fields:
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


def _parse_options(raw_options) -> list[QuestionOption]:
    if not isinstance(raw_options, list):
        return []
    options: list[QuestionOption] = []
    for item in raw_options:
        if not isinstance(item, dict):
            continue
        value = str(item.get("value", "")).strip()
        label = str(item.get("label", "")).strip()
        if value and label:
            options.append(QuestionOption(value=value, label=label))
    return options if MIN_OPTIONS <= len(options) <= MAX_OPTIONS else []


def run_turn(
    transcript: str,
    node: InterviewNode,
    advance_node: InterviewNode | None,
    filled_fields: dict,
    language: str,
    llm: LLMAdapter,
) -> TurnResult:
    """Extract this answer's fields and phrase the next question, in one call.

    `node` is the stage being answered. `advance_node` is the stage the state
    machine has already determined comes next IF `node`'s required fields all
    end up filled — pass None when there is no next stage, and the model is
    told to stay put.
    """
    allowed = set(node.required_fields) | set(node.optional_fields)

    advance_id = advance_node.id if advance_node else node.id
    advance_fields = (
        ", ".join(list(advance_node.required_fields) + list(advance_node.optional_fields))
        if advance_node
        else "(no further stage — stay in the current one)"
    )

    prompt = _load_prompt_template().format(
        transcript=transcript,
        node_id=node.id,
        allowed_fields=", ".join(sorted(allowed)) or "(none)",
        required_fields=", ".join(node.required_fields) or "(none)",
        already_answered=", ".join(sorted(filled_fields)) or "none yet",
        advance_node_id=advance_id,
        advance_fields=advance_fields,
        language=language,
    )

    try:
        raw = llm.complete_json(prompt)
    except MalformedOutputError:
        # Nothing trustworthy came back. Report no fields and no question; the
        # caller falls back to generating a question the normal way rather
        # than inventing clinical data.
        return TurnResult([], node.id, "", [])

    return TurnResult(
        fields=_parse_fields(raw.get("fields"), allowed),
        asking_about=str(raw.get("asking_about", node.id)).strip() or node.id,
        question=str(raw.get("question", "")).strip(),
        options=_parse_options(raw.get("options")),
    )

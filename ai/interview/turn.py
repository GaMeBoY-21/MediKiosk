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

import logging
from pathlib import Path

from app.schemas import ExtractedField, FieldSource, QuestionOption

from ai.adapters.base import LLMAdapter, MalformedOutputError
from ai.interview.followup import (
    describe_filled,
    english_of,
    enforce_danger_options,
    resolve_target_field,
)
from ai.interview.nodes import InterviewNode
from ai.interview.reconcile import derive_fields
from ai.knowledge.danger_symptoms import describe_danger_options

log = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "turn.txt"

MIN_CONFIDENCE = 0.5
MIN_OPTIONS = 2
# Six, not five: the ROS screening question offers five symptoms plus a
# "none" tile. At five, _parse_options silently returned [] for that one
# question, so the interview's only multi-select rendered as an
# unanswerable free-text box.
MAX_OPTIONS = 6


class TurnResult:
    """What one combined call produced.

    `asking_about` is the node the model believes its question belongs to. The
    caller must check it against the state machine before trusting `question`.
    """

    __slots__ = ("fields", "asking_about", "target_field", "question", "question_en", "options")

    def __init__(
        self,
        fields: list[ExtractedField],
        asking_about: str,
        question: str,
        options: list[QuestionOption],
        target_field: str = "",
        question_en: str | None = None,
    ):
        self.fields = fields
        self.asking_about = asking_about
        self.target_field = target_field
        self.question = question
        self.question_en = question_en
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
            label_en = str(item.get("label_en") or "").strip() or None
            options.append(
                QuestionOption(
                    value=value, label=label, label_en=None if label_en == label else label_en
                )
            )
    if options and not (MIN_OPTIONS <= len(options) <= MAX_OPTIONS):
        # Say so. Silently returning [] here turned a tappable question into a
        # free-text box that a patient who cannot type has no way to answer.
        log.warning(
            "discarding %d options (outside %d-%d); question falls back to free text",
            len(options),
            MIN_OPTIONS,
            MAX_OPTIONS,
        )
        return []
    return options


def run_turn(
    transcript: str,
    node: InterviewNode,
    advance_node: InterviewNode | None,
    filled_fields: dict,
    language: str,
    llm: LLMAdapter,
    capped_fields=(),
    asked_field: str = "",
) -> TurnResult:
    """Extract this answer's fields and phrase the next question, in one call.

    `node` is the stage being answered. `advance_node` is the stage the state
    machine has already determined comes next IF `node`'s required fields all
    end up filled — pass None when there is no next stage, and the model is
    told to stay put.

    `asked_field` is the field the question the patient just answered was
    trying to fill. We recorded it when we generated that question, so there is
    no reason to make the model guess: without it the model had the transcript
    and a list of nine fields and no idea which one the patient was replying
    to, and an answer filed under the wrong field leaves the right one empty —
    which is another question the patient gets asked twice.
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
        # Names AND values, for every stage — not just this one's keys. The
        # model cannot avoid re-asking for something it cannot see the answer to.
        already_answered=describe_filled(filled_fields),
        asked_field=asked_field or "(not recorded — infer it from the question)",
        advance_node_id=advance_id,
        advance_fields=advance_fields,
        # Resolved from a table before the call. The model is handed this
        # patient's danger symptoms, not asked to work out which ones apply.
        danger_symptom_options=describe_danger_options(filled_fields, language),
        language=language,
    )

    try:
        raw = llm.complete_json(prompt)
    except MalformedOutputError:
        # Nothing trustworthy came back. Report no fields and no question; the
        # caller falls back to generating a question the normal way rather
        # than inventing clinical data.
        return TurnResult([], node.id, "", [])

    asking_about = str(raw.get("asking_about", node.id)).strip() or node.id
    fields = _parse_fields(raw.get("fields"), allowed)

    # The target field must belong to whichever node the question is for,
    # and must not already be answered — a tapped option is written straight
    # into it, so a wrong name silently files clinical data under the wrong
    # key.
    scope = advance_node if (advance_node and asking_about == advance_node.id) else node
    answered = dict(filled_fields)
    answered.update({f.name: f.value for f in fields})
    # Reconcile before working out what is left. The model has just folded the
    # site into chief_complaint; without this line symptom_site still looks
    # unanswered here and the question we are about to keep is "where is the
    # pain?" — to a patient who said "back pain" one sentence ago.
    answered.update(derive_fields(answered))
    capped = set(capped_fields or ())
    remaining = [
        f
        for f in list(scope.required_fields) + list(scope.optional_fields)
        if f not in answered and f not in capped
    ]

    target_field = resolve_target_field(raw.get("target_field"), remaining)
    question = str(raw.get("question", "")).strip()
    return TurnResult(
        fields=fields,
        asking_about=asking_about,
        target_field=target_field,
        question=question,
        question_en=english_of(raw.get("question_en"), question),
        # Safety content is not the model's to choose. Checked against
        # ai/knowledge/danger_symptoms.py using the reconciled field set, so
        # the list matches the complaint we have actually landed on.
        options=enforce_danger_options(
            target_field, answered, _parse_options(raw.get("options")), language
        ),
    )

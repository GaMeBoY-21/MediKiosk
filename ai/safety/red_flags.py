# Owner: Nikki
"""Deterministic red-flag rules. No LLM calls anywhere in this module.

Tharun calls evaluate() synchronously after every extracted answer, so this
has to stay fast (sub-millisecond) and dependency-free: pure Python string
matching over already-extracted fields, no network, no LLM.
"""

from dataclasses import dataclass
from typing import Callable

from ai.types import RedFlag

# The only fields this module reads. Free-text or list-of-string fields that
# extraction may have filled with the patient's symptoms.
_SYMPTOM_FIELDS = (
    "chief_complaint",
    "symptom_site",
    "symptom_radiation",
    "associated_symptoms",
    "ros_cardiovascular",
    "ros_respiratory",
    "ros_neurological",
    "ros_gastrointestinal",
    "ros_genitourinary",
    "ros_musculoskeletal",
    "ros_dermatological",
    "ros_general",
)

_CHEST_PAIN = ("chest pain", "pain in chest", "chest discomfort", "chest tightness")
_BREATHLESSNESS = ("breathless", "shortness of breath", "difficulty breathing", "cant breathe", "can't breathe")
_ARM_JAW_RADIATION = ("left arm", "right arm", "to the arm", "jaw", "radiat")
_FACIAL_DROOP = ("facial droop", "face droop", "drooping face", "one side of the face", "one side of face")
_ARM_WEAKNESS = ("arm weakness", "weakness in the arm", "one sided weakness", "one-sided weakness", "cannot lift", "can't lift")
_SLURRED_SPEECH = ("slurred speech", "slurring", "difficulty speaking clearly")
_ALTERED_CONSCIOUSNESS = ("altered consciousness", "unconscious", "unresponsive", "confused", "disoriented", "drowsy", "not responding")
_ACTIVE_BLEEDING = ("active bleeding", "heavy bleeding", "bleeding heavily", "profuse bleeding", "won't stop bleeding", "wont stop bleeding")
_AT_REST = ("at rest", "even at rest", "while resting", "without exertion")
_SEVERE = ("severe",)
_SUICIDAL = ("suicidal", "want to die", "end my life", "kill myself", "no reason to live", "harm myself")
_HIGH_FEVER = ("high fever", "high temperature", "very high fever")
_NECK_STIFFNESS = ("neck stiffness", "stiff neck")
_PREGNANT = ("pregnant", "pregnancy")
_BLEEDING = ("bleeding",)
_SEVERE_ABDOMINAL_PAIN = ("severe abdominal pain", "severe stomach pain", "severe belly pain")


def _text_blob(fields: dict) -> str:
    """Flatten every symptom-bearing field into one lowercase string for
    substring matching."""
    parts = []
    for key in _SYMPTOM_FIELDS:
        value = fields.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, (list, tuple)):
            parts.extend(str(item) for item in value)
    return " ".join(parts).lower()


def _has_any(blob: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in blob for phrase in phrases)


def _rule_chest_pain_breathlessness(fields: dict) -> bool:
    blob = _text_blob(fields)
    return _has_any(blob, _CHEST_PAIN) and _has_any(blob, _BREATHLESSNESS)


def _rule_chest_pain_radiation(fields: dict) -> bool:
    blob = _text_blob(fields)
    return _has_any(blob, _CHEST_PAIN) and _has_any(blob, _ARM_JAW_RADIATION)


def _rule_fast_stroke_signs(fields: dict) -> bool:
    blob = _text_blob(fields)
    return _has_any(blob, _FACIAL_DROOP) or _has_any(blob, _ARM_WEAKNESS) or _has_any(blob, _SLURRED_SPEECH)


def _rule_altered_consciousness(fields: dict) -> bool:
    if fields.get("altered_consciousness"):
        return True
    return _has_any(_text_blob(fields), _ALTERED_CONSCIOUSNESS)


def _rule_active_bleeding(fields: dict) -> bool:
    return _has_any(_text_blob(fields), _ACTIVE_BLEEDING)


def _rule_severe_breathlessness_at_rest(fields: dict) -> bool:
    blob = _text_blob(fields)
    return _has_any(blob, _BREATHLESSNESS) and _has_any(blob, _AT_REST) and _has_any(blob, _SEVERE)


def _rule_suicidal_ideation(fields: dict) -> bool:
    if fields.get("suicidal_ideation"):
        return True
    return _has_any(_text_blob(fields), _SUICIDAL)


def _rule_high_fever_neck_stiffness(fields: dict) -> bool:
    blob = _text_blob(fields)
    return _has_any(blob, _HIGH_FEVER) and _has_any(blob, _NECK_STIFFNESS)


def _rule_pregnancy_complication(fields: dict) -> bool:
    blob = _text_blob(fields)
    is_pregnant = bool(fields.get("is_pregnant")) or _has_any(blob, _PREGNANT)
    if not is_pregnant:
        return False
    return _has_any(blob, _BLEEDING) or _has_any(blob, _SEVERE_ABDOMINAL_PAIN)


@dataclass(frozen=True)
class RedFlagRule:
    rule_id: str
    label: str
    severity: str  # "critical" | "urgent"
    match: Callable[[dict], bool]


RED_FLAG_RULES: tuple[RedFlagRule, ...] = (
    RedFlagRule("chest_pain_breathlessness", "Chest pain with breathlessness", "critical", _rule_chest_pain_breathlessness),
    RedFlagRule("chest_pain_radiation", "Chest pain radiating to arm or jaw", "critical", _rule_chest_pain_radiation),
    RedFlagRule("fast_stroke_signs", "Possible stroke signs (face, arm, or speech)", "critical", _rule_fast_stroke_signs),
    RedFlagRule("altered_consciousness", "Altered consciousness", "critical", _rule_altered_consciousness),
    RedFlagRule("active_bleeding", "Active bleeding", "critical", _rule_active_bleeding),
    RedFlagRule("severe_breathlessness_at_rest", "Severe breathlessness at rest", "critical", _rule_severe_breathlessness_at_rest),
    RedFlagRule("suicidal_ideation", "Suicidal ideation", "critical", _rule_suicidal_ideation),
    RedFlagRule("high_fever_neck_stiffness", "High fever with neck stiffness", "urgent", _rule_high_fever_neck_stiffness),
    RedFlagRule("pregnancy_complication", "Pregnancy with bleeding or severe abdominal pain", "critical", _rule_pregnancy_complication),
)


def evaluate(fields: dict) -> list[RedFlag]:
    """Check extracted fields against every red-flag rule.

    Pure Python, no network access, no LLM call. Safe to call synchronously
    after every answer.
    """
    return [
        RedFlag(rule_id=rule.rule_id, label=rule.label, severity=rule.severity)
        for rule in RED_FLAG_RULES
        if rule.match(fields)
    ]

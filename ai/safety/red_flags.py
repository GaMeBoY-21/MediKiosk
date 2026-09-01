# Owner: Nikki
"""Deterministic red-flag rules. No LLM calls anywhere in this module.

Tharun calls evaluate() synchronously after every extracted answer, so this
has to stay fast (sub-millisecond) and dependency-free: pure Python string
matching over already-extracted fields, no network, no LLM.
"""

from dataclasses import dataclass
from typing import Callable

from app.schemas import FlagSeverity, RedFlag

# The only fields this module reads. Free-text or list-of-string fields that
# extraction may have filled with the patient's symptoms.
_SYMPTOM_FIELDS = (
    "chief_complaint",
    "symptom_site",
    "symptom_radiation",
    "associated_symptoms",
    # The one general screening question. It is a symptom-bearing field and was
    # simply missing from this list, so nothing a patient reported there was
    # ever checked against a rule.
    "ros_screen",
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

# Cauda equina: back pain with bladder/bowel loss or leg weakness. A surgical
# emergency with a window measured in hours, and the OPD queue is not it.
_BACK_COMPLAINT = ("back pain", "backache", "back ache", "lower back", "low back", "spine")
_BLADDER_BOWEL_LOSS = (
    "loss of bladder", "loss of bowel", "bladder or bowel", "incontinence",
    "cannot control urine", "loss of control of urine",
)
_LEG_WEAKNESS = ("leg weakness", "weakness in the legs", "weakness in legs", "legs give way")
_VOMITING_BLOOD = ("vomiting blood", "vomited blood", "blood in vomit", "haematemesis", "hematemesis")
_COUGHING_BLOOD = ("coughing blood", "cough with blood", "blood in sputum", "haemoptysis", "hemoptysis")


def _text_blob(fields: dict) -> str:
    """Flatten every symptom-bearing field into one lowercase string for
    substring matching.

    Underscores become spaces. Values reaching here are not all prose any more:
    a tapped option stores a canonical token like "loss_of_bladder_or_bowel_
    control", and every phrase in this module is written with spaces. Without
    this one replace, a danger sign the patient tapped matches nothing at all —
    which is the whole failure mode the touch path exists to avoid.
    """
    parts = []
    for key in _SYMPTOM_FIELDS:
        value = fields.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, (list, tuple)):
            parts.extend(str(item) for item in value)
    return " ".join(parts).lower().replace("_", " ")


def _has_any(blob: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in blob for phrase in phrases)


def _norm(value) -> str:
    """One field's value, lowercased with underscores opened out.

    Used where a whole-value comparison is wanted rather than a substring scan
    of the blob: symptom_site == "back" must not be satisfied by the word
    "back" turning up inside some other answer.
    """
    if isinstance(value, (list, tuple)):
        return " ".join(str(item) for item in value).lower().replace("_", " ").strip()
    return str(value or "").lower().replace("_", " ").strip()


def _is_chest_complaint(fields: dict) -> bool:
    """The patient's problem is in their chest.

    Phrase matching alone was not enough. A patient who taps the "Chest" tile
    stores chief_complaint="chest" and symptom_site="chest" — canonical tokens,
    no prose — and every phrase here is written as "chest pain". So a patient
    who tapped Chest and then tapped Breathlessness raised NO red flag at all,
    which is the single most important pair of taps this kiosk can receive.

    Only a stated chest site counts. ai/knowledge/body_regions.py deliberately
    derives no site from "breathlessness" or "cough", so a purely respiratory
    complaint cannot arrive here looking like a chest-pain one.
    """
    blob = _text_blob(fields)
    if _has_any(blob, _CHEST_PAIN):
        return True
    return "chest" in (_norm(fields.get("symptom_site")), _norm(fields.get("chief_complaint")))


def _rule_chest_pain_breathlessness(fields: dict) -> bool:
    return _is_chest_complaint(fields) and _has_any(_text_blob(fields), _BREATHLESSNESS)


def _rule_chest_pain_radiation(fields: dict) -> bool:
    return _is_chest_complaint(fields) and _has_any(_text_blob(fields), _ARM_JAW_RADIATION)


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


def _rule_cauda_equina(fields: dict) -> bool:
    blob = _text_blob(fields)
    is_back = _has_any(blob, _BACK_COMPLAINT) or _norm(fields.get("symptom_site")) == "back"
    if not is_back:
        return False
    return _has_any(blob, _BLADDER_BOWEL_LOSS) or _has_any(blob, _LEG_WEAKNESS)


def _rule_vomiting_blood(fields: dict) -> bool:
    return _has_any(_text_blob(fields), _VOMITING_BLOOD)


def _rule_coughing_blood(fields: dict) -> bool:
    return _has_any(_text_blob(fields), _COUGHING_BLOOD)


@dataclass(frozen=True)
class RedFlagRule:
    rule_id: str
    label: str
    severity: FlagSeverity
    match: Callable[[dict], bool]


RED_FLAG_RULES: tuple[RedFlagRule, ...] = (
    RedFlagRule("chest_pain_breathlessness", "Chest pain with breathlessness", FlagSeverity.critical, _rule_chest_pain_breathlessness),
    RedFlagRule("chest_pain_radiation", "Chest pain radiating to arm or jaw", FlagSeverity.critical, _rule_chest_pain_radiation),
    RedFlagRule("fast_stroke_signs", "Possible stroke signs (face, arm, or speech)", FlagSeverity.critical, _rule_fast_stroke_signs),
    RedFlagRule("altered_consciousness", "Altered consciousness", FlagSeverity.critical, _rule_altered_consciousness),
    RedFlagRule("active_bleeding", "Active bleeding", FlagSeverity.critical, _rule_active_bleeding),
    RedFlagRule("severe_breathlessness_at_rest", "Severe breathlessness at rest", FlagSeverity.critical, _rule_severe_breathlessness_at_rest),
    RedFlagRule("suicidal_ideation", "Suicidal ideation", FlagSeverity.critical, _rule_suicidal_ideation),
    RedFlagRule("high_fever_neck_stiffness", "High fever with neck stiffness", FlagSeverity.high, _rule_high_fever_neck_stiffness),
    RedFlagRule("pregnancy_complication", "Pregnancy with bleeding or severe abdominal pain", FlagSeverity.critical, _rule_pregnancy_complication),
    # Added alongside ai/knowledge/danger_symptoms.py. That table now puts
    # these signs in front of back-pain, abdominal-pain and breathlessness
    # patients as tappable tiles; offering a danger sign that fires no rule is
    # the same silent success this codebase has been bitten by repeatedly — the
    # patient reports it, the record shows it, and nothing happens.
    RedFlagRule("cauda_equina", "Back pain with leg weakness or loss of bladder or bowel control", FlagSeverity.critical, _rule_cauda_equina),
    RedFlagRule("vomiting_blood", "Vomiting blood", FlagSeverity.critical, _rule_vomiting_blood),
    RedFlagRule("coughing_blood", "Coughing blood", FlagSeverity.high, _rule_coughing_blood),
)


def evaluate(fields: dict) -> list[RedFlag]:
    """Check extracted fields against every red-flag rule.

    Pure Python, no network access, no LLM call. Safe to call synchronously
    after every answer.
    """
    return [
        RedFlag(rule_id=rule.rule_id, label=rule.label, severity=rule.severity, triggered_by=[])
        for rule in RED_FLAG_RULES
        if rule.match(fields)
    ]

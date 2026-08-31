# Owner: Nikki
"""Interview state machine node definitions — the clinical scaffold as data.

The LLM never decides what stage of the interview we're in or how long it
runs; this module is the deterministic source of truth for that.
ai/interview/state_machine.py reads it to decide transitions.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class InterviewNode:
    id: str
    phase_label: str  # patient-facing string Tharun sends to the frontend
    required_fields: tuple[str, ...]  # must all be filled for the node to end
    optional_fields: tuple[str, ...] = ()  # may be filled but don't gate progress
    repeats: bool = False  # e.g. ROS loops over several sub-systems
    max_follow_ups: int = 3  # safety valve: end the node here even if unfilled


NODES: dict[str, InterviewNode] = {
    "identity": InterviewNode(
        id="identity",
        phase_label="Let's start with a few basic details.",
        required_fields=("patient_name", "age", "sex"),
        max_follow_ups=4,
    ),
    "consent": InterviewNode(
        id="consent",
        phase_label="Before we begin, we need your consent.",
        required_fields=("consent_given",),
        max_follow_ups=2,
    ),
    "chief_complaint": InterviewNode(
        id="chief_complaint",
        phase_label="What brings you in today?",
        required_fields=("chief_complaint", "symptom_duration"),
        max_follow_ups=3,
    ),
    "hpi": InterviewNode(
        id="hpi",
        phase_label="Tell me more about this problem.",
        required_fields=(
            "symptom_site",
            "symptom_onset",
            "symptom_character",
            "symptom_severity",
            # Required, not optional. Optional fields are never asked once the
            # required ones are filled, so as an optional field this was never
            # put to the patient at all — and it is the single field the
            # red-flag rules lean on hardest (breathlessness with chest pain,
            # bleeding in pregnancy). A patient who volunteered it in free
            # speech got a safety check; a patient answering by touch never
            # could. Asking it always is also just a correct history.
            "associated_symptoms",
        ),
        optional_fields=(
            "symptom_radiation",
            "symptom_timing",
            "symptom_exacerbating_factors",
            "symptom_relieving_factors",
        ),
        max_follow_ups=8,
    ),
    "ros": InterviewNode(
        id="ros",
        phase_label="A few quick questions about how you've been feeling overall.",
        required_fields=(),
        optional_fields=(
            "ros_cardiovascular",
            "ros_respiratory",
            "ros_gastrointestinal",
            "ros_neurological",
            "ros_genitourinary",
            "ros_musculoskeletal",
            "ros_dermatological",
            "ros_general",
        ),
        repeats=True,
        max_follow_ups=8,
    ),
    "past_medical": InterviewNode(
        id="past_medical",
        phase_label="Do you have any ongoing health conditions or past surgeries?",
        required_fields=("past_medical_conditions", "past_surgeries"),
        max_follow_ups=4,
    ),
    "drug_allergy": InterviewNode(
        id="drug_allergy",
        phase_label="Are you taking any medicines, and do you have any allergies?",
        required_fields=("current_medications", "known_allergies"),
        max_follow_ups=3,
    ),
    "family": InterviewNode(
        id="family",
        phase_label="Does anyone in your immediate family have a serious illness?",
        required_fields=("family_history",),
        max_follow_ups=3,
    ),
    "personal": InterviewNode(
        id="personal",
        phase_label="A few lifestyle questions.",
        required_fields=("smoking_status", "alcohol_use"),
        optional_fields=("diet", "occupation", "sleep_pattern"),
        max_follow_ups=4,
    ),
    "documents": InterviewNode(
        id="documents",
        phase_label="Do you have any prior prescriptions or lab reports to show us?",
        required_fields=(),
        optional_fields=("uploaded_documents",),
        max_follow_ups=1,
    ),
    "confirm": InterviewNode(
        id="confirm",
        phase_label="Please review your answers before we finish.",
        required_fields=("patient_confirmed",),
        max_follow_ups=1,
    ),
}

NODE_ORDER: tuple[str, ...] = (
    "identity",
    "consent",
    "chief_complaint",
    "hpi",
    "ros",
    "past_medical",
    "drug_allergy",
    "family",
    "personal",
    "documents",
    "confirm",
)


def get_node(node_id: str) -> InterviewNode:
    """Fetch the definition for an interview node."""
    try:
        return NODES[node_id]
    except KeyError:
        raise KeyError(f"unknown interview node: {node_id!r}") from None

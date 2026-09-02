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
    # The key the kiosk resolves against i18n/strings.js to render the stage
    # label in the patient's language. NOT a sentence: a phase label is static
    # UI chrome, so it belongs with the other static strings rather than in a
    # clinical file, and shipping English prose from here is what put
    # "Tell me more about this problem." above a Telugu question.
    phase_key: str
    # English, and deliberately so — this one is never shown to a patient. It
    # goes into the follow-up prompt as context for the model, which reads
    # English. Keep the two apart: translating this would degrade the prompt,
    # and rendering it would leak English onto the screen.
    phase_label: str
    required_fields: tuple[str, ...]  # must all be filled for the node to end
    optional_fields: tuple[str, ...] = ()  # may be filled but don't gate progress
    repeats: bool = False  # e.g. ROS loops over several sub-systems
    max_follow_ups: int = 3  # safety valve: end the node here even if unfilled
    # Fields answered by picking several options at once rather than one.
    multi_select_fields: tuple[str, ...] = ()


NODES: dict[str, InterviewNode] = {
    "identity": InterviewNode(
        id="identity",
        phase_key="identity",
        phase_label="Let's start with a few basic details.",
        required_fields=("patient_name", "age", "sex"),
        max_follow_ups=4,
    ),
    "consent": InterviewNode(
        id="consent",
        phase_key="consent",
        phase_label="Before we begin, we need your consent.",
        required_fields=("consent_given",),
        max_follow_ups=2,
    ),
    "chief_complaint": InterviewNode(
        id="chief_complaint",
        phase_key="chief_complaint",
        phase_label="What brings you in today?",
        required_fields=("chief_complaint", "symptom_duration"),
        max_follow_ups=3,
    ),
    "hpi": InterviewNode(
        id="hpi",
        phase_key="hpi",
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
        phase_key="ros",
        phase_label="One quick question about how you've been feeling overall.",
        # ONE screening question, asked once. A full system-by-system review is
        # twenty questions nobody standing in an OPD queue will sit through,
        # and the physician re-does it properly in the consultation anyway.
        # This exists to catch the constitutional symptoms worth flagging
        # before that conversation starts.
        #
        # It previously declared no required fields at all, which made
        # all(()) True and skipped the entire stage for every patient.
        required_fields=("ros_screen",),
        multi_select_fields=("ros_screen",),
        repeats=False,
        max_follow_ups=1,
    ),
    "past_medical": InterviewNode(
        id="past_medical",
        phase_key="past_medical",
        phase_label="Do you have any ongoing health conditions or past surgeries?",
        required_fields=("past_medical_conditions", "past_surgeries"),
        max_follow_ups=4,
    ),
    "drug_allergy": InterviewNode(
        id="drug_allergy",
        phase_key="drug_allergy",
        phase_label="Are you taking any medicines, and do you have any allergies?",
        required_fields=("current_medications", "known_allergies"),
        max_follow_ups=3,
    ),
    "family": InterviewNode(
        id="family",
        phase_key="family",
        phase_label="Does anyone in your immediate family have a serious illness?",
        required_fields=("family_history",),
        max_follow_ups=3,
    ),
    "personal": InterviewNode(
        id="personal",
        phase_key="personal",
        phase_label="A few lifestyle questions.",
        required_fields=("smoking_status", "alcohol_use"),
        optional_fields=("diet", "occupation", "sleep_pattern"),
        max_follow_ups=4,
    ),
    "documents": InterviewNode(
        id="documents",
        phase_key="documents",
        phase_label="Do you have any prior prescriptions or lab reports to show us?",
        # Also had no required fields, so this stage was skipped too and the
        # patient was never asked whether they brought anything. Asking is the
        # whole point — the upload screen is offered on the back of the answer.
        required_fields=("documents_offered",),
        optional_fields=("uploaded_documents",),
        max_follow_ups=1,
    ),
    "confirm": InterviewNode(
        id="confirm",
        phase_key="confirm",
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


class InvalidNodeGraph(Exception):
    """A node definition that cannot behave the way the state machine assumes."""


def validate_nodes() -> None:
    """Fail at import time on a node graph that cannot work.

    A node with no required fields satisfies itself instantly, because
    all(()) is True — the state machine skips straight past it and the stage
    silently never happens. Both `ros` and `documents` shipped that way, so no
    patient was ever asked either set of questions and nothing anywhere said
    so.

    That is the fifth silent success on this project (after check_red_flags
    resolving to a name that did not exist, extract_document being called with
    the wrong arity, drug names never matching the lookup table, and
    haemoglobin never matching a reference range). Every one of them looked
    like working code and produced a plausible empty result. This check makes
    that specific shape impossible to reintroduce: it runs on import, so a bad
    node graph stops the process at startup instead of quietly shortening
    every interview.
    """
    problems: list[str] = []

    for node_id, node in NODES.items():
        if not node.required_fields:
            problems.append(
                f"{node_id!r} declares no required fields, so all(()) is True and the "
                f"stage would be skipped for every patient. Give it at least one "
                f"required field, or remove it from NODE_ORDER."
            )
        if node.max_follow_ups < 1:
            problems.append(f"{node_id!r} has max_follow_ups={node.max_follow_ups}; it can never be asked.")
        overlap = set(node.required_fields) & set(node.optional_fields)
        if overlap:
            problems.append(f"{node_id!r} lists {sorted(overlap)} as both required and optional.")
        stray = set(node.multi_select_fields) - set(node.required_fields) - set(node.optional_fields)
        if stray:
            problems.append(f"{node_id!r} marks {sorted(stray)} multi-select but does not declare them.")

    missing = set(NODE_ORDER) - set(NODES)
    if missing:
        problems.append(f"NODE_ORDER names nodes that do not exist: {sorted(missing)}")
    unreachable = set(NODES) - set(NODE_ORDER)
    if unreachable:
        problems.append(f"nodes defined but never reachable from NODE_ORDER: {sorted(unreachable)}")

    if problems:
        raise InvalidNodeGraph(
            "invalid interview node graph:\n  - " + "\n  - ".join(problems)
        )


validate_nodes()

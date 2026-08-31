# Owner: Nikki
"""Clinical summary generation.

English for the physician, in standard clinical order. Never diagnoses,
never recommends treatment — this assembles a history, not an opinion.
"""

from pathlib import Path

from app.schemas import ClinicalSummary, DocumentRecord, ExtractedField

from ai.adapters.base import LLMAdapter, MalformedOutputError

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "summary.txt"

LOW_CONFIDENCE_THRESHOLD = 0.65

# The section keys the summary prompt must produce, in clinical order.
# chief_complaint and hpi_narrative land on ClinicalSummary's own top-level
# fields; the rest land in ClinicalSummary.sections under these same keys.
# Matches app.fhir.SECTION_CODES and app.schemas.FlatSummary exactly — keep
# all three in sync if the section list ever changes.
SUMMARY_SECTIONS: tuple[str, ...] = (
    "chief_complaint",
    "hpi_narrative",
    "past_history",
    "drugs_allergies",
    "family",
    "personal",
    "ros",
)

_TOP_LEVEL_SECTIONS = ("chief_complaint", "hpi_narrative")


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text()


# The six ROS screening options, mapped to how a physician would read them.
# Keys are the canonical English values the option tiles carry.
ROS_SCREEN_LABELS: dict[str, str] = {
    "fever": "fever",
    "weight_loss": "weight loss",
    "appetite_change": "change in appetite",
    "sleep_problems": "disturbed sleep",
    "bowel_or_urine_change": "change in bowel or urinary habit",
    "none": "none",
}


def _ros_narrative(value) -> str:
    """Turn the ros_screen selections into one clinical sentence.

    Accepts a list (multi-select) or a single string, since a patient who
    speaks the answer produces one and a patient who taps produces the other.
    """
    if value in (None, "", []):
        return ""
    picked = value if isinstance(value, (list, tuple)) else [value]
    names = [str(v).strip().lower().replace(" ", "_") for v in picked if str(v).strip()]
    if not names:
        return ""

    if names == ["none"]:
        return "Screening review of systems: no fever, weight loss, appetite, sleep or bowel/urinary change reported."

    positives = [ROS_SCREEN_LABELS.get(n, n.replace("_", " ")) for n in names if n != "none"]
    if not positives:
        return ""
    return "Screening review of systems positive for: " + ", ".join(positives) + "."


def _low_confidence_field_names(extracted_fields: list[ExtractedField]) -> list[str]:
    return [f.name for f in extracted_fields if f.confidence < LOW_CONFIDENCE_THRESHOLD]


def generate_summary(
    extracted_fields: list[ExtractedField],
    document_timeline: list[DocumentRecord],
    llm: LLMAdapter,
) -> ClinicalSummary:
    """Generate a physician-readable clinical summary.

    `extracted_fields` is the session's cumulative extracted fields, each
    carrying its own confidence; fields below LOW_CONFIDENCE_THRESHOLD are
    named in low_confidence_fields rather than hedged inside the prose.
    `document_timeline` is structured data already assembled by
    ai.documents.extract — passed straight through, never rewritten by the
    LLM as prose.
    """
    fields = {f.name: f.value for f in extracted_fields}
    prompt = _load_prompt_template().format(fields=fields, document_timeline=document_timeline)

    try:
        raw = llm.complete_json(prompt)
    except MalformedOutputError:
        raw = {}

    sections = {key: str(raw.get(key, "")) for key in SUMMARY_SECTIONS if key not in _TOP_LEVEL_SECTIONS}

    ros_line = _ros_narrative(fields.get("ros_screen"))
    if ros_line:
        # Written deterministically from what the patient actually selected,
        # rather than left to the model to remember. The ROS heading used to
        # render empty on the console for every patient, because the stage was
        # skipped entirely; now that it is asked, the answer must actually
        # arrive.
        sections["ros"] = ros_line

    return ClinicalSummary(
        chief_complaint=str(raw.get("chief_complaint", "")).strip() or None,
        hpi_narrative=str(raw.get("hpi_narrative", "")).strip() or None,
        sections=sections,
        document_timeline=document_timeline,
        low_confidence_fields=_low_confidence_field_names(extracted_fields),
    )

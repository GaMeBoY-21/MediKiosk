# Owner: Nikki
"""Clinical summary generation.

English for the physician, in standard clinical order. Never diagnoses,
never recommends treatment — this assembles a history, not an opinion.
"""

from pathlib import Path

from ai.adapters.base import LLMAdapter, MalformedOutputError
from ai.types import ClinicalSummary

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "summary.txt"

LOW_CONFIDENCE_THRESHOLD = 0.65


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text()


def _low_confidence_fields(fields: dict, confidences: dict) -> list[str]:
    return [name for name in fields if confidences.get(name, 1.0) < LOW_CONFIDENCE_THRESHOLD]


def generate_summary(
    fields: dict, confidences: dict, document_timeline: list[dict], llm: LLMAdapter
) -> ClinicalSummary:
    """Generate a physician-readable clinical summary from a session's
    cumulative extracted fields and document timeline.

    `confidences` maps field name -> confidence score; fields below
    LOW_CONFIDENCE_THRESHOLD are flagged rather than asserted as fact.
    `document_timeline` is prior investigations/prescriptions pulled from
    ai.documents.extract, already ordered chronologically.
    """
    prompt = _load_prompt_template().format(fields=fields, document_timeline=document_timeline)

    try:
        raw = llm.complete_json(prompt)
    except MalformedOutputError:
        raw = {}

    return ClinicalSummary(
        chief_complaint=raw.get("chief_complaint", ""),
        hpi_narrative=raw.get("hpi_narrative", ""),
        past_medical_surgical=raw.get("past_medical_surgical", ""),
        drugs_and_allergies=raw.get("drugs_and_allergies", ""),
        family_history=raw.get("family_history", ""),
        personal_history=raw.get("personal_history", ""),
        review_of_systems=raw.get("review_of_systems", ""),
        prior_investigations=raw.get("prior_investigations", ""),
        low_confidence_fields=_low_confidence_fields(fields, confidences),
    )

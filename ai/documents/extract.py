# Owner: Nikki
"""Vision-model extraction over a prescription or lab report photo."""

from pathlib import Path

from ai.adapters.base import MalformedOutputError, VisionAdapter
from ai.knowledge.drug_names import normalize_drug_name
from ai.knowledge.lab_ranges import check_lab_range
from ai.types import DocumentExtraction

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "document.txt"


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def _normalize_medications(raw_medications) -> list[dict]:
    if not isinstance(raw_medications, list):
        return []
    normalized = []
    for item in raw_medications:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        normalized.append(
            {"name": normalize_drug_name(str(item["name"])), "dosage": str(item.get("dosage", ""))}
        )
    return normalized


def _normalize_lab_values(raw_lab_values) -> list[dict]:
    if not isinstance(raw_lab_values, list):
        return []
    normalized = []
    for item in raw_lab_values:
        if not isinstance(item, dict) or not item.get("test_name"):
            continue
        entry = {
            "test_name": item["test_name"],
            "value": item.get("value"),
            "unit": item.get("unit", ""),
        }
        value = item.get("value")
        if isinstance(value, (int, float)):
            flag = check_lab_range(str(item["test_name"]), float(value))
            if flag:
                entry["flag"] = flag
        normalized.append(entry)
    return normalized


def extract_document(image_bytes: bytes, vision: VisionAdapter) -> DocumentExtraction:
    """Extract structured data from an uploaded prescription/lab report photo.

    Returns whatever fields the vision model could make out rather than
    failing the whole document on a blurry or partial image.
    """
    prompt = _load_prompt()
    try:
        raw = vision.extract_from_image(image_bytes, prompt)
    except MalformedOutputError:
        return DocumentExtraction(low_confidence=True)

    diagnoses = raw.get("diagnoses", [])
    if not isinstance(diagnoses, list):
        diagnoses = []

    dates = raw.get("dates", [])
    if not isinstance(dates, list):
        dates = []

    return DocumentExtraction(
        diagnoses=[str(d) for d in diagnoses],
        medications=_normalize_medications(raw.get("medications")),
        lab_values=_normalize_lab_values(raw.get("lab_values")),
        dates=[str(d) for d in dates],
        low_confidence=bool(raw.get("low_confidence", False)),
    )

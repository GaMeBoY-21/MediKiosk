# Owner: Nikki
"""Vision-model extraction over a prescription or lab report photo."""

from pathlib import Path

from app.schemas import DocumentFinding, DocumentRecord, DocumentStatus, FindingKind

from ai.adapters.base import MalformedOutputError, VisionAdapter
from ai.knowledge.drug_names import normalize_drug_name
from ai.knowledge.lab_ranges import check_lab_range

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "document.txt"


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def _diagnosis_findings(raw_diagnoses) -> list[DocumentFinding]:
    if not isinstance(raw_diagnoses, list):
        return []
    findings = []
    for item in raw_diagnoses:
        label = str(item).strip()
        if not label:
            continue
        findings.append(DocumentFinding(kind=FindingKind.diagnosis, label=label, value=label))
    return findings


def _medication_findings(raw_medications) -> list[DocumentFinding]:
    if not isinstance(raw_medications, list):
        return []
    findings = []
    for item in raw_medications:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        name = normalize_drug_name(str(item["name"]))
        dosage = str(item.get("dosage", "")).strip()
        findings.append(DocumentFinding(kind=FindingKind.medication, label=name, value=dosage))
    return findings


def _lab_findings(raw_lab_values) -> list[DocumentFinding]:
    if not isinstance(raw_lab_values, list):
        return []
    findings = []
    for item in raw_lab_values:
        if not isinstance(item, dict) or not item.get("test_name"):
            continue
        value = item.get("value")
        out_of_range = False
        if isinstance(value, (int, float)):
            out_of_range = check_lab_range(str(item["test_name"]), float(value)) is not None
        findings.append(
            DocumentFinding(
                kind=FindingKind.lab,
                label=str(item["test_name"]),
                value=value if value is not None else "",
                unit=item.get("unit") or None,
                out_of_range=out_of_range,
            )
        )
    return findings


def _procedure_findings(raw_procedures) -> list[DocumentFinding]:
    if not isinstance(raw_procedures, list):
        return []
    findings = []
    for item in raw_procedures:
        if isinstance(item, dict):
            label = str(item.get("name", "")).strip()
            detail = str(item.get("detail", "")).strip()
        else:
            label, detail = str(item).strip(), ""
        if not label:
            continue
        findings.append(DocumentFinding(kind=FindingKind.procedure, label=label, value=detail))
    return findings


def _first_date(raw_dates) -> str | None:
    if isinstance(raw_dates, list) and raw_dates:
        return str(raw_dates[0])
    return None


def extract_document(image_bytes: bytes, doc_id: str, vision: VisionAdapter) -> DocumentRecord:
    """Extract structured data from an uploaded prescription/lab report photo.

    `doc_id` is the server-assigned identifier the caller already minted at
    upload time; this just fills in the record around it.

    Returns whatever findings the vision model could make out rather than
    failing the whole document on a blurry or partial image — status is only
    ever `failed` when the model's response couldn't be parsed at all.
    """
    prompt = _load_prompt()
    try:
        raw = vision.extract_from_image(image_bytes, prompt)
    except MalformedOutputError:
        return DocumentRecord(doc_id=doc_id, status=DocumentStatus.failed)

    findings = [
        *_diagnosis_findings(raw.get("diagnoses")),
        *_medication_findings(raw.get("medications")),
        *_lab_findings(raw.get("lab_values")),
        *_procedure_findings(raw.get("procedures")),
    ]

    return DocumentRecord(
        doc_id=doc_id,
        status=DocumentStatus.done,
        extracted=raw if isinstance(raw, dict) else {},
        date=_first_date(raw.get("dates")),
        findings=findings,
    )

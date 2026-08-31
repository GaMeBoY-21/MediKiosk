# Owner: Tharun
"""FHIR R4 document Bundle builder.

The transport is mocked; the bundle is not. This gets shown on screen to judges
and has to survive someone who actually knows FHIR reading it, so:

  - Bundle.type = "document", and the FIRST entry is the Composition (R4 requires
    exactly that for a document bundle).
  - Every entry has a fullUrl, and every reference points at that fullUrl as a
    urn:uuid, so the bundle is internally resolvable with no server round trip.
  - Resource ids are deterministic (uuid5 over the session id), so reopening a
    case shows the same bundle rather than a freshly randomised one.
  - Composition.status is "preliminary" until a physician accepts, then "final".
    That mirrors the console's unverified-draft banner exactly.
  - Codes are real LOINC / SNOMED / HL7 terminology, not invented strings.

Structured resources are built from structured data only. Nothing here parses
clinical facts out of prose — a wrongly regexed drug name is a patient safety
problem, not a formatting one. Where structured data is absent the resource is
simply omitted.

Reference: https://hl7.org/fhir/R4/documents.html
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas import ClinicalSummary, DocumentFinding, FindingKind

# Terminology systems
LOINC = "http://loinc.org"
SNOMED = "http://snomed.info/sct"
SYS_CONDITION_CLINICAL = "http://terminology.hl7.org/CodeSystem/condition-clinical"
SYS_CONDITION_VER = "http://terminology.hl7.org/CodeSystem/condition-ver-status"
SYS_CONDITION_CATEGORY = "http://terminology.hl7.org/CodeSystem/condition-category"
SYS_ALLERGY_CLINICAL = "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
SYS_ALLERGY_VER = "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification"
SYS_OBS_CATEGORY = "http://terminology.hl7.org/CodeSystem/observation-category"
SYS_INTERPRETATION = "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"

# Deterministic id namespace for this application.
_NS = uuid.UUID("6b1f5f4a-4a0e-5c2b-9f43-1d9c0a7e2f11")

ORGANISATION_NAME = "MediKiosk, Ministry of Ayush OPD"

# LOINC section codes, in standard clinical reading order.
SECTION_CODES = [
    ("chief_complaint", "10154-3", "Chief complaint Narrative - Reported"),
    ("hpi", "10164-2", "History of present illness Narrative"),
    ("past_history", "11348-0", "History of past illness Narrative"),
    ("drugs_allergies", "10160-0", "History of medication use Narrative"),
    ("family", "10157-6", "History of family member diseases Narrative"),
    ("personal", "29762-2", "Social history Narrative"),
    ("ros", "10187-3", "Review of systems Narrative"),
]


def _uid(session_id: str, key: str) -> str:
    """Stable resource id: same session and key always yield the same uuid."""
    return str(uuid.uuid5(_NS, f"{session_id}:{key}"))


def _urn(resource_id: str) -> str:
    return f"urn:uuid:{resource_id}"


def _iso(value: Optional[datetime] = None) -> str:
    return (value or datetime.now(timezone.utc)).isoformat()


def _text(value: str) -> Dict[str, str]:
    """A CodeableConcept carrying only display text.

    Legitimate FHIR: CodeableConcept.text is the human-readable form when no
    code applies. Better than inventing a code we cannot stand behind.
    """
    return {"text": value}


def _fhir_gender(sex: Optional[str]) -> str:
    """Map our sex values onto the FHIR administrative-gender value set."""
    mapping = {"male": "male", "m": "male", "female": "female", "f": "female", "other": "other"}
    return mapping.get((sex or "").strip().lower(), "unknown")


def _entry(resource: Dict[str, Any]) -> Dict[str, Any]:
    return {"fullUrl": _urn(resource["id"]), "resource": resource}


def build_fhir_bundle(
    summary: ClinicalSummary,
    patient_id: str,
    history: Optional[Dict[str, Any]] = None,
    patient: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a FHIR R4 document Bundle from a ClinicalSummary.

    Args:
        summary: the clinical summary being represented.
        patient_id: the session id, used as the deterministic id seed.
        history: structured ClinicalHistory data, when available. Conditions,
            medications and allergies are built from this and omitted without it.
        patient: name/age/sex/abha for the Patient resource.

    Returns a plain dict, JSON-serialisable as-is.
    """
    history = history or {}
    patient = patient or {}
    verified = bool(summary.verified_by)

    patient_uid = _uid(patient_id, "patient")
    patient_ref = {"reference": _urn(patient_uid)}
    entries: List[Dict[str, Any]] = []

    # ---------------------------------------------------------- Patient
    patient_resource: Dict[str, Any] = {
        "resourceType": "Patient",
        "id": patient_uid,
        "active": True,
        "gender": _fhir_gender(patient.get("sex")),
    }
    if patient.get("name"):
        patient_resource["name"] = [{"use": "official", "text": patient["name"]}]
    if patient.get("abha"):
        # ABHA is India's national health id. NDHM namespace.
        patient_resource["identifier"] = [
            {
                "system": "https://healthid.ndhm.gov.in",
                "value": patient["abha"],
                "type": _text("ABHA number"),
            }
        ]
    if patient.get("age") is not None:
        # Age, not date of birth: the kiosk asks for age, and inventing a
        # birthDate from it would be fabricated precision.
        patient_resource["extension"] = [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-age",
                "valueAge": {
                    "value": patient["age"],
                    "unit": "years",
                    "system": "http://unitsofmeasure.org",
                    "code": "a",
                },
            }
        ]

    # -------------------------------------------------------- Conditions
    # Kept in two buckets rather than one list: the Composition puts the chief
    # complaint and the past history in different sections, and slicing a single
    # list would silently mislabel a past condition as the chief complaint
    # whenever there is no chief complaint.
    chief_refs: List[Dict[str, str]] = []
    past_condition_refs: List[Dict[str, str]] = []
    condition_entries: List[Dict[str, Any]] = []

    def _condition(
        label: str,
        key: str,
        category: str,
        target: List[Dict[str, str]],
        is_active: bool = True,
    ) -> None:
        cid = _uid(patient_id, f"condition:{key}")
        condition_entries.append(
            _entry(
                {
                    "resourceType": "Condition",
                    "id": cid,
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": SYS_CONDITION_CLINICAL,
                                "code": "active" if is_active else "inactive",
                            }
                        ]
                    },
                    "verificationStatus": {
                        "coding": [
                            {
                                "system": SYS_CONDITION_VER,
                                # Patient-reported at a kiosk, not clinician-confirmed.
                                "code": "unconfirmed",
                            }
                        ]
                    },
                    "category": [
                        {"coding": [{"system": SYS_CONDITION_CATEGORY, "code": category}]}
                    ],
                    "code": _text(label),
                    "subject": patient_ref,
                    "recordedDate": _iso(summary.generated_at),
                }
            )
        )
        target.append({"reference": _urn(cid)})

    if summary.chief_complaint:
        _condition(summary.chief_complaint, "chief", "encounter-diagnosis", chief_refs)
    for i, item in enumerate(history.get("past_medical") or []):
        _condition(item, f"past-{i}", "problem-list-item", past_condition_refs)

    # ------------------------------------------------ MedicationStatements
    medication_refs: List[Dict[str, str]] = []
    medication_entries: List[Dict[str, Any]] = []

    def _medication(label: str, dosage: Any, key: str) -> None:
        mid = _uid(patient_id, f"medication:{key}")
        resource: Dict[str, Any] = {
            "resourceType": "MedicationStatement",
            "id": mid,
            "status": "active",
            "medicationCodeableConcept": _text(label),
            "subject": patient_ref,
            "dateAsserted": _iso(summary.generated_at),
            # The patient said so; nobody has verified it.
            "informationSource": patient_ref,
        }
        if dosage not in (None, ""):
            resource["dosage"] = [{"text": str(dosage)}]
        medication_entries.append(_entry(resource))
        medication_refs.append({"reference": _urn(mid)})

    # History entries carry their own dosage inside the string
    # ("Metformin 500 mg twice daily"), so there is nothing separate to split out.
    for i, med in enumerate(history.get("medications") or []):
        _medication(med, None, str(i))

    # ------------------------------------------------ AllergyIntolerances
    allergy_refs: List[Dict[str, str]] = []
    allergy_entries: List[Dict[str, Any]] = []
    for i, allergy in enumerate(history.get("allergies") or []):
        aid = _uid(patient_id, f"allergy:{i}")
        allergy_entries.append(
            _entry(
                {
                    "resourceType": "AllergyIntolerance",
                    "id": aid,
                    "clinicalStatus": {
                        "coding": [{"system": SYS_ALLERGY_CLINICAL, "code": "active"}]
                    },
                    "verificationStatus": {
                        "coding": [{"system": SYS_ALLERGY_VER, "code": "unconfirmed"}]
                    },
                    "code": _text(allergy),
                    "patient": patient_ref,
                    "recordedDate": _iso(summary.generated_at),
                }
            )
        )
        allergy_refs.append({"reference": _urn(aid)})

    # ---------------------------------------------------- document findings
    # Findings are one list with a `kind` discriminator, because a prescription
    # and a lab report come off the same page in the same order. `kind` maps
    # straight onto a resource type here.
    observation_refs: List[Dict[str, str]] = []
    observation_entries: List[Dict[str, Any]] = []
    procedure_refs: List[Dict[str, str]] = []
    procedure_entries: List[Dict[str, Any]] = []

    def _observation(finding: DocumentFinding, key: str, effective: Optional[str]) -> None:
        oid = _uid(patient_id, f"observation:{key}")
        resource: Dict[str, Any] = {
            "resourceType": "Observation",
            "id": oid,
            "status": "final" if verified else "preliminary",
            "category": [{"coding": [{"system": SYS_OBS_CATEGORY, "code": "laboratory"}]}],
            "code": _text(finding.label),
            "subject": patient_ref,
        }
        if effective:
            resource["effectiveDateTime"] = effective

        # valueQuantity only for real numbers; anything else is valueString.
        if isinstance(finding.value, (int, float)) and not isinstance(finding.value, bool):
            quantity: Dict[str, Any] = {"value": finding.value}
            if finding.unit:
                quantity["unit"] = finding.unit
                quantity["system"] = "http://unitsofmeasure.org"
            resource["valueQuantity"] = quantity
        else:
            resource["valueString"] = str(finding.value)

        if finding.ref:
            resource["referenceRange"] = [{"text": finding.ref}]
        if finding.out_of_range:
            resource["interpretation"] = [
                {"coding": [{"system": SYS_INTERPRETATION, "code": "A", "display": "Abnormal"}]}
            ]
        observation_entries.append(_entry(resource))
        observation_refs.append({"reference": _urn(oid)})

    def _procedure(label: str, detail: Any, key: str, effective: Optional[str]) -> None:
        pid = _uid(patient_id, f"procedure:{key}")
        resource: Dict[str, Any] = {
            "resourceType": "Procedure",
            "id": pid,
            # Read off a past document, so it already happened.
            "status": "completed",
            "code": _text(label),
            "subject": patient_ref,
        }
        if effective:
            resource["performedDateTime"] = effective
        if detail not in (None, ""):
            resource["note"] = [{"text": str(detail)}]
        procedure_entries.append(_entry(resource))
        procedure_refs.append({"reference": _urn(pid)})

    for doc in summary.document_timeline or []:
        for i, finding in enumerate(doc.findings or []):
            key = f"{doc.doc_id}:{i}"
            if finding.kind is FindingKind.medication:
                _medication(finding.label, finding.value, key)
            elif finding.kind is FindingKind.diagnosis:
                # A diagnosis printed on an old document is past history, not
                # the reason they came in today.
                _condition(finding.label, key, "problem-list-item", past_condition_refs)
            elif finding.kind is FindingKind.procedure:
                _procedure(finding.label, finding.value, key, doc.date)
            else:
                _observation(finding, key, doc.date)

    # --------------------------------------------------------- Composition
    flat = {
        "chief_complaint": summary.chief_complaint or "",
        "hpi": summary.hpi_narrative or "",
        **(summary.sections or {}),
    }

    section_refs = {
        "chief_complaint": chief_refs,
        "past_history": past_condition_refs,
        "drugs_allergies": medication_refs + allergy_refs,
    }

    sections: List[Dict[str, Any]] = []
    for key, code, display in SECTION_CODES:
        body = (flat.get(key) or "").strip()
        refs = section_refs.get(key, [])
        if not body and not refs:
            continue
        section: Dict[str, Any] = {
            "title": display,
            "code": {"coding": [{"system": LOINC, "code": code, "display": display}]},
        }
        if body:
            # Narrative must be XHTML in the div, per FHIR.
            section["text"] = {
                "status": "generated",
                "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{_escape(body)}</p></div>',
            }
        if refs:
            section["entry"] = refs
        sections.append(section)

    if observation_refs:
        sections.append(
            {
                "title": "Relevant diagnostic tests",
                "code": {
                    "coding": [
                        {"system": LOINC, "code": "30954-2", "display": "Relevant diagnostic tests"}
                    ]
                },
                "entry": observation_refs,
            }
        )

    if procedure_refs:
        sections.append(
            {
                "title": "History of procedures",
                "code": {
                    "coding": [
                        {
                            "system": LOINC,
                            "code": "47519-4",
                            "display": "History of Procedures Document",
                        }
                    ]
                },
                "entry": procedure_refs,
            }
        )

    composition = {
        "resourceType": "Composition",
        "id": _uid(patient_id, "composition"),
        "status": "final" if verified else "preliminary",
        "type": {
            "coding": [
                {"system": LOINC, "code": "34117-2", "display": "History and physical note"}
            ]
        },
        "subject": patient_ref,
        "date": _iso(summary.generated_at),
        "author": [{"display": summary.verified_by or ORGANISATION_NAME}],
        "title": "OPD intake summary",
        "confidentiality": "R",  # restricted
        "section": sections,
    }
    if verified:
        composition["attester"] = [
            {
                "mode": "legal",
                "time": _iso(summary.verified_at),
                "party": {"display": summary.verified_by},
            }
        ]

    # ---------------------------------------------------------- assemble
    # Composition MUST be first in a document bundle.
    entries.append(_entry(composition))
    entries.append(_entry(patient_resource))
    entries.extend(condition_entries)
    entries.extend(medication_entries)
    entries.extend(allergy_entries)
    entries.extend(observation_entries)
    entries.extend(procedure_entries)

    return {
        "resourceType": "Bundle",
        "id": _uid(patient_id, "bundle"),
        "identifier": {"system": "urn:ietf:rfc:3986", "value": _urn(_uid(patient_id, "bundle"))},
        "type": "document",
        "timestamp": _iso(summary.generated_at),
        "entry": entries,
    }


def _escape(text: str) -> str:
    """Minimal XML escaping for narrative div content."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ------------------------------------------------------------- validation

# Elements R4 marks as required (cardinality 1..*) for the resources we emit.
REQUIRED: Dict[str, List[str]] = {
    "Composition": ["status", "type", "date", "author", "title"],
    "Patient": [],
    "Condition": ["subject"],
    "MedicationStatement": ["status", "subject"],
    "Observation": ["status", "code", "subject"],
    "AllergyIntolerance": ["patient"],
    "Procedure": ["status", "subject"],
}


def validate_bundle(bundle: Dict[str, Any]) -> List[str]:
    """Check the bundle against R4's structural rules.

    Returns a list of problems; empty means it passed. Not a full profile
    validator — it checks the things that actually break a real FHIR consumer:
    required elements, document-bundle ordering, and reference resolvability.
    """
    problems: List[str] = []

    if bundle.get("resourceType") != "Bundle":
        problems.append("root resourceType must be Bundle")
    if bundle.get("type") != "document":
        problems.append("Bundle.type must be 'document'")
    if not bundle.get("timestamp"):
        problems.append("Bundle.timestamp is required for a document bundle")

    entries = bundle.get("entry") or []
    if not entries:
        problems.append("Bundle.entry is empty")
        return problems

    first = entries[0].get("resource", {})
    if first.get("resourceType") != "Composition":
        problems.append("first Bundle.entry must be the Composition")

    known_urls = set()
    for i, entry in enumerate(entries):
        if not entry.get("fullUrl"):
            problems.append(f"entry[{i}] missing fullUrl")
        known_urls.add(entry.get("fullUrl"))

        resource = entry.get("resource") or {}
        rtype = resource.get("resourceType")
        if not rtype:
            problems.append(f"entry[{i}] resource missing resourceType")
            continue
        if not resource.get("id"):
            problems.append(f"entry[{i}] {rtype} missing id")
        if entry.get("fullUrl") != f"urn:uuid:{resource.get('id')}":
            problems.append(f"entry[{i}] {rtype} fullUrl does not match resource id")

        for field in REQUIRED.get(rtype, []):
            if not resource.get(field):
                problems.append(f"{rtype}/{resource.get('id')} missing required '{field}'")

    # Every internal reference must resolve to an entry in this bundle.
    def _walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            ref = node.get("reference")
            if isinstance(ref, str) and ref.startswith("urn:uuid:") and ref not in known_urls:
                problems.append(f"unresolvable reference at {path}: {ref}")
            for key, value in node.items():
                _walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for idx, value in enumerate(node):
                _walk(value, f"{path}[{idx}]")

    _walk(entries, "entry")
    return problems

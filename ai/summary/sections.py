# Owner: Nikki
"""Every recorded field belongs to exactly one section of the console.

The physician console showed "Not recorded" in all seven sections for sessions
whose clinical record held a dozen answers. Two separate faults produced that,
and this module addresses the second:

  1. the summary was assembled from the in-memory session store rather than
     the persisted record, so a restart emptied it (fixed in
     app/routers/summary.py);

  2. the section text is written by the model, so when the model is slow,
     overloaded or returns nothing usable, every section came out blank even
     though the fields were right there.

The model's prose is better than a list of fields and stays the preferred
output. This is the floor beneath it: a deterministic mapping that guarantees
a recorded answer is SHOWN somewhere, whatever the model did. On this screen
"Not recorded" has to mean the patient was not asked — never that the
plumbing dropped it.

The mapping is derived from ai/interview/nodes.py rather than written out by
hand, so a field added to a node cannot quietly go missing here: it lands in
that node's section automatically, and anything genuinely unmapped is
reported by section_for() as None rather than silently discarded.
"""

from typing import Any, Dict, Iterable, Optional

from ai.interview.display import humanise
from ai.interview.nodes import NODES

# Which console section each interview stage feeds. Stages absent from this
# map hold no clinical content for the summary: identity and consent are the
# patient header, documents have their own timeline, confirm is a checkbox.
NODE_TO_SECTION: Dict[str, str] = {
    "chief_complaint": "chief_complaint",
    "hpi": "hpi_narrative",
    "ros": "ros",
    "past_medical": "past_history",
    "drug_allergy": "drugs_allergies",
    "family": "family",
    "personal": "personal",
}

# Everyday labels for the fields, so a section reads as a sentence fragment
# rather than as database columns. A field with no entry falls back to its own
# name with the underscores opened out, which is ugly on purpose: it should be
# noticed and named properly rather than disappearing.
FIELD_LABELS: Dict[str, str] = {
    "chief_complaint": "Complaint",
    "symptom_duration": "Duration",
    "symptom_site": "Site",
    "symptom_onset": "Onset",
    "symptom_character": "Character",
    "symptom_severity": "Severity",
    "symptom_radiation": "Radiates to",
    "symptom_timing": "Timing",
    "symptom_exacerbating_factors": "Worse with",
    "symptom_relieving_factors": "Better with",
    "associated_symptoms": "Associated symptoms",
    "ros_screen": "Review of systems",
    "past_medical_conditions": "Conditions",
    "past_surgeries": "Surgeries",
    "current_medications": "Medicines",
    "known_allergies": "Allergies",
    "family_history": "Family history",
    "smoking_status": "Smoking",
    "alcohol_use": "Alcohol",
    "diet": "Diet",
    "occupation": "Occupation",
    "sleep_pattern": "Sleep",
}


def _field_to_section() -> Dict[str, str]:
    """Built once from the node definitions. See the module docstring."""
    mapping: Dict[str, str] = {}
    for node_id, node in NODES.items():
        section = NODE_TO_SECTION.get(node_id)
        if not section:
            continue
        for field in tuple(node.required_fields) + tuple(node.optional_fields):
            mapping.setdefault(field, section)
    return mapping


FIELD_TO_SECTION: Dict[str, str] = _field_to_section()


def section_for(field: str) -> Optional[str]:
    """Which console section a field belongs in, or None if it belongs in none."""
    return FIELD_TO_SECTION.get(field)


def label_for(field: str) -> str:
    return FIELD_LABELS.get(field, field.replace("_", " ").capitalize())


def render_section(fields: Dict[str, Any], section: str) -> str:
    """The recorded answers for one section, as one readable line.

    Empty string when nothing in this section was recorded — which is what
    "Not recorded" should mean, and now the only thing it can mean.
    """
    parts = []
    for name, value in fields.items():
        if FIELD_TO_SECTION.get(name) != section:
            continue
        shown = humanise(value)
        if shown:
            parts.append(f"{label_for(name)}: {shown}")
    return " · ".join(parts)


def covered_fields(fields: Iterable[str]) -> Dict[str, str]:
    """Field -> section, for the fields that reach the console at all.

    Used by the test that asserts a session with N recorded fields renders
    those N. Identity, consent and the document flags are deliberately absent:
    they are shown elsewhere on the screen, not in the clinical sections.
    """
    return {f: FIELD_TO_SECTION[f] for f in fields if f in FIELD_TO_SECTION}


def fill_missing(summary, fields: Dict[str, Any]):
    """Give every empty section its recorded answers. Mutates and returns.

    Only fills what the model left blank: where it wrote prose, that prose is
    better and is kept.
    """
    sections = dict(summary.sections or {})

    if not (summary.chief_complaint or "").strip():
        summary.chief_complaint = render_section(fields, "chief_complaint") or None
    if not (summary.hpi_narrative or "").strip():
        summary.hpi_narrative = render_section(fields, "hpi_narrative") or None

    for section in ("past_history", "drugs_allergies", "family", "personal", "ros"):
        if not str(sections.get(section, "")).strip():
            rendered = render_section(fields, section)
            if rendered:
                sections[section] = rendered

    summary.sections = sections
    return summary

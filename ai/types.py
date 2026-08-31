# Owner: Nikki
"""Placeholder data models for ai/.

app/schemas.py is Tharun's file and is empty as of this writing. Every
dataclass below stands in for a Pydantic model that belongs there — each
docstring names the app.schemas symbol it replaces. Swap these out for real
imports once app.schemas defines them; nothing in ai/ should keep its own
model definitions once that happens.
"""

from dataclasses import dataclass, field


@dataclass
class FollowUpQuestion:
    """TODO: replace with app.schemas.FollowUpQuestion"""

    text: str
    options: list[str] = field(default_factory=list)


@dataclass
class ClinicalSummary:
    """TODO: replace with app.schemas.ClinicalSummary"""

    chief_complaint: str
    hpi_narrative: str
    past_medical_surgical: str
    drugs_and_allergies: str
    family_history: str
    personal_history: str
    review_of_systems: str
    prior_investigations: str
    low_confidence_fields: list[str] = field(default_factory=list)


@dataclass
class DocumentExtraction:
    """TODO: replace with app.schemas.DocumentExtraction"""

    diagnoses: list[str] = field(default_factory=list)
    medications: list[dict] = field(default_factory=list)
    lab_values: list[dict] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    low_confidence: bool = False

# Owner: Nikki
"""Placeholder data models for ai/.

app/schemas.py is Tharun's file and is empty as of this writing. Every
dataclass below stands in for a Pydantic model that belongs there — each
docstring names the app.schemas symbol it replaces. Swap these out for real
imports once app.schemas defines them; nothing in ai/ should keep its own
model definitions once that happens.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RedFlag:
    """TODO: replace with app.schemas.RedFlag"""

    rule_id: str
    label: str
    severity: str  # "critical" | "urgent"
    matched_fields: list[str] = field(default_factory=list)

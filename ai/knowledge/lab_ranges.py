# Owner: Nikki
"""Lab reference ranges. Not a model.

Approximate adult reference ranges used to flag a lab value read off a
report as out-of-range. Deliberately approximate — a physician reviews
every flagged value, this is just a triage signal.
"""

LAB_RANGES: dict[str, dict] = {
    "hemoglobin": {"unit": "g/dL", "low": 12.0, "high": 17.0},
    "wbc_count": {"unit": "cells/cumm", "low": 4000, "high": 11000},
    "platelet_count": {"unit": "cells/cumm", "low": 150000, "high": 450000},
    "fasting_blood_sugar": {"unit": "mg/dL", "low": 70, "high": 100},
    "random_blood_sugar": {"unit": "mg/dL", "low": 70, "high": 140},
    "hba1c": {"unit": "%", "low": 4.0, "high": 5.6},
    "creatinine": {"unit": "mg/dL", "low": 0.6, "high": 1.3},
    "blood_urea": {"unit": "mg/dL", "low": 7, "high": 20},
    "total_cholesterol": {"unit": "mg/dL", "low": 0, "high": 200},
    "ldl": {"unit": "mg/dL", "low": 0, "high": 100},
    "hdl": {"unit": "mg/dL", "low": 40, "high": 200},
    "triglycerides": {"unit": "mg/dL", "low": 0, "high": 150},
    "tsh": {"unit": "mIU/L", "low": 0.4, "high": 4.0},
    "bilirubin_total": {"unit": "mg/dL", "low": 0.3, "high": 1.2},
    "sgpt_alt": {"unit": "U/L", "low": 7, "high": 56},
    "sgot_ast": {"unit": "U/L", "low": 8, "high": 48},
    "sodium": {"unit": "mmol/L", "low": 135, "high": 145},
    "potassium": {"unit": "mmol/L", "low": 3.5, "high": 5.1},
}


def check_lab_range(test_name: str, value: float) -> str | None:
    """Return "low", "high", or None (in range, or an unknown test)."""
    key = test_name.strip().lower().replace(" ", "_")
    reference = LAB_RANGES.get(key)
    if reference is None:
        return None
    if value < reference["low"]:
        return "low"
    if value > reference["high"]:
        return "high"
    return None

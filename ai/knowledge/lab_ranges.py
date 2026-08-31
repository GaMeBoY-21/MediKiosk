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


# A report prints whatever the lab's software prints. Spelling differences are
# not a reason to skip a range check: "Haemoglobin 11.2" went unflagged purely
# because this table spelled it the American way, so an anaemic patient's
# result was shown to the physician as if it were normal.
_ALIASES: dict[str, str] = {
    "haemoglobin": "hemoglobin",
    "hb": "hemoglobin",
    "hgb": "hemoglobin",
    "hba1c": "hba1c",
    "glycated_haemoglobin": "hba1c",
    "glycosylated_hemoglobin": "hba1c",
    "fbs": "fasting_blood_sugar",
    "fasting_glucose": "fasting_blood_sugar",
    "fasting_plasma_glucose": "fasting_blood_sugar",
    "rbs": "random_blood_sugar",
    "random_glucose": "random_blood_sugar",
    "tlc": "wbc_count",
    "total_leucocyte_count": "wbc_count",
    "total_leukocyte_count": "wbc_count",
    "wbc": "wbc_count",
    "platelets": "platelet_count",
    "serum_creatinine": "creatinine",
    "urea": "blood_urea",
    "blood_urea_nitrogen": "blood_urea",
    "cholesterol": "total_cholesterol",
    "serum_cholesterol": "total_cholesterol",
    "ldl_cholesterol": "ldl",
    "hdl_cholesterol": "hdl",
    "tg": "triglycerides",
    "sgpt": "sgpt_alt",
    "alt": "sgpt_alt",
    "sgot": "sgot_ast",
    "ast": "sgot_ast",
    "total_bilirubin": "bilirubin_total",
    "s_sodium": "sodium",
    "na": "sodium",
    "s_potassium": "potassium",
    "k": "potassium",
}


def _canonical(test_name: str) -> str:
    """Normalise a printed test name to a key in LAB_RANGES, if we know it."""
    key = test_name.strip().lower()
    # Drop the qualifiers labs prefix onto test names.
    for prefix in ("serum ", "s. ", "s ", "plasma ", "blood ", "total "):
        if key.startswith(prefix) and key != "total cholesterol":
            key = key[len(prefix):]
            break
    key = "_".join(key.replace("-", " ").replace(".", " ").split())
    if key in LAB_RANGES:
        return key
    return _ALIASES.get(key, key)


def check_lab_range(test_name: str, value: float) -> str | None:
    """Return "low", "high", or None (in range, or an unknown test)."""
    reference = LAB_RANGES.get(_canonical(test_name))
    if reference is None:
        return None
    if value < reference["low"]:
        return "low"
    if value > reference["high"]:
        return "high"
    return None

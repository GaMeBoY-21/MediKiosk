# Owner: Nikki
"""Drug name lookup table. Not a model.

Maps common brand names / generic spellings a vision model might read off a
prescription to a canonical generic name, so document extraction reports one
consistent name per drug instead of whatever brand was printed.
"""

import re

DRUG_NAMES: dict[str, str] = {
    "paracetamol": "Paracetamol",
    "acetaminophen": "Paracetamol",
    "crocin": "Paracetamol",
    "dolo": "Paracetamol",
    "calpol": "Paracetamol",
    "ibuprofen": "Ibuprofen",
    "brufen": "Ibuprofen",
    "combiflam": "Ibuprofen-Paracetamol",
    "amoxicillin": "Amoxicillin",
    "amoxyclav": "Amoxicillin-Clavulanate",
    "augmentin": "Amoxicillin-Clavulanate",
    "azithromycin": "Azithromycin",
    "azithral": "Azithromycin",
    "azee": "Azithromycin",
    "ciprofloxacin": "Ciprofloxacin",
    "cifran": "Ciprofloxacin",
    "metformin": "Metformin",
    "glycomet": "Metformin",
    "amlodipine": "Amlodipine",
    "amlopres": "Amlodipine",
    "atorvastatin": "Atorvastatin",
    "atorva": "Atorvastatin",
    "omeprazole": "Omeprazole",
    "omez": "Omeprazole",
    "pantoprazole": "Pantoprazole",
    "pan": "Pantoprazole",
    "pantocid": "Pantoprazole",
    "cetirizine": "Cetirizine",
    "levocetirizine": "Levocetirizine",
    "ors": "Oral Rehydration Salts",
    "insulin": "Insulin",
    "losartan": "Losartan",
    "telmisartan": "Telmisartan",
    "telma": "Telmisartan",
    "aspirin": "Aspirin",
    "ecosprin": "Aspirin",
    "clopidogrel": "Clopidogrel",
    "levothyroxine": "Levothyroxine",
    "thyronorm": "Levothyroxine",
    "eltroxin": "Levothyroxine",
}


# Dosage forms printed in front of the drug name on an Indian prescription.
_DOSAGE_FORMS = (
    "tab", "tabs", "tablet", "tablets", "cap", "caps", "capsule", "capsules",
    "syp", "syr", "syrup", "inj", "injection", "susp", "suspension", "oint",
    "ointment", "drop", "drops", "sol", "solution", "powder", "sachet",
)

# "500 mg", "5mg", "75 mcg", "10 ml", "40 iu" — a strength, not part of the name.
_STRENGTH_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|gm|ml|iu|units?|%)\b", re.IGNORECASE)
_NON_WORD_RE = re.compile(r"[^a-z0-9\s]+")


def normalize_drug_name(raw_name: str) -> str:
    """Return the canonical generic name for a drug name read off a document.

    A prescription almost never prints a bare drug name — it prints
    "Tab. Glycomet 500 mg". Matching the whole string against the table missed
    every single time and silently fell through to a title-cased copy of the
    label, so this table looked wired up while doing nothing at all.

    Strips the dosage form and strength, then matches the remaining words. Any
    word that names a known drug wins. Falls back to a tidied version of the
    input rather than dropping a medication we could not identify — an
    unrecognised drug still belongs in the record.
    """
    cleaned = _STRENGTH_RE.sub(" ", raw_name.lower())
    cleaned = _NON_WORD_RE.sub(" ", cleaned)
    words = [w for w in cleaned.split() if w and w not in _DOSAGE_FORMS]

    if not words:
        return raw_name.strip().title()

    # Whole remaining phrase first ("amoxicillin clavulanate"), then each word,
    # so a combination name is not split apart by a single-word match.
    phrase = " ".join(words)
    if phrase in DRUG_NAMES:
        return DRUG_NAMES[phrase]
    for word in words:
        if word in DRUG_NAMES:
            return DRUG_NAMES[word]
    return " ".join(words).title()

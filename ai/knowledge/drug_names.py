# Owner: Nikki
"""Drug name lookup table. Not a model.

Maps common brand names / generic spellings a vision model might read off a
prescription to a canonical generic name, so document extraction reports one
consistent name per drug instead of whatever brand was printed.
"""

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


def normalize_drug_name(raw_name: str) -> str:
    """Return the canonical generic name for a drug name read off a document.

    Falls back to a title-cased version of the input rather than dropping
    the medication entirely when it isn't in the table.
    """
    key = raw_name.strip().lower()
    return DRUG_NAMES.get(key, raw_name.strip().title())

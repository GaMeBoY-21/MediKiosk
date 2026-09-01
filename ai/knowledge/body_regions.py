# Owner: Nikki
"""Complaint phrase -> body region, and duration phrase -> canonical token.

A lookup table, not a model. The kiosk used to ask "where on your body?" of a
patient who had just said "back pain": the model folded the site into
chief_complaint, symptom_site stayed empty, the state machine saw an unfilled
required field and re-asked, and the model folded it in again. The loop only
broke on the node's follow-up cap.

Capping is a bandage. The real fix is that "back pain" ALREADY answers "where",
and something has to say so deterministically, before the state machine decides
what is still missing. That is what this table is for.

Deterministic on purpose. Flow and safety must not depend on the model being
consistent between two calls it has no memory of.
"""

import re

# Complaint phrase -> canonical symptom_site value.
#
# Longest phrase wins (see site_for_complaint), so "lower back pain" resolves
# to back rather than matching some shorter substring first.
#
# Values are canonical English tokens, the same vocabulary extraction is told
# to produce, because ai/safety/red_flags.py matches on them.
BODY_REGIONS: dict[str, str] = {
    # --- head and neck ---
    "headache": "head",
    "head ache": "head",
    "head pain": "head",
    "migraine": "head",
    "head": "head",
    "eye pain": "eye",
    "eye": "eye",
    "ear pain": "ear",
    "earache": "ear",
    "ear": "ear",
    "toothache": "tooth",
    "tooth pain": "tooth",
    "dental pain": "tooth",
    "sore throat": "throat",
    "throat pain": "throat",
    "throat": "throat",
    "neck pain": "neck",
    # --- chest and breathing ---
    "chest pain": "chest",
    "pain in chest": "chest",
    "pain in the chest": "chest",
    "chest discomfort": "chest",
    "chest tightness": "chest",
    "chest": "chest",
    # --- abdomen ---
    "abdominal pain": "abdomen",
    "stomach pain": "abdomen",
    "stomach ache": "abdomen",
    "stomachache": "abdomen",
    "belly pain": "abdomen",
    "tummy pain": "abdomen",
    "abdomen": "abdomen",
    "stomach": "abdomen",
    "acidity": "abdomen",
    # --- back ---
    "back pain": "back",
    "backache": "back",
    "back ache": "back",
    "lower back pain": "back",
    "low back pain": "back",
    "upper back pain": "back",
    "pain in back": "back",
    "pain in the back": "back",
    "back": "back",
    # --- limbs ---
    "leg pain": "leg",
    "knee pain": "knee",
    "arm pain": "arm",
    "shoulder pain": "shoulder",
    "hand pain": "hand",
    "foot pain": "foot",
    # --- genitourinary ---
    "burning urination": "urinary",
    "burning while passing urine": "urinary",
    "painful urination": "urinary",
    "urinary": "urinary",
}

# Complaints that name no region, or name one too vague to be an answer to
# "where?". Listed explicitly rather than left to fall through, because
# "which joint" and "where on your skin" are questions genuinely worth asking,
# and a wrongly derived site would stop them being asked at all.
#
# "fever" is not a site; neither is "weakness". A tapped "joints" tile says the
# problem is in a joint, not which one.
NO_SITE_COMPLAINTS: frozenset = frozenset(
    {
        "fever",
        "joints",
        "joint pain",
        "body ache",
        "body pain",
        "skin",
        "rash",
        "itching",
        "weakness",
        "tiredness",
        "fatigue",
        "dizziness",
        "giddiness",
        "fainting",
        "other",
        "something else",
        "swelling",
        "bleeding",
        "injury",
        # Respiratory and gastrointestinal symptoms name no place the patient
        # can point to, and mapping them to a region was actively harmful:
        # "breathlessness" resolving to symptom_site=chest made a purely
        # respiratory complaint indistinguishable from a chest-pain one, and
        # ai/safety/red_flags.py reads symptom_site. A derived site must never
        # invent a clinical picture the patient did not describe.
        "breathlessness",
        "breathing",
        "shortness of breath",
        "difficulty breathing",
        "cough",
        "palpitations",
        "vomiting",
        "loose motions",
        "diarrhoea",
        "diarrhea",
        "constipation",
    }
)

# Sorted longest first so the most specific phrase present in the text wins.
_REGION_PHRASES: tuple = tuple(
    sorted(BODY_REGIONS.items(), key=lambda kv: len(kv[0]), reverse=True)
)


def _flatten(value) -> str:
    """Multi-select fields arrive as lists. Read them as one string."""
    if isinstance(value, (list, tuple)):
        return " ".join(str(item) for item in value)
    return str(value or "")


def _normalise(text) -> str:
    """Lowercase, single-spaced, underscores opened out.

    Values reaching here are not always prose. A field already holding a
    canonical token ("2_days", "back_pain") has to read the same as the
    sentence it came from, or a duration we ourselves stored fails to parse
    back out and the patient is asked for it a second time.
    """
    return re.sub(r"\s+", " ", _flatten(text).replace("_", " ").strip().lower())


# Public alias: other modules in ai/knowledge/ normalise the same way, and one
# flattening/lowercasing rule beats three subtly different ones.
def normalise(text) -> str:
    return _normalise(text)


def _contains_phrase(text: str, phrase: str) -> bool:
    """Whole-word containment.

    Plain `in` would match "ear" inside "heart" and "arm" inside "warm". Word
    boundaries keep a one-word key from firing on an unrelated longer word.
    """
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text) is not None


def site_for_complaint(complaint) -> str:
    """The body region a complaint already names, or "" when it names none.

    Empty means "this complaint does not answer 'where?'", so the interview
    should still ask. Returning a guess here would be worse than asking.
    """
    text = _normalise(complaint)
    if not text or text in NO_SITE_COMPLAINTS:
        return ""
    # Exact match first: a tapped tile value ("back", "chest") is already
    # canonical and needs no scanning.
    exact = BODY_REGIONS.get(text)
    if exact:
        return exact
    for phrase, site in _REGION_PHRASES:
        if _contains_phrase(text, phrase):
            return site
    return ""


# --------------------------------------------------------------- durations

_WORD_NUMBERS: dict = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "couple": 2,
    "few": 3,
}

_UNIT_CANON: dict = {
    "hour": "hours", "hours": "hours", "hr": "hours", "hrs": "hours",
    "day": "days", "days": "days",
    "week": "weeks", "weeks": "weeks",
    "month": "months", "months": "months",
    "year": "years", "years": "years",
}

_DURATION_RE = re.compile(
    r"(?<!\w)(\d{1,3}|" + "|".join(_WORD_NUMBERS) + r")\s*"
    r"(hours|hour|hrs|hr|days|day|weeks|week|months|month|years|year)(?!\w)"
)

# Phrases that are a duration on their own, with no number in them.
_BARE_DURATIONS: dict = {
    "today": "today",
    "since today": "today",
    "this morning": "today",
    "since morning": "today",
    "last night": "1_day",
    "yesterday": "1_day",
    "since yesterday": "1_day",
    "day before yesterday": "2_days",
    "last week": "1_week",
    "since last week": "1_week",
    "last month": "1_month",
    "since last month": "1_month",
    "last year": "1_year",
    "many years": "many_years",
    "several years": "many_years",
    "a long time": "long_time",
    "long time": "long_time",
}

_BARE_PHRASES: tuple = tuple(sorted(_BARE_DURATIONS, key=len, reverse=True))


def duration_token(text) -> str:
    """"for two days" -> "2_days", "since today" -> "today", else "".

    The token vocabulary matches what the model is told to emit for duration
    options ("2_days", "1_week"), so a derived value and a tapped one are
    indistinguishable downstream.
    """
    blob = _normalise(text)
    if not blob:
        return ""

    match = _DURATION_RE.search(blob)
    if match:
        raw_count, raw_unit = match.group(1), match.group(2)
        count = int(raw_count) if raw_count.isdigit() else _WORD_NUMBERS.get(raw_count)
        unit = _UNIT_CANON.get(raw_unit)
        if count is not None and unit:
            # "1 days" reads wrong in a summary a physician actually sees.
            if count == 1:
                unit = unit.rstrip("s")
            return str(count) + "_" + unit

    for phrase in _BARE_PHRASES:
        if _contains_phrase(blob, phrase):
            return _BARE_DURATIONS[phrase]
    return ""

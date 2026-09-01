# Owner: Nikki
"""Complaint category -> the danger symptoms worth putting to that patient.

A lookup table, not a model. A back-pain patient was offered "breathlessness":
forcing a danger symptom into the associated_symptoms question was right,
letting the model pick which one was not.

This matters more than the other tables in ai/knowledge/. For a patient
answering by touch, these options are the ONLY danger signs they can report at
all — there is no free text to fall back on. A wrong list is not a cosmetic
problem: it is the difference between a red flag firing and a patient going
back into the queue. Safety-relevant content is not model-generated here. The
model translates these labels into the patient's language and does nothing
else; ai/interview/followup.py enforces that by rebuilding the option list from
this file after the model has answered.

Values are canonical English tokens and MUST stay in English: they are what
ai/safety/red_flags.py matches on, and what the physician's summary reads.
"""

from ai.knowledge.body_regions import normalise, site_for_complaint

# One entry per complaint category: (canonical english value, english label).
# The label is what the model is asked to translate; the value never changes.
#
# Kept to four or fewer plus "none", because the whole set has to be readable
# at 40px type by someone who may not read well, standing up, in a queue.
DANGER_SYMPTOMS: dict = {
    "chest_pain": (
        ("breathlessness", "Breathlessness"),
        ("pain_radiating_to_arm_or_jaw", "Pain spreading to arm or jaw"),
        ("sweating", "Sweating"),
    ),
    "headache": (
        ("one_sided_weakness", "Weakness on one side of the body"),
        ("vision_change", "Change in eyesight"),
        ("neck_stiffness", "Stiff neck"),
        # Kept from the prompt this table replaces. The old instruction sent
        # headache/weakness/fainting to "slurred_speech", and dropping it would
        # have quietly removed a stroke sign from the touch path.
        ("slurred_speech", "Slurred speech"),
    ),
    "back_pain": (
        ("leg_weakness", "Weakness in the legs"),
        ("numbness", "Numbness"),
        ("loss_of_bladder_or_bowel_control", "Loss of control of urine or stool"),
    ),
    "abdominal_pain": (
        ("vomiting_blood", "Vomiting blood"),
        ("black_stools", "Black stools"),
        ("fever_with_rigors", "Fever with shivering"),
    ),
    "breathlessness": (
        ("chest_pain", "Chest pain"),
        ("swelling_of_legs", "Swelling of the legs"),
        ("coughing_blood", "Coughing blood"),
    ),
    "fever": (
        ("neck_stiffness", "Stiff neck"),
        ("confusion", "Confusion or drowsiness"),
        ("difficulty_breathing", "Difficulty breathing"),
    ),
}

# Used when the complaint does not resolve to a category. Never a model
# choice: an unrecognised complaint is exactly the case where the model is
# least likely to be consistent, and the patient most needs a usable list.
GENERIC_DANGER_SYMPTOMS: tuple = (
    ("chest_pain", "Chest pain"),
    ("breathlessness", "Breathlessness"),
    ("bleeding", "Bleeding"),
    ("fainting", "Fainting or blackout"),
)

# Always last, always present. Without it a patient with none of these has no
# way to say so and either taps one falsely or cannot advance.
NONE_OPTION = ("none", "None of these")

# Danger-symptom labels in every language the kiosk speaks.
#
# The model is asked to translate these, and its translation is preferred when
# it supplies one. This table is the FALLBACK — and the fallback matters more
# than it looks, because it is used exactly when the model misbehaved: omitted
# an option, invented one, or returned nothing usable. Falling back to English
# there hands a Hindi-only patient a list of danger signs they cannot read,
# which is the same as not offering them at all.
#
# TRANSLATION NOTE: the same caveat as frontend/src/i18n/fieldNames.js. en and
# hi have been checked most carefully; kn, ta, te, mr and bn use everyday words
# but have NOT been reviewed by a native speaker. These are safety strings —
# get them reviewed before the judged demo.
DANGER_LABELS: dict = {
    "breathlessness": {
        "en": "Breathlessness", "hi": "साँस फूलना", "kn": "ಉಸಿರಾಟದ ತೊಂದರೆ",
        "ta": "மூச்சுத் திணறல்", "te": "ఊపిరి ఆడకపోవడం", "mr": "दम लागणे",
        "bn": "শ্বাসকষ্ট",
    },
    "pain_radiating_to_arm_or_jaw": {
        "en": "Pain spreading to arm or jaw", "hi": "दर्द बाँह या जबड़े तक जाना",
        "kn": "ನೋವು ತೋಳು ಅಥವಾ ದವಡೆಗೆ ಹರಡುವುದು",
        "ta": "வலி கை அல்லது தாடைக்குப் பரவுதல்",
        "te": "నొప్పి చేయి లేదా దవడకు వ్యాపించడం",
        "mr": "वेदना हात किंवा जबड्यापर्यंत पसरणे",
        "bn": "ব্যথা হাত বা চোয়ালে ছড়ানো",
    },
    "sweating": {
        "en": "Sweating", "hi": "पसीना आना", "kn": "ಬೆವರುವುದು",
        "ta": "வியர்வை", "te": "చెమటలు", "mr": "घाम येणे", "bn": "ঘাম হওয়া",
    },
    "one_sided_weakness": {
        "en": "Weakness on one side of the body", "hi": "शरीर के एक तरफ कमजोरी",
        "kn": "ದೇಹದ ಒಂದು ಬದಿಯಲ್ಲಿ ದೌರ್ಬಲ್ಯ",
        "ta": "உடலின் ஒரு பக்கம் பலவீனம்",
        "te": "శరీరం ఒక వైపు బలహీనత",
        "mr": "शरीराच्या एका बाजूला अशक्तपणा",
        "bn": "শরীরের এক দিকে দুর্বলতা",
    },
    "vision_change": {
        "en": "Change in eyesight", "hi": "नज़र में बदलाव",
        "kn": "ದೃಷ್ಟಿಯಲ್ಲಿ ಬದಲಾವಣೆ", "ta": "பார்வையில் மாற்றம்",
        "te": "చూపులో మార్పు", "mr": "दृष्टीत बदल", "bn": "দৃষ্টিতে পরিবর্তন",
    },
    "neck_stiffness": {
        "en": "Stiff neck", "hi": "गर्दन में अकड़न", "kn": "ಕುತ್ತಿಗೆ ಬಿಗಿತ",
        "ta": "கழுத்து இறுக்கம்", "te": "మెడ బిగుసుకుపోవడం",
        "mr": "मान आखडणे", "bn": "ঘাড় শক্ত হওয়া",
    },
    "slurred_speech": {
        "en": "Slurred speech", "hi": "बोलने में लड़खड़ाहट",
        "kn": "ಮಾತು ತೊದಲುವುದು", "ta": "பேச்சு தடுமாற்றம்",
        "te": "మాట తడబడటం", "mr": "बोलताना अडखळणे", "bn": "কথা জড়িয়ে যাওয়া",
    },
    "leg_weakness": {
        "en": "Weakness in the legs", "hi": "पैरों में कमजोरी",
        "kn": "ಕಾಲುಗಳಲ್ಲಿ ದೌರ್ಬಲ್ಯ", "ta": "கால்களில் பலவீனம்",
        "te": "కాళ్లలో బలహీనత", "mr": "पायांत अशक्तपणा", "bn": "পায়ে দুর্বলতা",
    },
    "numbness": {
        "en": "Numbness", "hi": "सुन्नपन", "kn": "ಮರಗಟ್ಟುವಿಕೆ",
        "ta": "மரத்துப்போதல்", "te": "మొద్దుబారడం", "mr": "बधिरपणा",
        "bn": "অসাড়তা",
    },
    "loss_of_bladder_or_bowel_control": {
        "en": "Loss of control of urine or stool",
        "hi": "पेशाब या शौच पर काबू न रहना",
        "kn": "ಮೂತ್ರ ಅಥವಾ ಮಲದ ಮೇಲೆ ಹಿಡಿತ ಇಲ್ಲದಿರುವುದು",
        "ta": "சிறுநீர் அல்லது மலம் கட்டுப்பாடு இழத்தல்",
        "te": "మూత్రం లేదా మలం మీద నియంత్రణ కోల్పోవడం",
        "mr": "लघवी किंवा शौचावर ताबा न राहणे",
        "bn": "প্রস্রাব বা পায়খানার নিয়ন্ত্রণ হারানো",
    },
    "vomiting_blood": {
        "en": "Vomiting blood", "hi": "खून की उल्टी", "kn": "ರಕ್ತ ವಾಂತಿ",
        "ta": "இரத்த வாந்தி", "te": "రక్తం వాంతి", "mr": "रक्ताची उलटी",
        "bn": "রক্ত বমি",
    },
    "black_stools": {
        "en": "Black stools", "hi": "काला शौच", "kn": "ಕಪ್ಪು ಮಲ",
        "ta": "கருப்பு மலம்", "te": "నల్లని మలం", "mr": "काळे शौच",
        "bn": "কালো পায়খানা",
    },
    "fever_with_rigors": {
        "en": "Fever with shivering", "hi": "कँपकँपी के साथ बुखार",
        "kn": "ನಡುಕದೊಂದಿಗೆ ಜ್ವರ", "ta": "நடுக்கத்துடன் காய்ச்சல்",
        "te": "వణుకుతో జ్వరం", "mr": "थंडी वाजून ताप", "bn": "কাঁপুনি সহ জ্বর",
    },
    "chest_pain": {
        "en": "Chest pain", "hi": "छाती में दर्द", "kn": "ಎದೆ ನೋವು",
        "ta": "மார்பு வலி", "te": "ఛాతీ నొప్పి", "mr": "छातीत दुखणे",
        "bn": "বুকে ব্যথা",
    },
    "swelling_of_legs": {
        "en": "Swelling of the legs", "hi": "पैरों में सूजन",
        "kn": "ಕಾಲುಗಳಲ್ಲಿ ಊತ", "ta": "கால்களில் வீக்கம்",
        "te": "కాళ్ల వాపు", "mr": "पायांना सूज", "bn": "পায়ে ফোলা",
    },
    "coughing_blood": {
        "en": "Coughing blood", "hi": "खाँसी में खून", "kn": "ಕೆಮ್ಮಿನಲ್ಲಿ ರಕ್ತ",
        "ta": "இருமலில் இரத்தம்", "te": "దగ్గులో రక్తం",
        "mr": "खोकल्यातून रक्त", "bn": "কাশিতে রক্ত",
    },
    "confusion": {
        "en": "Confusion or drowsiness", "hi": "भ्रम या बहुत नींद आना",
        "kn": "ಗೊಂದಲ ಅಥವಾ ಮಂಪರು", "ta": "குழப்பம் அல்லது மயக்கம்",
        "te": "గందరగోళం లేదా మత్తు", "mr": "गोंधळ किंवा गुंगी",
        "bn": "বিভ্রান্তি বা ঝিমুনি",
    },
    "difficulty_breathing": {
        "en": "Difficulty breathing", "hi": "साँस लेने में तकलीफ़",
        "kn": "ಉಸಿರಾಡಲು ಕಷ್ಟ", "ta": "மூச்சு விட சிரமம்",
        "te": "ఊపిరి తీసుకోవడం కష్టం", "mr": "श्वास घेण्यास त्रास",
        "bn": "শ্বাস নিতে কষ্ট",
    },
    "bleeding": {
        "en": "Bleeding", "hi": "खून बहना", "kn": "ರಕ್ತಸ್ರಾವ",
        "ta": "இரத்தப்போக்கு", "te": "రక్తస్రావం", "mr": "रक्तस्राव",
        "bn": "রক্তপাত",
    },
    "fainting": {
        "en": "Fainting or blackout", "hi": "बेहोशी", "kn": "ಮೂರ್ಛೆ",
        "ta": "மயக்கம்", "te": "స్పృహ తప్పడం", "mr": "बेशुद्ध पडणे",
        "bn": "অজ্ঞান হওয়া",
    },
    "none": {
        "en": "None of these", "hi": "इनमें से कोई नहीं",
        "kn": "ಇವುಗಳಲ್ಲಿ ಯಾವುದೂ ಇಲ್ಲ", "ta": "இவை எதுவும் இல்லை",
        "te": "వీటిలో ఏదీ లేదు", "mr": "यांपैकी काहीही नाही",
        "bn": "এর কোনোটিই নয়",
    },
}


def label_for(value: str, english: str, language: str) -> str:
    """The label for one danger symptom in the patient's language.

    Falls back to English only when this table has no entry, which for a value
    out of DANGER_SYMPTOMS should never happen — there is a guard test for it.
    """
    return (DANGER_LABELS.get(value) or {}).get(str(language or "en"), english)


# Body region -> category, for complaints that named a site.
_SITE_CATEGORY: dict = {
    "chest": "chest_pain",
    "head": "headache",
    "back": "back_pain",
    "abdomen": "abdominal_pain",
}

# Phrases that decide the category directly, ahead of the site. A patient whose
# complaint IS breathlessness maps to the breathlessness list even though
# body_regions files that under the chest.
_DIRECT_PHRASES: tuple = (
    (("breathless", "shortness of breath", "difficulty breathing", "cannot breathe",
      # The complaint screen's tile value is the bare word.
      "breathing"), "breathlessness"),
    (("fever", "temperature"), "fever"),
)


def category_for(fields: dict) -> str:
    """Which danger-symptom list this patient's complaint calls for.

    Returns "" when the complaint resolves to no category, and the caller uses
    GENERIC_DANGER_SYMPTOMS.
    """
    complaint = normalise(fields.get("chief_complaint"))
    for phrases, category in _DIRECT_PHRASES:
        if any(phrase in complaint for phrase in phrases):
            return category

    # The site the patient gave, or the one their complaint already implies.
    site = normalise(fields.get("symptom_site")) or site_for_complaint(
        fields.get("chief_complaint")
    )
    return _SITE_CATEGORY.get(site, "")


def english_danger_options(fields: dict) -> list:
    """The (value, english_label) pairs for this complaint, "none" last."""
    category = category_for(fields)
    return list(DANGER_SYMPTOMS.get(category) or GENERIC_DANGER_SYMPTOMS) + [NONE_OPTION]


def danger_options(fields: dict, language: str = "en") -> list:
    """The exact (value, label) pairs to offer, "none" last.

    Labels come back in `language`. This is the list the patient sees when the
    model gives us nothing usable, so it has to be readable on its own.
    """
    return [
        (value, label_for(value, english, language))
        for value, english in english_danger_options(fields)
    ]


def danger_values(fields: dict) -> list:
    """Just the canonical values, in order. What enforcement compares against."""
    return [value for value, _ in danger_options(fields)]


def describe_danger_options(fields: dict, language: str = "en") -> str:
    """The block dropped into the prompt where the option list belongs.

    Spelled out one per line with the value quoted, so there is nothing for the
    model to interpret: it copies the values and translates the labels. The
    reference translation is shown beside each one, so the model has an anchor
    rather than a free hand on a safety string.
    """
    lines = []
    for value, english in english_danger_options(fields):
        lines.append(
            '  - value "%s"  ->  label: "%s"   (reference: "%s")'
            % (value, english, label_for(value, english, language))
        )
    return "\n".join(lines)


__all__ = [
    "DANGER_SYMPTOMS",
    "GENERIC_DANGER_SYMPTOMS",
    "NONE_OPTION",
    "DANGER_LABELS",
    "category_for",
    "danger_options",
    "english_danger_options",
    "label_for",
    "danger_values",
    "describe_danger_options",
]
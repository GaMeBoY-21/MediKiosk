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
    (("breathless", "shortness of breath", "difficulty breathing", "cannot breathe"), "breathlessness"),
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


def danger_options(fields: dict) -> list:
    """The exact (value, english_label) pairs to offer, "none" last."""
    category = category_for(fields)
    items = DANGER_SYMPTOMS.get(category) or GENERIC_DANGER_SYMPTOMS
    return list(items) + [NONE_OPTION]


def danger_values(fields: dict) -> list:
    """Just the canonical values, in order. What enforcement compares against."""
    return [value for value, _ in danger_options(fields)]


def describe_danger_options(fields: dict) -> str:
    """The block dropped into the prompt where the option list belongs.

    Spelled out one per line with the value quoted, so there is nothing for the
    model to interpret: it copies the values and translates the labels.
    """
    lines = [
        '  - value "%s"  ->  label to translate: "%s"' % (value, label)
        for value, label in danger_options(fields)
    ]
    return "\n".join(lines)


__all__ = [
    "DANGER_SYMPTOMS",
    "GENERIC_DANGER_SYMPTOMS",
    "NONE_OPTION",
    "category_for",
    "danger_options",
    "danger_values",
    "describe_danger_options",
]
# Owner: Nikki
"""AYUSH Dashavidha Pariksha question set — an optional interview branch.

The ten classical examination parameters, plus Ahara-Vihara (diet and daily
routine), asked in plain language and mapped back to their classical names
for the physician summary. This is a question set and a prompt, not a
separate model — ai.interview.followup phrases these the same way it
phrases any other node's questions, constrained to this list.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DashavidhaQuestion:
    parameter: str  # classical Sanskrit name, shown to the physician
    field_name: str  # key the answer is stored under
    patient_question: str  # plain-language question asked to the patient
    options: tuple[str, ...] = ()  # empty means open-ended


DASHAVIDHA_QUESTIONS: tuple[DashavidhaQuestion, ...] = (
    DashavidhaQuestion(
        parameter="Prakriti",
        field_name="dashavidha_prakriti",
        patient_question="Since childhood, has your body always been more on the thin side, medium build, or heavy build?",
        options=("Thin", "Medium build", "Heavy build"),
    ),
    DashavidhaQuestion(
        parameter="Vikriti",
        field_name="dashavidha_vikriti",
        patient_question="Compared to how you normally feel, how much has this illness changed your body and energy?",
        options=("A little", "Somewhat", "A lot"),
    ),
    DashavidhaQuestion(
        parameter="Sara",
        field_name="dashavidha_sara",
        patient_question="Would you say your hair, skin, and nails are generally strong and healthy, or weak and easily damaged?",
        options=("Strong and healthy", "Average", "Weak and easily damaged"),
    ),
    DashavidhaQuestion(
        parameter="Samhanana",
        field_name="dashavidha_samhanana",
        patient_question="How would you describe your body frame — tightly built, average, or loosely built?",
        options=("Tightly built", "Average", "Loosely built"),
    ),
    DashavidhaQuestion(
        parameter="Pramana",
        field_name="dashavidha_pramana",
        patient_question="Do you feel your height and weight are well proportioned to each other?",
        options=("Yes, well proportioned", "Somewhat", "No"),
    ),
    DashavidhaQuestion(
        parameter="Satmya",
        field_name="dashavidha_satmya",
        patient_question="Are there foods, weather, or habits that always seem to suit you well, no matter what?",
    ),
    DashavidhaQuestion(
        parameter="Sattva",
        field_name="dashavidha_sattva",
        patient_question="When you are stressed or in pain, do you generally stay calm, get anxious, or get irritable?",
        options=("Stay calm", "Get anxious", "Get irritable"),
    ),
    DashavidhaQuestion(
        parameter="Ahara Shakti",
        field_name="dashavidha_ahara_shakti",
        patient_question="How is your appetite and digestion — do you feel hungry regularly and digest food easily?",
        options=("Good appetite and digestion", "Irregular appetite", "Poor appetite or digestion"),
    ),
    DashavidhaQuestion(
        parameter="Vyayama Shakti",
        field_name="dashavidha_vyayama_shakti",
        patient_question="How much physical activity or exercise can you comfortably do before feeling tired?",
        options=("A lot", "A moderate amount", "Very little"),
    ),
    DashavidhaQuestion(
        parameter="Vaya",
        field_name="dashavidha_vaya",
        patient_question="What is your age?",
    ),
)

AHARA_VIHARA_QUESTIONS: tuple[DashavidhaQuestion, ...] = (
    DashavidhaQuestion(
        parameter="Ahara (diet)",
        field_name="ahara_diet_pattern",
        patient_question="What do your meals usually look like — mostly vegetarian, non-vegetarian, or mixed?",
        options=("Vegetarian", "Non-vegetarian", "Mixed"),
    ),
    DashavidhaQuestion(
        parameter="Ahara (meal timing)",
        field_name="ahara_meal_timing",
        patient_question="Do you eat your meals at regular times each day, or does it vary a lot?",
        options=("Regular times", "Varies a lot"),
    ),
    DashavidhaQuestion(
        parameter="Vihara (daily routine)",
        field_name="vihara_daily_routine",
        patient_question="Would you describe your daily routine as active, or mostly sitting and resting?",
        options=("Active", "Mixed", "Mostly sitting or resting"),
    ),
    DashavidhaQuestion(
        parameter="Vihara (sleep)",
        field_name="vihara_sleep_pattern",
        patient_question="Do you sleep well and wake up feeling rested?",
        options=("Yes", "Sometimes", "No"),
    ),
)

ALL_DASHAVIDHA_FIELDS: tuple[str, ...] = tuple(
    question.field_name for question in DASHAVIDHA_QUESTIONS + AHARA_VIHARA_QUESTIONS
)

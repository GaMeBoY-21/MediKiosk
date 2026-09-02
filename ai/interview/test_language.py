# Owner: Nikki
"""The chosen language must actually reach the generated question.

This is the check that would have caught a whole class of bug cheaply: when the
language stops being threaded through, EVERY non-English language degrades to
English at once, and the failure is invisible to anyone reading English. The
assertion is deliberately crude — the question must not be byte-identical to
its English counterpart — because that is exactly what a dropped language
looks like, and it needs no translation knowledge to check.

Offline: the LLM is stubbed. What is under test is the plumbing (does the
language reach the prompt, and does the answer survive back to the caller),
not the model's translation quality.
"""

import re
import unittest

from app.schemas import QuestionOption

from ai.adapters.base import LLMAdapter
from ai.interview.followup import generate_followup
from ai.interview.nodes import get_node

NON_ENGLISH = ("hi", "kn", "ta", "te", "mr", "bn")

# What a correctly-behaving model returns: the question in the requested
# language, plus its English. Keyed off the language the PROMPT asked for, so
# if the language never reaches the prompt the stub answers in English and the
# test fails — which is the exact production failure being guarded against.
# question, then a label for each of the two option values.
BY_LANG = {
    "hi": ("यह दर्द कब से है?", "आज से", "हफ़्तों से"),
    "kn": ("ಈ ನೋವು ಎಷ್ಟು ದಿನದಿಂದ ಇದೆ?", "ಇಂದಿನಿಂದ", "ವಾರಗಳಿಂದ"),
    "ta": ("இந்த வலி எவ்வளவு நாட்களாக உள்ளது?", "இன்று முதல்", "வாரங்களாக"),
    "te": ("ఈ నొప్పి ఎప్పటి నుండి ఉంది?", "ఈ రోజు నుండి", "వారాలుగా"),
    "mr": ("ही वेदना किती दिवसांपासून आहे?", "आजपासून", "आठवड्यांपासून"),
    "bn": ("এই ব্যথা কতদিন ধরে আছে?", "আজ থেকে", "সপ্তাহ ধরে"),
    # For English the label and its English are the same string, exactly as a
    # correctly-behaving model would answer.
    "en": ("How long have you had this pain?", "Since today", "Weeks"),
}
ENGLISH_Q, ENGLISH_TODAY, ENGLISH_WEEKS = BY_LANG["en"]
ENGLISH_LABEL = ENGLISH_TODAY


class LanguageEchoingLLM(LLMAdapter):
    """Answers in whichever language the prompt actually asked for.

    Reads the language out of the rendered prompt rather than being told, so
    the test fails if the language never gets interpolated into it.
    """

    def __init__(self):
        self.last_prompt = ""

    def complete(self, prompt):  # pragma: no cover - unused
        return ""

    def complete_json(self, prompt):
        self.last_prompt = prompt
        # Word-boundary match: a bare substring finds "ta" inside ordinary
        # English words like "table" and mistakes an English prompt for Tamil.
        found = re.findall(r"\b(" + "|".join(NON_ENGLISH) + r")\b", prompt)
        lang = found[0] if found else "en"
        question, today, weeks = BY_LANG[lang]
        return {
            "target_field": "symptom_duration",
            "question": question,
            "question_en": ENGLISH_Q,
            "options": [
                {"value": "today", "label": today, "label_en": ENGLISH_TODAY},
                {"value": "weeks", "label": weeks, "label_en": ENGLISH_WEEKS},
            ],
        }


class TestQuestionIsTranslated(unittest.TestCase):
    def setUp(self):
        self.node = get_node("chief_complaint")
        self.filled = {"chief_complaint": "chest pain"}

    def test_language_reaches_the_prompt(self):
        """Every non-English language must appear in the rendered prompt."""
        for lang in NON_ENGLISH:
            with self.subTest(lang=lang):
                llm = LanguageEchoingLLM()
                generate_followup(self.node, dict(self.filled), lang, llm)
                self.assertIn(
                    lang,
                    llm.last_prompt,
                    f"the prompt never mentions {lang!r}; the language is not "
                    f"reaching the model, so every question comes back English",
                )

    def test_question_is_not_english(self):
        """The generated question must differ from its English counterpart."""
        for lang in NON_ENGLISH:
            with self.subTest(lang=lang):
                _, question, question_en, _ = generate_followup(
                    self.node, dict(self.filled), lang, LanguageEchoingLLM()
                )
                self.assertNotEqual(
                    question,
                    ENGLISH_Q,
                    f"{lang}: the question came back byte-identical to English",
                )
                self.assertEqual(question_en, ENGLISH_Q, f"{lang}: lost the English line")

    def test_option_labels_are_not_english(self):
        """Option tiles must translate too, not just the question."""
        for lang in NON_ENGLISH:
            with self.subTest(lang=lang):
                _, _, _, options = generate_followup(
                    self.node, dict(self.filled), lang, LanguageEchoingLLM()
                )
                self.assertTrue(options, f"{lang}: no options returned")
                for opt in options:
                    self.assertNotEqual(
                        opt.label,
                        opt.label_en,
                        f"{lang}: option {opt.value!r} label equals its English label",
                    )

    def test_english_renders_once(self):
        """For English there is nothing to show twice."""
        _, question, question_en, options = generate_followup(
            self.node, dict(self.filled), "en", LanguageEchoingLLM()
        )
        self.assertEqual(question, ENGLISH_Q)
        self.assertIsNone(question_en, "English must not carry a second English line")
        for opt in options:
            self.assertIsNone(opt.label_en, "English options must not carry label_en")


class TestDangerOptionsTranslate(unittest.TestCase):
    """Danger tiles are safety strings and the likeliest silent fallback.

    They are rebuilt from ai/knowledge/danger_symptoms.py rather than taken
    from the model, so if that table lacks a language they come back English
    while everything around them translates.
    """

    def test_danger_options_translate_in_every_language(self):
        from ai.knowledge.danger_symptoms import danger_options

        fields = {"chief_complaint": "chest pain"}
        english = {v: l for v, l in danger_options(fields, "en")}
        self.assertTrue(english, "no danger options for a chest-pain complaint")

        for lang in NON_ENGLISH:
            with self.subTest(lang=lang):
                localised = danger_options(fields, lang)
                self.assertEqual(
                    [v for v, _ in localised],
                    list(english),
                    f"{lang}: danger symptom VALUES must not change per language",
                )
                same = [v for v, label in localised if label == english[v]]
                self.assertFalse(
                    same,
                    f"{lang}: danger tiles {same} fell back to English — a "
                    f"touch-only patient cannot report a warning sign they "
                    f"cannot read",
                )


if __name__ == "__main__":
    unittest.main()

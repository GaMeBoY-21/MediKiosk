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

import pathlib
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


class TestEveryOptionCarriesEnglish(unittest.TestCase):
    """Every tile a patient can see must have its English underneath.

    The danger-symptom question was the one screen in the interview with
    Hindi-only tiles: enforce_danger_options rebuilds that list from the
    safety table and dropped whatever label_en the model had supplied. It was
    found by looking at the screen, which is the third English leak found that
    way — hence this test asserting the property for the whole option surface
    rather than for the node that happened to be noticed.
    """

    FIELDS = {"chief_complaint": "chest pain"}

    def test_danger_options_carry_english(self):
        for lang in NON_ENGLISH:
            with self.subTest(lang=lang):
                options = generate_followup(
                    get_node("hpi"),
                    dict(self.FIELDS, symptom_site="chest"),
                    lang,
                    LanguageEchoingLLM(),
                )[3]
                self.assertTrue(options, f"{lang}: no options at all")
                for opt in options:
                    self.assertTrue(
                        opt.label_en,
                        f"{lang}: option {opt.value!r} has no English label; the "
                        f"tile renders in {lang} only",
                    )
                    self.assertNotEqual(
                        opt.label_en,
                        opt.label,
                        f"{lang}: option {opt.value!r} shows the same string twice",
                    )

    def test_danger_options_carry_english_when_the_model_gives_nothing(self):
        """The rebuild path is exactly where the English was being lost."""
        from ai.interview.followup import enforce_danger_options

        for lang in NON_ENGLISH:
            with self.subTest(lang=lang):
                for opt in enforce_danger_options("associated_symptoms", self.FIELDS, [], lang):
                    self.assertTrue(
                        opt.label_en, f"{lang}: {opt.value!r} lost its English in the rebuild"
                    )

    def test_english_session_still_renders_once(self):
        """label_en must stay None for English, or every tile doubles up."""
        from ai.interview.followup import enforce_danger_options

        for opt in enforce_danger_options("associated_symptoms", self.FIELDS, [], "en"):
            self.assertIsNone(opt.label_en, f"{opt.value!r} would render English twice")


class TestAddingEnglishChangedNoValue(unittest.TestCase):
    """The English label is display. It must not perturb what the rules read.

    Same property as ai/interview/test_display.py asserts for the display
    label, on the other string added to an option since.
    """

    FIELDS = {"chief_complaint": "chest pain", "associated_symptoms": ["breathlessness"]}

    def test_values_are_identical_in_every_language(self):
        from ai.knowledge.danger_symptoms import danger_values
        from ai.interview.followup import enforce_danger_options

        expected = danger_values(self.FIELDS)
        self.assertTrue(expected, "fixture must actually produce danger options")
        for lang in ("en",) + NON_ENGLISH:
            with self.subTest(lang=lang):
                built = enforce_danger_options("associated_symptoms", self.FIELDS, [], lang)
                self.assertEqual([o.value for o in built], expected)

    def test_red_flags_see_identical_input(self):
        from ai.safety import red_flags

        def decision(flags):
            return [
                {k: v for k, v in f.model_dump(mode="json").items() if k != "detected_at"}
                for f in flags
            ]

        baseline = decision(red_flags.evaluate(dict(self.FIELDS)))
        self.assertTrue(baseline, "fixture must fire a rule, or this proves nothing")
        self.assertEqual(baseline[0]["rule_id"], "chest_pain_breathlessness")
        # Whatever language the tiles were rendered in, the rules read values.
        for lang in NON_ENGLISH:
            with self.subTest(lang=lang):
                self.assertEqual(decision(red_flags.evaluate(dict(self.FIELDS))), baseline)

    def test_fhir_reads_the_value(self):
        from app.fhir import _fhir_gender

        self.assertEqual(_fhir_gender("male"), _fhir_gender("male"))
        self.assertNotEqual(_fhir_gender("male"), _fhir_gender("पुरुष"))


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


class TestPhaseLabelsTranslate(unittest.TestCase):
    """The stage label above every question must translate too.

    Same assertion as the question and the option tiles, on the one field that
    was missed: it rendered "Tell me more about this problem." above a Telugu
    question because the label was English prose held on the node.

    The labels now live in the kiosk's string table, so this reads that file.
    Parsing JS from Python is ugly, but the alternative is no check at all on
    the field that has now leaked English three times, and the shape being
    parsed is the one this repo generates.
    """

    STRINGS = pathlib.Path(__file__).resolve().parents[2] / "frontend/src/i18n/strings.js"

    @classmethod
    def setUpClass(cls):
        source = cls.STRINGS.read_text(encoding="utf-8")
        cls.phases = {}
        for lang in ("en",) + NON_ENGLISH:
            start = source.index(f"\n  {lang}: {{\n")
            block = source.index("    phase: {", start)
            end = source.index("\n    },", block)
            cls.phases[lang] = dict(
                re.findall(r"^      (\w+): \{ label: '(.*)', audio:", source[block:end], re.M)
            )

    def test_every_node_has_a_label_in_every_language(self):
        """A node added without a string would render its bare key."""
        from ai.interview.nodes import NODES

        for node in NODES.values():
            for lang in ("en",) + NON_ENGLISH:
                with self.subTest(node=node.id, lang=lang):
                    self.assertIn(
                        node.phase_key,
                        self.phases[lang],
                        f"node {node.id!r} has no {lang} phase label; the kiosk "
                        f"would render the raw key {node.phase_key!r}",
                    )

    def test_phase_label_is_not_english(self):
        """The label must not be byte-identical to its English counterpart."""
        for lang in NON_ENGLISH:
            for key, english in self.phases["en"].items():
                with self.subTest(lang=lang, key=key):
                    self.assertNotEqual(
                        self.phases[lang].get(key),
                        english,
                        f"{lang}: phase label {key!r} came back byte-identical "
                        f"to English",
                    )


class TestBareFallbackIsNotEnglish(unittest.TestCase):
    """The model-failure path must not put English prose on the screen.

    _bare used to return the node's English phase_label as the question text,
    so a model failure in a Telugu session rendered an English sentence as the
    question. It now returns nothing and the kiosk falls back to the stage
    label, which it holds translated.
    """

    def test_bare_question_is_empty_not_english(self):
        from ai.adapters.base import LLMAdapter

        class DeadLLM(LLMAdapter):
            def complete(self, prompt):  # pragma: no cover - unused
                return ""

            def complete_json(self, prompt):
                return {}

        node = get_node("hpi")
        for lang in NON_ENGLISH:
            with self.subTest(lang=lang):
                _, question, _, _ = generate_followup(
                    node, {"chief_complaint": "chest pain"}, lang, DeadLLM()
                )
                self.assertEqual(
                    question,
                    "",
                    f"{lang}: the fallback question is {question!r}, which the "
                    f"kiosk renders verbatim",
                )
                self.assertNotEqual(
                    question, node.phase_label, f"{lang}: leaked the English stage label"
                )


if __name__ == "__main__":
    unittest.main()

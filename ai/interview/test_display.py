# Owner: Nikki
"""The display label must never reach anything that makes a decision.

The understanding panel was rendering canonical tokens — "1_day", "male",
"throbbing" — so a patient reading Telugu was shown English, and sometimes an
underscore. Fixing that means carrying a second string per field, and the
whole risk of doing so is that the second string leaks into the parts that are
supposed to be language-independent.

So the property under test is not "the label is pretty". It is:

    adding a display label changes NOTHING that reads `value`.

Red flags, the danger-tile rebuild, storage and the FHIR gender mapping all
key off the canonical value. If any of them ever starts seeing "ఒక రోజు"
instead of "1_day", a chest-pain red flag stops firing in six languages and
nobody finds out from the English demo.
"""

import unittest

from app.schemas import ExtractedField, FieldSource, QuestionOption

from ai.interview.display import display_for, humanise, inherited_label, label_for
from ai.interview.followup import enforce_danger_options
from ai.safety import red_flags

# The same answers, once bare and once carrying patient-language labels.
CANONICAL = {
    "chief_complaint": "chest",
    "symptom_duration": "1_day",
    "symptom_severity": "severe",
    "sex": "male",
    "associated_symptoms": ["breathlessness"],
}
LABELS = {
    "chief_complaint": "ఛాతీ",
    "symptom_duration": "ఒక రోజు",
    "symptom_severity": "తీవ్రమైన",
    "sex": "పురుషుడు",
    "associated_symptoms": "ఊపిరి ఆడకపోవడం",
}


def _fields(with_display: bool) -> list[ExtractedField]:
    return [
        ExtractedField(
            name=name,
            value=value,
            confidence=1.0,
            source=FieldSource.touch,
            display=LABELS[name] if with_display else None,
        )
        for name, value in CANONICAL.items()
    ]


class TestDisplayNeverReachesTheRules(unittest.TestCase):
    def test_stored_values_are_byte_identical(self):
        """What goes into session state and the database is the value alone."""
        bare = {f.name: f.value for f in _fields(False)}
        labelled = {f.name: f.value for f in _fields(True)}
        self.assertEqual(bare, labelled)
        self.assertEqual(labelled, CANONICAL)
        for value in labelled.values():
            self.assertNotIn(value, LABELS.values())

    def test_red_flags_are_byte_identical(self):
        """The rules must fire the same way with and without labels."""
        bare = {f.name: f.value for f in _fields(False)}
        labelled = {f.name: f.value for f in _fields(True)}
        # Everything except detected_at, which is a clock reading and differs
        # between two calls however identical the inputs.
        def decision(flags):
            return [
                {k: v for k, v in f.model_dump(mode="json").items() if k != "detected_at"}
                for f in flags
            ]

        before, after = decision(red_flags.evaluate(bare)), decision(red_flags.evaluate(labelled))
        self.assertEqual(before, after)
        self.assertTrue(before, "the fixture must actually trigger a rule, or this proves nothing")
        self.assertEqual(before[0]["rule_id"], "chest_pain_breathlessness")

    def test_danger_options_are_byte_identical(self):
        """The safety tiles are rebuilt from the value, not from what is shown."""
        bare = {f.name: f.value for f in _fields(False)}
        labelled = {f.name: f.value for f in _fields(True)}
        for language in ("en", "te", "hi"):
            with self.subTest(language=language):
                before = enforce_danger_options("associated_symptoms", bare, [], language)
                after = enforce_danger_options("associated_symptoms", labelled, [], language)
                self.assertEqual(
                    [(o.value, o.label) for o in before],
                    [(o.value, o.label) for o in after],
                )

    def test_fhir_gender_reads_the_value(self):
        """A translated sex label must not change the FHIR gender."""
        from app.fhir import _fhir_gender

        self.assertEqual(_fhir_gender(CANONICAL["sex"]), _fhir_gender("male"))
        self.assertNotEqual(_fhir_gender("male"), _fhir_gender(LABELS["sex"]))

    def test_display_is_absent_by_default(self):
        """Nothing that does not set a label gets one implicitly."""
        f = ExtractedField(
            name="symptom_duration", value="1_day", confidence=1.0, source=FieldSource.speech
        )
        self.assertIsNone(f.display)


class TestDisplayStrings(unittest.TestCase):
    def test_tokens_are_opened_out(self):
        """No underscore may reach a patient."""
        self.assertEqual(humanise("1_day"), "1 day")
        self.assertEqual(humanise("few_days"), "Few days")
        self.assertEqual(humanise(["1_day", "weeks"]), "1 day, Weeks")

    def test_sentence_case_does_not_destroy_the_rest(self):
        self.assertEqual(humanise("MRI scan"), "MRI scan")

    def test_tapped_label_wins_over_the_token(self):
        """When the patient tapped a tile, that tile's words are what we show."""
        options = [
            QuestionOption(value="1_day", label="ఒక రోజు"),
            QuestionOption(value="weeks", label="వారాలు"),
        ]
        self.assertEqual(label_for("1_day", options), "ఒక రోజు")
        self.assertEqual(display_for("1_day", options), "ఒక రోజు")

    def test_unmatched_value_falls_back_rather_than_guessing(self):
        options = [QuestionOption(value="1_day", label="ఒక రోజు")]
        self.assertIsNone(label_for("weeks", options))
        self.assertEqual(display_for("weeks", options), "Weeks")

    def test_partly_matched_list_does_not_half_translate(self):
        """A list rendered half in each language reads as a bug, not an answer."""
        options = [QuestionOption(value="a", label="ఏ")]
        self.assertIsNone(label_for(["a", "b"], options))

    def test_a_derived_field_borrows_its_source_label(self):
        """symptom_onset is symptom_duration's answer; it reads the same."""
        values = {"symptom_duration": "1_day", "symptom_onset": "1_day"}
        labels = {"symptom_duration": "ఒక రోజు"}
        self.assertEqual(
            inherited_label("symptom_onset", "1_day", values, labels), "ఒక రోజు"
        )

    def test_a_different_answer_borrows_nothing(self):
        values = {"symptom_duration": "1_day", "symptom_severity": "mild"}
        labels = {"symptom_duration": "ఒక రోజు"}
        self.assertIsNone(inherited_label("symptom_severity", "mild", values, labels))

    def test_no_options_at_all(self):
        self.assertEqual(display_for("1_day", []), "1 day")
        self.assertEqual(display_for("1_day", None), "1 day")


if __name__ == "__main__":
    unittest.main()

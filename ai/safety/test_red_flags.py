# Owner: Nikki
"""Unit tests for ai.safety.red_flags. No network access required."""

import time
import unittest

from ai.safety.red_flags import evaluate


def _rule_ids(fields: dict) -> set[str]:
    return {flag.rule_id for flag in evaluate(fields)}


class TestChestPain(unittest.TestCase):
    def test_chest_pain_with_breathlessness_fires(self):
        fields = {"chief_complaint": "chest pain", "associated_symptoms": ["breathlessness"]}
        self.assertIn("chest_pain_breathlessness", _rule_ids(fields))

    def test_chest_pain_radiating_to_arm_fires(self):
        fields = {"chief_complaint": "chest pain", "symptom_radiation": "left arm"}
        self.assertIn("chest_pain_radiation", _rule_ids(fields))

    def test_chest_pain_radiating_to_jaw_fires(self):
        fields = {"chief_complaint": "chest pain", "symptom_radiation": "jaw"}
        self.assertIn("chest_pain_radiation", _rule_ids(fields))

    def test_chest_pain_alone_does_not_fire_either_rule(self):
        fields = {"chief_complaint": "chest pain"}
        ids = _rule_ids(fields)
        self.assertNotIn("chest_pain_breathlessness", ids)
        self.assertNotIn("chest_pain_radiation", ids)

    def test_breathlessness_without_chest_pain_does_not_fire(self):
        fields = {"chief_complaint": "breathlessness"}
        self.assertNotIn("chest_pain_breathlessness", _rule_ids(fields))


class TestFastStrokeSigns(unittest.TestCase):
    def test_facial_droop_fires(self):
        self.assertIn("fast_stroke_signs", _rule_ids({"associated_symptoms": ["facial droop"]}))

    def test_arm_weakness_fires(self):
        self.assertIn("fast_stroke_signs", _rule_ids({"ros_neurological": ["weakness in the arm"]}))

    def test_slurred_speech_fires(self):
        self.assertIn("fast_stroke_signs", _rule_ids({"chief_complaint": "slurred speech since morning"}))

    def test_unrelated_neuro_complaint_does_not_fire(self):
        self.assertNotIn("fast_stroke_signs", _rule_ids({"chief_complaint": "headache"}))


class TestAlteredConsciousness(unittest.TestCase):
    def test_boolean_field_fires(self):
        self.assertIn("altered_consciousness", _rule_ids({"altered_consciousness": True}))

    def test_text_mention_fires(self):
        self.assertIn("altered_consciousness", _rule_ids({"chief_complaint": "found unresponsive"}))

    def test_false_boolean_does_not_fire(self):
        self.assertNotIn("altered_consciousness", _rule_ids({"altered_consciousness": False}))


class TestActiveBleeding(unittest.TestCase):
    def test_active_bleeding_fires(self):
        self.assertIn("active_bleeding", _rule_ids({"chief_complaint": "active bleeding from wound"}))

    def test_minor_bleeding_mention_does_not_fire(self):
        self.assertNotIn("active_bleeding", _rule_ids({"chief_complaint": "small cut, bleeding stopped"}))


class TestSevereBreathlessnessAtRest(unittest.TestCase):
    def test_all_three_terms_fire(self):
        fields = {"chief_complaint": "severe breathlessness at rest"}
        self.assertIn("severe_breathlessness_at_rest", _rule_ids(fields))

    def test_breathlessness_on_exertion_only_does_not_fire(self):
        fields = {"chief_complaint": "breathlessness on climbing stairs"}
        self.assertNotIn("severe_breathlessness_at_rest", _rule_ids(fields))


class TestSuicidalIdeation(unittest.TestCase):
    def test_boolean_field_fires(self):
        self.assertIn("suicidal_ideation", _rule_ids({"suicidal_ideation": True}))

    def test_text_mention_fires(self):
        self.assertIn("suicidal_ideation", _rule_ids({"chief_complaint": "says he wants to end my life"}))

    def test_unrelated_complaint_does_not_fire(self):
        self.assertNotIn("suicidal_ideation", _rule_ids({"chief_complaint": "feeling low lately"}))


class TestHighFeverNeckStiffness(unittest.TestCase):
    def test_both_together_fire(self):
        fields = {"chief_complaint": "high fever", "ros_general": ["neck stiffness"]}
        self.assertIn("high_fever_neck_stiffness", _rule_ids(fields))

    def test_fever_alone_does_not_fire(self):
        self.assertNotIn("high_fever_neck_stiffness", _rule_ids({"chief_complaint": "high fever"}))


class TestPregnancyComplication(unittest.TestCase):
    def test_pregnant_with_bleeding_fires(self):
        fields = {"is_pregnant": True, "chief_complaint": "bleeding"}
        self.assertIn("pregnancy_complication", _rule_ids(fields))

    def test_pregnant_with_severe_abdominal_pain_fires(self):
        fields = {"chief_complaint": "pregnant, severe abdominal pain"}
        self.assertIn("pregnancy_complication", _rule_ids(fields))

    def test_pregnant_without_complication_does_not_fire(self):
        self.assertNotIn("pregnancy_complication", _rule_ids({"is_pregnant": True, "chief_complaint": "routine checkup"}))

    def test_bleeding_without_pregnancy_does_not_fire_this_rule(self):
        self.assertNotIn("pregnancy_complication", _rule_ids({"chief_complaint": "bleeding"}))


class TestEvaluateGeneral(unittest.TestCase):
    def test_empty_fields_returns_no_flags(self):
        self.assertEqual(evaluate({}), [])

    def test_unrelated_fields_return_no_flags(self):
        fields = {"chief_complaint": "mild rash on arm", "symptom_duration": "2 days"}
        self.assertEqual(evaluate(fields), [])

    def test_multiple_rules_can_fire_at_once(self):
        fields = {"chief_complaint": "chest pain", "associated_symptoms": ["breathlessness"], "symptom_radiation": "left arm"}
        ids = _rule_ids(fields)
        self.assertIn("chest_pain_breathlessness", ids)
        self.assertIn("chest_pain_radiation", ids)

    def test_ignores_fields_outside_the_symptom_allowlist(self):
        # "notes" isn't a field this module reads — must not be scanned.
        fields = {"notes": "patient mentioned suicidal ideation to a relative"}
        self.assertEqual(evaluate(fields), [])

    def test_runs_in_under_a_millisecond(self):
        fields = {
            "chief_complaint": "chest pain",
            "symptom_site": "chest",
            "symptom_radiation": "left arm",
            "associated_symptoms": ["breathlessness", "sweating", "nausea"],
            "ros_general": ["fever", "fatigue"],
        }
        iterations = 1000
        start = time.perf_counter()
        for _ in range(iterations):
            evaluate(fields)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed / iterations, 0.001)


if __name__ == "__main__":
    unittest.main()

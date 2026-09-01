# Owner: Nikki
"""Unit tests for ai.knowledge.danger_symptoms and its enforcement.

These options are the only danger signs a patient answering by touch can
report, so what is in the list is a safety property, not a wording choice.
No network access and no LLM.
"""

import unittest

from app.schemas import QuestionOption

from ai.interview.followup import enforce_danger_options
from ai.knowledge.danger_symptoms import category_for, danger_values
from ai.safety.red_flags import evaluate


def _ids(fields):
    return {flag.rule_id for flag in evaluate(fields)}


class TestCategory(unittest.TestCase):
    def test_back_pain(self):
        self.assertEqual(category_for({"chief_complaint": "back pain"}), "back_pain")

    def test_chest_pain(self):
        self.assertEqual(category_for({"chief_complaint": "chest pain"}), "chest_pain")

    def test_breathlessness_beats_its_chest_site(self):
        # body_regions files breathlessness under the chest; the danger list
        # for a breathless patient is not the chest-pain one.
        self.assertEqual(category_for({"chief_complaint": "breathlessness"}), "breathlessness")

    def test_site_alone_is_enough(self):
        self.assertEqual(category_for({"symptom_site": "abdomen"}), "abdominal_pain")

    def test_unknown_complaint_has_no_category(self):
        self.assertEqual(category_for({"chief_complaint": "i feel unwell"}), "")


class TestOptions(unittest.TestCase):
    def test_back_pain_offers_leg_weakness_and_bladder_change(self):
        values = danger_values({"chief_complaint": "back pain"})
        self.assertIn("leg_weakness", values)
        self.assertIn("loss_of_bladder_or_bowel_control", values)

    def test_back_pain_does_not_offer_breathlessness(self):
        self.assertNotIn("breathlessness", danger_values({"chief_complaint": "back pain"}))

    def test_chest_pain_offers_breathlessness(self):
        self.assertIn("breathlessness", danger_values({"chief_complaint": "chest pain"}))

    def test_none_is_always_last(self):
        for complaint in ("back pain", "chest pain", "headache", "i feel unwell"):
            self.assertEqual(danger_values({"chief_complaint": complaint})[-1], "none")

    def test_unknown_complaint_falls_back_to_a_generic_list_not_nothing(self):
        values = danger_values({"chief_complaint": "i feel unwell"})
        self.assertGreater(len(values), 1)
        self.assertIn("chest_pain", values)

    def test_every_list_fits_the_option_cap(self):
        from ai.interview.followup import MAX_OPTIONS

        for complaint in ("back pain", "chest pain", "headache", "stomach pain",
                          "breathlessness", "fever", "unknown thing"):
            self.assertLessEqual(len(danger_values({"chief_complaint": complaint})), MAX_OPTIONS)


class TestEnforcement(unittest.TestCase):
    """The model translates. It does not choose."""

    def test_model_invented_option_is_discarded(self):
        fields = {"chief_complaint": "back pain"}
        # Exactly the reported bug: the model offers breathlessness to a
        # back-pain patient.
        got = enforce_danger_options(
            "associated_symptoms",
            fields,
            [QuestionOption(value="breathlessness", label="Saans phoolna")],
        )
        self.assertNotIn("breathlessness", [o.value for o in got])
        self.assertEqual([o.value for o in got], danger_values(fields))

    def test_model_translation_is_kept_for_options_we_asked_for(self):
        got = enforce_danger_options(
            "associated_symptoms",
            {"chief_complaint": "back pain"},
            [QuestionOption(value="leg_weakness", label="पैरों में कमजोरी")],
        )
        self.assertEqual(got[0].label, "पैरों में कमजोरी")

    def test_omitted_options_come_back_in_english_rather_than_missing(self):
        got = enforce_danger_options("associated_symptoms", {"chief_complaint": "back pain"}, [])
        self.assertEqual([o.value for o in got], danger_values({"chief_complaint": "back pain"}))
        self.assertTrue(all(o.label for o in got))

    def test_other_fields_are_left_alone(self):
        opts = [QuestionOption(value="mild", label="Mild")]
        self.assertEqual(enforce_danger_options("symptom_severity", {}, opts), opts)


class TestTappedValuesStillFireRules(unittest.TestCase):
    """A tapped tile stores a canonical token. The rules must still match it."""

    def test_chest_pain_with_tapped_breathlessness(self):
        fields = {"chief_complaint": "chest pain", "associated_symptoms": ["breathlessness"]}
        self.assertIn("chest_pain_breathlessness", _ids(fields))

    def test_tapped_radiation_token_fires(self):
        fields = {
            "chief_complaint": "chest pain",
            "associated_symptoms": ["pain_radiating_to_arm_or_jaw"],
        }
        self.assertIn("chest_pain_radiation", _ids(fields))

    def test_tapped_one_sided_weakness_token_fires_stroke(self):
        fields = {"chief_complaint": "headache", "associated_symptoms": ["one_sided_weakness"]}
        self.assertIn("fast_stroke_signs", _ids(fields))

    def test_tapped_bladder_loss_with_back_pain_fires_cauda_equina(self):
        fields = {
            "chief_complaint": "back pain",
            "symptom_site": "back",
            "associated_symptoms": ["loss_of_bladder_or_bowel_control"],
        }
        self.assertIn("cauda_equina", _ids(fields))

    def test_bladder_loss_without_back_pain_does_not_fire_cauda_equina(self):
        self.assertNotIn(
            "cauda_equina",
            _ids({"chief_complaint": "fever", "associated_symptoms": ["loss_of_bladder_or_bowel_control"]}),
        )

    def test_tapped_vomiting_blood_fires(self):
        self.assertIn(
            "vomiting_blood",
            _ids({"chief_complaint": "abdominal pain", "associated_symptoms": ["vomiting_blood"]}),
        )

    def test_tapped_coughing_blood_fires(self):
        self.assertIn(
            "coughing_blood",
            _ids({"chief_complaint": "breathlessness", "associated_symptoms": ["coughing_blood"]}),
        )

    def test_ros_screen_answers_reach_the_rules(self):
        # ros_screen was missing from the fields red_flags reads at all.
        self.assertIn("fast_stroke_signs", _ids({"ros_screen": ["slurred_speech"]}))


if __name__ == "__main__":
    unittest.main()

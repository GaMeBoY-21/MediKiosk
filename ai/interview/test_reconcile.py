# Owner: Nikki
"""Unit tests for ai.interview.reconcile and the per-field ask cap.

No network access and no LLM: everything here is the deterministic half of the
interview, which is the half that has to hold when the model does not.
"""

import unittest

from ai.interview.nodes import get_node
from ai.interview.reconcile import derive_fields, reconcile
from ai.interview.state_machine import (
    MAX_FIELD_ASKS,
    next_node,
    record_field_ask,
    unfilled_fields,
)
from ai.knowledge.body_regions import duration_token, site_for_complaint


class TestSiteLookup(unittest.TestCase):
    def test_back_pain_names_the_back(self):
        self.assertEqual(site_for_complaint("back pain"), "back")

    def test_chest_pain_names_the_chest(self):
        self.assertEqual(site_for_complaint("chest pain for two days"), "chest")

    def test_headache_names_the_head(self):
        self.assertEqual(site_for_complaint("headache"), "head")

    def test_tapped_tile_value_resolves(self):
        # The complaint screen sends canonical tile values, not sentences.
        self.assertEqual(site_for_complaint("back"), "back")
        self.assertEqual(site_for_complaint("stomach"), "abdomen")

    def test_longest_phrase_wins(self):
        self.assertEqual(site_for_complaint("lower back pain since morning"), "back")

    def test_fever_names_no_site(self):
        self.assertEqual(site_for_complaint("fever"), "")

    def test_joint_pain_names_no_site_so_which_joint_is_still_asked(self):
        self.assertEqual(site_for_complaint("joint pain"), "")
        self.assertEqual(site_for_complaint("joints"), "")

    def test_unknown_complaint_derives_nothing(self):
        self.assertEqual(site_for_complaint("something is not right"), "")

    def test_word_boundaries_stop_false_matches(self):
        # "ear" must not match inside "heart", "arm" must not match "warm".
        self.assertNotEqual(site_for_complaint("my heart races"), "ear")
        self.assertNotEqual(site_for_complaint("feeling warm"), "arm")


class TestDurationLookup(unittest.TestCase):
    def test_numeric_days(self):
        self.assertEqual(duration_token("for 2 days"), "2_days")

    def test_word_numbers(self):
        self.assertEqual(duration_token("chest pain for two days"), "2_days")

    def test_singular_unit_for_one(self):
        self.assertEqual(duration_token("1 day"), "1_day")

    def test_today(self):
        self.assertEqual(duration_token("back pain since today"), "today")

    def test_yesterday(self):
        self.assertEqual(duration_token("since yesterday"), "1_day")

    def test_no_duration(self):
        self.assertEqual(duration_token("back pain"), "")


class TestDeriveFields(unittest.TestCase):
    def test_back_pain_fills_the_site(self):
        self.assertEqual(derive_fields({"chief_complaint": "back pain"})["symptom_site"], "back")

    def test_chest_pain_for_two_days_fills_site_and_onset(self):
        derived = derive_fields({"chief_complaint": "chest pain for two days"})
        self.assertEqual(derived["symptom_site"], "chest")
        self.assertEqual(derived["symptom_onset"], "2_days")
        self.assertEqual(derived["symptom_duration"], "2_days")

    def test_duration_answer_also_answers_onset(self):
        # The same sentence to the patient. Asking both is the same re-ask
        # loop wearing a different label.
        derived = derive_fields({"chief_complaint": "back pain", "symptom_duration": "3_days"})
        self.assertEqual(derived["symptom_onset"], "3_days")

    def test_never_overwrites_what_the_patient_said(self):
        fields = {"chief_complaint": "back pain", "symptom_site": "neck"}
        self.assertNotIn("symptom_site", derive_fields(fields))
        self.assertEqual(reconcile(fields)["symptom_site"], "neck")

    def test_empty_value_is_a_hole_not_an_answer(self):
        fields = {"chief_complaint": "back pain", "symptom_site": ""}
        self.assertEqual(derive_fields(fields)["symptom_site"], "back")

    def test_derives_nothing_from_an_unknown_complaint(self):
        self.assertEqual(derive_fields({"chief_complaint": "i feel unwell"}), {})

    def test_reconcile_does_not_mutate_its_input(self):
        fields = {"chief_complaint": "back pain"}
        reconcile(fields)
        self.assertNotIn("symptom_site", fields)


class TestNoReAsk(unittest.TestCase):
    """The bug this whole block exists for."""

    def _state(self, fields):
        return {"fields": dict(fields), "follow_up_counts": {}, "field_ask_counts": {}}

    def test_back_pain_since_today_is_never_asked_where_it_hurts(self):
        state = self._state(
            reconcile(
                {
                    "patient_name": "Asha",
                    "age": 40,
                    "sex": "female",
                    "consent_given": "yes",
                    "chief_complaint": "back pain since today",
                }
            )
        )
        # Every field the interview would still put to this patient, across
        # every stage, until nothing is left to ask.
        asked = []
        for _ in range(60):
            node = next_node(state)
            if node is None:
                break
            remaining = unfilled_fields(node, state)
            if not remaining:
                break
            field_name = remaining[0]
            asked.append(field_name)
            # Simulate the patient answering it.
            state["fields"][field_name] = "answered"
            state["fields"].update(derive_fields(state["fields"]))

        self.assertNotIn("symptom_site", asked)
        self.assertNotIn("symptom_duration", asked)
        self.assertNotIn("symptom_onset", asked)

    def test_a_complaint_with_no_site_still_gets_asked_where(self):
        state = self._state(reconcile({"chief_complaint": "joint pain"}))
        hpi = get_node("hpi")
        self.assertIn("symptom_site", unfilled_fields(hpi, state))


class TestFieldAskCap(unittest.TestCase):
    def test_two_asks_then_the_interview_moves_on(self):
        state = {
            "fields": {"chief_complaint": "joint pain"},
            "follow_up_counts": {},
            "field_ask_counts": {},
        }
        hpi = get_node("hpi")
        self.assertIn("symptom_site", unfilled_fields(hpi, state))

        for _ in range(MAX_FIELD_ASKS):
            record_field_ask(state, "symptom_site")

        self.assertNotIn("symptom_site", unfilled_fields(hpi, state))

    def test_a_capped_field_does_not_stall_the_whole_interview(self):
        state = {"fields": {}, "follow_up_counts": {}, "field_ask_counts": {}}
        seen = set()
        for _ in range(200):
            node = next_node(state)
            if node is None:
                break
            remaining = unfilled_fields(node, state)
            if not remaining:
                # Node satisfied only by caps; force progress the way the
                # per-node follow-up counter would.
                state["follow_up_counts"][node.id] = node.max_follow_ups
                continue
            seen.add(remaining[0])
            record_field_ask(state, remaining[0])
        else:
            self.fail("interview never completed: a field re-ask loop is still possible")

        self.assertIsNone(next_node(state))
        # Nothing was ever answered, so every field ends up unfilled — the
        # point is the interview ENDED rather than looping forever.
        self.assertTrue(seen)


if __name__ == "__main__":
    unittest.main()

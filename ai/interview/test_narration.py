# Owner: Nikki
"""The opening description fills fields across stages, and never drives flow.

The interview used to walk a fixed scaffold no matter what the patient had
already volunteered: "chest pain for two days, it goes to my left arm, worse
when I walk" was followed by questions asking where it hurts, when it started,
whether it spreads and what makes it worse. Four questions the patient had
just answered, in a queue, out loud.

What is asserted here is the boundary, not the cleverness: extraction may fill
anything the patient said, and NOTHING about what happens next is the model's
to decide.
"""

import unittest

from ai.adapters.base import LLMAdapter, MalformedOutputError
from ai.interview.extraction import extract_narration, narration_fields


class _LLM(LLMAdapter):
    def __init__(self, payload=None, raises=None):
        self.payload = payload if payload is not None else {"fields": []}
        self.raises = raises
        self.prompt = ""

    def complete(self, prompt):  # pragma: no cover - unused
        return ""

    def complete_json(self, prompt):
        self.prompt = prompt
        if self.raises:
            raise self.raises
        return self.payload


class TestNarrationScope(unittest.TestCase):
    def test_it_spans_stages_not_just_one(self):
        """The whole point: one sentence, fields from several stages."""
        fields = narration_fields()
        self.assertIn("chief_complaint", fields)      # chief_complaint stage
        self.assertIn("symptom_radiation", fields)    # hpi stage
        self.assertIn("past_medical_conditions", fields)
        self.assertIn("smoking_status", fields)       # personal stage
        self.assertGreater(len(fields), 15)

    def test_it_excludes_what_a_patient_does_not_narrate(self):
        """Identity and consent are collected on their own screens."""
        fields = narration_fields()
        for name in ("patient_name", "age", "sex", "consent_given", "patient_confirmed"):
            self.assertNotIn(name, fields)

    def test_the_scope_is_derived_from_the_nodes(self):
        """A field added to a clinical node becomes narratable automatically."""
        from ai.interview.nodes import NODES

        fields = narration_fields()
        for name in NODES["hpi"].required_fields:
            self.assertIn(name, fields)


class TestTheModelCannotDriveTheFlow(unittest.TestCase):
    def test_a_field_nobody_allowed_is_discarded(self):
        """A hallucinated field must not reach the record."""
        llm = _LLM({"fields": [
            {"name": "chief_complaint", "value": "chest pain", "confidence": 0.9},
            {"name": "next_node", "value": "documents", "confidence": 0.99},
            {"name": "patient_confirmed", "value": True, "confidence": 0.99},
        ]})
        got = {f.name for f in extract_narration("chest pain", llm)}
        self.assertEqual(got, {"chief_complaint"})

    def test_low_confidence_is_dropped_rather_than_guessed(self):
        llm = _LLM({"fields": [
            {"name": "chief_complaint", "value": "chest pain", "confidence": 0.9},
            {"name": "symptom_severity", "value": "severe", "confidence": 0.1},
        ]})
        got = {f.name for f in extract_narration("chest pain", llm)}
        self.assertEqual(got, {"chief_complaint"})


class TestUnusableNarrationFallsThrough(unittest.TestCase):
    """A silent or unusable description must not be an error.

    The patient simply gets the questions they would have got before this
    screen existed.
    """

    def test_empty_transcript_extracts_nothing_and_does_not_call_the_model(self):
        llm = _LLM()
        self.assertEqual(extract_narration("", llm), [])
        self.assertEqual(extract_narration("   ", llm), [])
        self.assertEqual(llm.prompt, "", "an empty narration must not spend a request")

    def test_malformed_model_output_is_not_an_exception(self):
        llm = _LLM(raises=MalformedOutputError("not json"))
        self.assertEqual(extract_narration("chest pain", llm), [])

    def test_a_non_list_payload_is_survived(self):
        self.assertEqual(extract_narration("chest pain", _LLM({"fields": "nope"})), [])
        self.assertEqual(extract_narration("chest pain", _LLM({})), [])


if __name__ == "__main__":
    unittest.main()

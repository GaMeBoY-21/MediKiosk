# Owner: Nikki
"""What the physician console shows must match what was recorded.

Two properties, both of which failed on a real screen:

  IDENTITY  the queue row and the case header describe the same patient. They
            used to disagree — the queue fell back to the clinical record and
            the header fell back to a fixture without reading the record — so
            one session appeared as "NIKKI 21 male" in the list and
            "Lakshmi Devi 65 F" in the header. A doctor was reading a name
            that belonged to nobody in the room.

  SECTIONS  a session with N recorded fields renders those fields. They used
            to render "Not recorded" for everything, because the summary was
            assembled from the in-memory session store rather than from the
            persisted record, and the store is empty after any restart.

These live in ai/ because that is the suite that actually runs
(`python3 -m unittest discover -s ai`). They import from app/ only.
"""

import unittest

from app import fixtures, models
from app.routers.physician import _identity


class _Row:
    """The columns of models.Session that identity reads."""

    def __init__(self, patient_name=None, age=None, sex=None, abha_id=None):
        self.patient_name = patient_name
        self.age = age
        self.sex = sex
        self.abha_id = abha_id
        self.session_id = "mk-test"


class TestOneIdentitySource(unittest.TestCase):
    def test_queue_and_header_agree_on_a_real_patient(self):
        """The exact case from the screenshot: the record has the answers."""
        history = {"patient_name": "NIKKI", "age": 21, "sex": "male"}
        row = _Row()  # nothing ever writes these columns

        queue_patient, _ = _identity(row, history)
        header_patient, mocked = _identity(row, history)

        self.assertEqual(queue_patient.name, header_patient.name)
        self.assertEqual(queue_patient.age, header_patient.age)
        self.assertEqual(queue_patient.sex, header_patient.sex)
        self.assertEqual(queue_patient.name, "NIKKI", "the patient's real answer must win")
        self.assertEqual(queue_patient.age, 21)
        self.assertNotIn("name", mocked, "a real name must not be flagged as demo data")
        self.assertNotIn("age", mocked)

    def test_the_fixture_never_overrides_a_real_answer(self):
        history = {"patient_name": "NIKKI", "age": 21, "sex": "male"}
        patient, _ = _identity(_Row(), history)
        self.assertNotEqual(patient.name, fixtures.DEMO_PATIENT["name"])
        self.assertNotEqual(patient.age, fixtures.DEMO_PATIENT["age"])

    def test_demo_values_only_fill_what_the_patient_did_not_give(self):
        """The badge must name the invented fields, not label the whole record."""
        history = {"patient_name": "NIKKI", "age": 21}  # no sex, no abha
        patient, mocked = _identity(_Row(), history)

        self.assertEqual(patient.name, "NIKKI")
        self.assertEqual(sorted(mocked), ["abha", "sex"], "only the missing ones")
        self.assertEqual(patient.sex, fixtures.DEMO_PATIENT["sex"])

    def test_nothing_recorded_at_all_is_flagged_completely(self):
        patient, mocked = _identity(_Row(), {})
        self.assertEqual(sorted(mocked), ["abha", "age", "name", "sex"])
        self.assertEqual(patient.name, fixtures.DEMO_PATIENT["name"])

    def test_the_session_row_wins_over_the_record(self):
        """If the column is ever populated it is the more specific answer."""
        row = _Row(patient_name="From Row", age=30)
        patient, mocked = _identity(row, {"patient_name": "From Record", "age": 21})
        self.assertEqual(patient.name, "From Row")
        self.assertEqual(patient.age, 30)
        self.assertEqual(mocked, ["sex", "abha"])

    def test_age_zero_is_a_real_age_not_a_missing_one(self):
        """An infant is not an unrecorded patient."""
        patient, mocked = _identity(_Row(), {"age": 0, "patient_name": "Baby"})
        self.assertEqual(patient.age, 0)
        self.assertNotIn("age", mocked)


class TestEveryRecordedFieldIsRendered(unittest.TestCase):
    """A session with N recorded fields must show those N.

    The fifth time data has been stored correctly and dropped before it
    reached the screen, so this asserts the property directly rather than the
    mechanism: take a full record, render it, and look for every value.
    """

    RECORD = {
        "patient_name": "NIKKI",
        "age": 21,
        "sex": "male",
        "consent_given": "yes",
        "chief_complaint": "chest",
        "symptom_site": "chest",
        "symptom_duration": "2_days",
        "symptom_onset": "2_days",
        "symptom_character": "burning",
        "symptom_severity": "severe",
        "symptom_timing": "morning",
        "associated_symptoms": ["breathlessness"],
        "ros_screen": "none",
        "past_medical_conditions": "diabetes",
        "past_surgeries": "appendectomy",
        "current_medications": "metformin",
        "known_allergies": "penicillin",
        "family_history": "heart disease",
        "smoking_status": "never",
        "alcohol_use": "occasionally",
        "diet": "vegetarian",
    }

    def test_every_clinical_field_maps_to_a_section(self):
        """A field with nowhere to go is a field that vanishes."""
        from ai.summary.sections import FIELD_TO_SECTION, section_for

        # Identity, consent and the document flags belong elsewhere on screen.
        elsewhere = {"patient_name", "age", "sex", "consent_given"}
        for name in self.RECORD:
            if name in elsewhere:
                continue
            with self.subTest(field=name):
                self.assertIsNotNone(
                    section_for(name),
                    f"{name} has no section, so it would never be rendered",
                )
        self.assertTrue(FIELD_TO_SECTION, "the mapping must not be empty")

    def test_a_blank_summary_still_renders_every_recorded_answer(self):
        """The model wrote nothing — the doctor must still see the record."""
        from app.schemas import ClinicalSummary
        from ai.summary.sections import fill_missing

        summary = fill_missing(ClinicalSummary(session_id="mk-test"), self.RECORD)
        rendered = " ".join(
            [summary.chief_complaint or "", summary.hpi_narrative or ""]
            + [str(v) for v in (summary.sections or {}).values()]
        ).lower()

        missing = []
        for name, value in self.RECORD.items():
            if name in {"patient_name", "age", "sex", "consent_given"}:
                continue
            needle = (value[0] if isinstance(value, list) else str(value)).lower()
            needle = needle.replace("_", " ")
            if needle not in rendered:
                missing.append(f"{name}={value!r}")
        self.assertEqual(missing, [], f"recorded but not rendered: {missing}")

    def test_sections_the_model_wrote_are_not_overwritten(self):
        """Prose beats a field list; the mapping is only a floor."""
        from app.schemas import ClinicalSummary
        from ai.summary.sections import fill_missing

        summary = ClinicalSummary(
            session_id="mk-test",
            chief_complaint="Burning chest pain for two days.",
            sections={"personal": "Non-smoker, vegetarian."},
        )
        fill_missing(summary, self.RECORD)
        self.assertEqual(summary.chief_complaint, "Burning chest pain for two days.")
        self.assertEqual(summary.sections["personal"], "Non-smoker, vegetarian.")

    def test_not_recorded_still_means_not_recorded(self):
        """An empty record must not invent content."""
        from app.schemas import ClinicalSummary
        from ai.summary.sections import fill_missing

        summary = fill_missing(ClinicalSummary(session_id="mk-test"), {})
        self.assertIsNone(summary.chief_complaint)
        self.assertIsNone(summary.hpi_narrative)
        self.assertEqual({k: v for k, v in (summary.sections or {}).items() if v}, {})

    def test_a_field_added_to_a_node_lands_in_that_nodes_section(self):
        """The mapping is derived, so it cannot drift from the interview."""
        from ai.interview.nodes import NODES
        from ai.summary.sections import NODE_TO_SECTION, section_for

        for node_id, section in NODE_TO_SECTION.items():
            for field in NODES[node_id].required_fields:
                with self.subTest(node=node_id, field=field):
                    self.assertEqual(section_for(field), section)


if __name__ == "__main__":
    unittest.main()

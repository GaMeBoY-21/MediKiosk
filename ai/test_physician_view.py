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


class TestDocumentTimelineIsHonest(unittest.TestCase):
    """A document the patient never uploaded must never appear.

    The console showed a lipid profile and an HbA1c for sessions with no
    upload at all, because _build_summary fell back to fixtures.DEMO_DOCUMENTS
    when the query came back empty. Invented lab values sitting under a real
    patient's name, unmarked, is the worst thing a clinical screen can do.
    """

    def test_the_demo_documents_are_not_a_render_time_fallback(self):
        import inspect

        from app.routers import summary as summary_router

        source = inspect.getsource(summary_router._build_summary)
        code = "\n".join(
            line for line in source.splitlines() if not line.strip().startswith("#")
        )
        self.assertNotIn(
            "DEMO_DOCUMENTS",
            code,
            "a session with no upload would show documents the patient never gave",
        )


class TestDocumentImageIsProtected(unittest.TestCase):
    """The uploaded image is PHI and must never be reachable without a doctor.

    Verified live with curl as well (401 unauthenticated, 401 with a bad
    token, 200 for a clinician). This is the regression guard: it fails if the
    clinician dependency is ever dropped from the route, which is the change
    that would quietly expose patient documents.
    """

    def _route(self, path: str, method: str = "GET"):
        from fastapi.routing import APIRoute

        from app.main import app

        for r in app.routes:
            if isinstance(r, APIRoute) and r.path == path and method in r.methods:
                return r
        # Routers included with a prefix are not flattened in this FastAPI
        # version; fall back to the OpenAPI schema for existence.
        return None

    def _dependency_names(self, path: str, method: str = "GET"):
        import inspect

        from app.routers import physician

        fn = {
            ("/document/{doc_id}", "GET"): physician.fetch_document_image,
            ("/{session_id}/document", "POST"): physician.attach_clinician_document,
        }[(path, method)]
        return {
            p.default.dependency.__name__
            for p in inspect.signature(fn).parameters.values()
            if hasattr(p.default, "dependency")
        }

    def test_serving_an_image_requires_a_clinician(self):
        self.assertIn("require_clinician", self._dependency_names("/document/{doc_id}"))

    def test_attaching_a_document_requires_a_clinician(self):
        self.assertIn(
            "require_clinician", self._dependency_names("/{session_id}/document", "POST")
        )

    def test_both_document_routes_are_registered(self):
        from app.main import app

        paths = app.openapi()["paths"]
        self.assertIn("/api/physician/document/{doc_id}", paths)
        self.assertIn("/api/physician/{session_id}/document", paths)

    def test_reading_an_image_writes_an_audit_row(self):
        """Every PHI read is audited, this one included."""
        import inspect

        from app.routers import physician

        src = inspect.getsource(physician.fetch_document_image)
        self.assertIn("write_audit", src)
        self.assertIn("document.read", src)

    def test_attaching_is_marked_as_clinician_uploaded(self):
        """A doctor's prescription must not look like something the patient brought."""
        import inspect

        from app.routers import physician

        src = inspect.getsource(physician.attach_clinician_document)
        self.assertIn('uploaded_by="clinician"', src)
        self.assertIn("document.attach", src)


class TestTimelineIsReadLive(unittest.TestCase):
    """The document timeline comes from the uploads table, not the summary.

    `summary.document_timeline` is a snapshot written when the summary was
    generated. Two things routinely happen afterwards and were invisible in
    it: extraction finishing (the seeded lab report is summarised within a
    second of upload and extracted several seconds later, so the console
    showed it with zero findings while the database held seven), and a
    clinician attaching a prescription during the consultation, which by
    definition arrives after the summary exists.

    Same fault as the summary being read from the session store rather than
    the persisted record: a stale copy standing in for the live row.
    """

    def test_the_case_response_does_not_read_the_summary_snapshot(self):
        import inspect

        from app.routers import physician

        src = inspect.getsource(physician._case_response)
        self.assertNotIn("summary.document_timeline", src)
        self.assertIn("documents_for(db", src)

    def test_documents_for_queries_the_uploads_table(self):
        import inspect

        from app.routers import physician

        src = inspect.getsource(physician._document_rows)
        self.assertIn("models.DocumentUpload", src)

    def test_the_bundle_and_the_timeline_share_one_query(self):
        """Otherwise the FHIR push and the screen can disagree about what exists."""
        import inspect

        from app.routers import physician

        for fn in (physician._bundle_for, physician._case_response):
            self.assertIn("_document_rows(db", inspect.getsource(fn).replace("documents_for(db", "_document_rows(db"))


class TestOutboundSharingRespectsConsent(unittest.TestCase):
    """Block 1's consent governs the bundle, documents included.

    Verified live: A-44 (consented) returns 200 with both DocumentReference
    entries; A-43 (refused) returns 403 and writes an fhir.blocked audit row.
    """

    def test_the_bundle_route_checks_sharing_consent(self):
        import inspect

        from app.routers import physician

        src = inspect.getsource(physician.fetch_fhir)
        self.assertIn("sharing_consent(db", src)
        self.assertIn("403", src.replace("HTTP_403_FORBIDDEN", "403"))

    def test_a_refusal_is_audited_rather_than_silently_emptied(self):
        """An empty bundle would look like a push that succeeded."""
        import inspect

        from app.routers import physician

        src = inspect.getsource(physician.fetch_fhir)
        self.assertIn("fhir.blocked", src)

    def test_absent_consent_is_a_refusal(self):
        """No consent row means no consent. Never a default yes."""
        import inspect

        from app.routers import physician

        self.assertIn("False", inspect.getsource(physician.sharing_consent))


class TestClinicianAttachmentIsComplete(unittest.TestCase):
    def test_the_attachment_carries_a_date(self):
        """Nothing extracts a date from the clinician's own document.

        Without one the timeline showed the prescription with a blank Date
        cell and no way to tell when it was written.
        """
        import inspect

        from app.routers import physician

        self.assertIn("doc_date=", inspect.getsource(physician.attach_clinician_document))

    def test_no_extraction_is_run_on_it(self):
        """The doctor wrote it. Reading it back to them with a model is noise."""
        import inspect

        from app.routers import physician

        src = inspect.getsource(physician.attach_clinician_document)
        self.assertNotIn("_extract_in_background", src)


if __name__ == "__main__":
    unittest.main()

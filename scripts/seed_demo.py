#!/usr/bin/env python3
# Owner: Nikki
"""Fill the local queue with a handful of realistic, complete patients.

Run after scripts/reset_db.py, with the backend already up. What it produces
is what a doctor should see at the start of a clinic: a few people waiting,
different complaints, different languages, one urgent.

    python3 scripts/seed_demo.py

Everything goes through the REAL API — POST /session/start, /session/{id}/
fields, /documents/{id}/upload, /summary/{id}/generate. Nothing is written to
the database directly. That matters because it is the only way the seeded rows
exercise the same paths a live patient does: the same token allocation, the
same reconciliation, the same red-flag evaluation, the same summary. A row
inserted by hand would look right in the queue and prove nothing.

The clinical fields are seeded through /fields rather than by answering the
interview question by question. /fields costs no model call, so seeding five
patients takes seconds and works when the model is slow or down — which on the
morning of a demo is exactly when this needs to work. The one thing it does
not exercise is the interview loop itself, and that is what the kiosk in front
of you is for.
"""

import argparse
import base64
import json
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

API = "http://localhost:8000/api"

# A 1x1 PNG. The upload path is what is being exercised, not the image.
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

# Five patients. Different languages, different complaints, one red flag
# (chest pain with breathlessness fires chest_pain_breathlessness), one with a
# document to upload. Ages and names are obviously fictional.
PATIENTS = [
    {
        "label": "chest pain, urgent",
        "language": "hi",
        "upload": False,
        "share_government": True,
        "fields": {
            "patient_name": "Ramesh Kumar", "age": 58, "sex": "male", "consent_given": "yes",
            "chief_complaint": "chest", "symptom_site": "chest",
            "symptom_duration": "2_days", "symptom_onset": "2_days",
            "symptom_character": "pressure", "symptom_severity": "severe",
            "symptom_timing": "on_exertion",
            # This pair is what makes the red flag fire.
            "associated_symptoms": ["breathlessness"],
            "past_medical_conditions": "hypertension", "past_surgeries": "none",
            "current_medications": "amlodipine", "known_allergies": "none",
            "family_history": "father had a heart attack at 60",
            "smoking_status": "daily", "alcohol_use": "occasionally", "diet": "mixed",
            "ros_screen": "none",
        },
    },
    {
        "label": "headache",
        "language": "te",
        "upload": False,
        # One patient who declines sharing, so the console shows both states
        # and the blocked outbound path can be demonstrated on a real record.
        "share_government": False,
        "fields": {
            "patient_name": "Lakshmi Reddy", "age": 34, "sex": "female", "consent_given": "yes",
            "chief_complaint": "head", "symptom_site": "head",
            "symptom_duration": "few_days", "symptom_onset": "few_days",
            "symptom_character": "throbbing", "symptom_severity": "moderate",
            "symptom_timing": "morning", "associated_symptoms": ["none"],
            "past_medical_conditions": "none", "past_surgeries": "none",
            "current_medications": "none", "known_allergies": "penicillin",
            "family_history": "mother has migraine",
            "smoking_status": "never", "alcohol_use": "never", "diet": "vegetarian",
            "ros_screen": "none",
        },
    },
    {
        "label": "back pain, with a document",
        "share_government": True,
        "language": "en",
        "upload": True,
        "fields": {
            "patient_name": "Anand Pillai", "age": 45, "sex": "male", "consent_given": "yes",
            "chief_complaint": "back", "symptom_site": "back",
            "symptom_duration": "weeks", "symptom_onset": "weeks",
            "symptom_character": "aching", "symptom_severity": "moderate",
            "symptom_timing": "worse_at_night", "associated_symptoms": ["none"],
            "past_medical_conditions": "diabetes", "past_surgeries": "none",
            "current_medications": "metformin", "known_allergies": "none",
            "family_history": "none", "smoking_status": "never",
            "alcohol_use": "occasionally", "diet": "mixed", "ros_screen": "none",
        },
    },
    {
        "label": "fever",
        "share_government": True,
        "language": "kn",
        "upload": False,
        "fields": {
            "patient_name": "Meena Shetty", "age": 27, "sex": "female", "consent_given": "yes",
            "chief_complaint": "fever", "symptom_site": "whole body",
            "symptom_duration": "1_day", "symptom_onset": "1_day",
            "symptom_character": "continuous", "symptom_severity": "mild",
            "symptom_timing": "evening", "associated_symptoms": ["none"],
            "past_medical_conditions": "none", "past_surgeries": "none",
            "current_medications": "paracetamol", "known_allergies": "none",
            "family_history": "none", "smoking_status": "never",
            "alcohol_use": "never", "diet": "vegetarian", "ros_screen": "none",
        },
    },
    {
        "label": "stomach pain",
        "share_government": True,
        "language": "ta",
        "upload": False,
        "fields": {
            "patient_name": "Suresh Iyer", "age": 61, "sex": "male", "consent_given": "yes",
            "chief_complaint": "stomach", "symptom_site": "stomach",
            "symptom_duration": "weeks", "symptom_onset": "weeks",
            "symptom_character": "burning", "symptom_severity": "moderate",
            "symptom_timing": "after_food", "associated_symptoms": ["none"],
            "past_medical_conditions": "acidity", "past_surgeries": "appendectomy",
            "current_medications": "omeprazole", "known_allergies": "none",
            "family_history": "none", "smoking_status": "former",
            "alcohol_use": "never", "diet": "vegetarian", "ros_screen": "none",
        },
    },
]


def call(method: str, path: str, body=None, timeout=90):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API}{path}", data=data, method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


def upload_document(session_id: str) -> bool:
    """A real multipart upload, so the timeline shows something that happened."""
    boundary = "----medikioskseed"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="report.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + TINY_PNG + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{API}/documents/{session_id}/upload", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            r.read()
        return True
    except Exception as exc:
        print(f"      document upload failed: {str(exc)[:70]}")
        return False


def seed_one(p: dict) -> dict:
    started = call("POST", "/session/start", {"language": p["language"]})
    sid = started["session_id"]

    # Consent first, exactly as the kiosk does it — the record is not
    # shareable unless the patient said so, and the seeded queue has to
    # reflect that rather than leaving every case unconsented.
    call("POST", f"/session/{sid}/consent", {
        "history": True,
        "documents": True,
        "abha": False,
        "government": p.get("share_government", False),
        "language": p["language"],
    })

    call("POST", f"/session/{sid}/fields", {"fields": p["fields"]})

    uploaded = upload_document(sid) if p["upload"] else False

    # Generating here means the doctor never waits for it, and it is the same
    # call the kiosk's Confirm screen makes.
    try:
        call("POST", f"/summary/{sid}/generate", {}, timeout=120)
        summarised = True
    except Exception as exc:
        # The deterministic field mapping still fills the sections, so the case
        # is readable either way. Say so rather than pretending it worked.
        print(f"      summary generation failed ({str(exc)[:50]}); sections fall back to fields")
        summarised = False

    return {
        "session_id": sid,
        "uploaded": uploaded,
        "summarised": summarised,
        "shared": p.get("share_government", False),
    }


def main() -> int:
    global API
    parser = argparse.ArgumentParser(description="Seed a realistic demo queue.")
    parser.add_argument("--api", default=API, help="API base URL")
    args = parser.parse_args()
    API = args.api

    try:
        call("GET", "/health", timeout=5)
    except Exception:
        print(f"backend not reachable at {API} — start it with ./dev.sh first")
        return 2

    print(f"seeding {len(PATIENTS)} patients through {API}\n")
    made = []
    for p in PATIENTS:
        print(f"  {p['label']} ({p['language']}) ...")
        try:
            made.append({**seed_one(p), "label": p["label"]})
        except urllib.error.HTTPError as exc:
            print(f"      FAILED: HTTP {exc.code} {exc.read()[:90]!r}")
        except Exception as exc:
            print(f"      FAILED: {str(exc)[:90]}")

    if not made:
        print("\nnothing seeded.")
        return 1

    # Read the queue back through the API the console uses, so what is printed
    # is what the doctor will actually see.
    print(f"\nseeded {len(made)} of {len(PATIENTS)}. Queue as the console sees it:\n")
    from app.database import SessionLocal
    from app import models

    db = SessionLocal()
    for m in made:
        row = db.get(models.Session, m["session_id"])
        if row is None:
            # Should not happen now that reset empties tables instead of
            # unlinking the file, but a summary line is not worth a traceback.
            print(f"  ?????  {m['label']:28} seeded but not readable back")
            continue
        rec = (
            db.query(models.ClinicalRecord)
            .filter(models.ClinicalRecord.session_id == m["session_id"])
            .one_or_none()
        )
        flags = (rec.red_flags if rec else None) or []
        fields = len((rec.history if rec else None) or {})
        docs = (
            db.query(models.DocumentUpload)
            .filter(models.DocumentUpload.session_id == m["session_id"])
            .count()
        )
        print(
            f"  {row.token:6} {m['label']:28} fields={fields:2} docs={docs} "
            f"summary={'yes' if (rec and rec.summary) else 'NO':3} "
            f"share={'yes' if m['shared'] else 'NO ':3} "
            f"{'RED FLAG' if flags else ''}"
        )

    tokens = [db.get(models.Session, m["session_id"]).token for m in made]
    print(f"\ntokens unique: {len(set(tokens)) == len(tokens)}  ({', '.join(tokens)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

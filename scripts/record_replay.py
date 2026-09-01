"""Record one real session's API responses into a replay fixture.

Drives the live backend (real Gemini) exactly the way the kiosk does, and
writes every response verbatim to frontend/public/replay/session.json.

Records two tracks:
  answers      — a full interview that ends in a red flag (chest pain with
                 breathlessness). That is the headline demo path.
  physician    — queue, case and FHIR bundle from a completed session, so the
                 console has real data too.

Paced under the free tier's 15 requests/minute.
"""
import json
import pathlib
import sys
import time
import urllib.request
from datetime import datetime, timezone

B = "http://localhost:8000/api"
PACE = 4.5

OUT = pathlib.Path("/Users/nikhilesh/projects/Medikiosk/frontend/public/replay/session.json")


TOKEN = {"access": None}


def _headers():
    h = {"Content-Type": "application/json"}
    if TOKEN["access"]:
        h["Authorization"] = f"Bearer {TOKEN['access']}"
    return h


def call(path, body=None, method="POST"):
    data = json.dumps(body if body is not None else {}).encode()
    req = urllib.request.Request(
        B + path, data=data if method != "GET" else None,
        headers=_headers(), method=method,
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def get(path):
    req = urllib.request.Request(B + path, headers=_headers(), method="GET")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def sign_in():
    """The physician routes need a clinician token now. Credentials come from
    app/.demo-credentials, written when the account was seeded."""
    creds_file = pathlib.Path("/Users/nikhilesh/projects/Medikiosk/app/.demo-credentials")
    creds = dict(
        line.split(": ", 1) for line in creds_file.read_text().strip().splitlines()
    )
    TOKEN["access"] = call(
        "/auth/login", {"username": creds["username"], "password": creds["password"]}
    )["access"]


SEED = {"patient_name": "Lakshmi Devi", "age": "65", "sex": "female", "consent_given": "yes"}

# The patient answers whatever was actually asked, so the recording reads like
# a real conversation rather than a script talking past the questions. Keyword
# matched against the question text, cheapest thing that works and keeps the
# recording natural. Ends on breathlessness so a genuine red flag is captured.
REPLIES = [
    (("how long", "since when", "kab se", "duration"), "for the last two days"),
    (("where", "which part", "located", "kahan"), "in the middle of my chest"),
    (("start", "begin", "suddenly", "slowly"), "it started suddenly while I was resting"),
    (("feel", "type of pain", "kind of pain", "describe"), "it feels like a burning pressure"),
    (("bad", "severe", "strong", "how much"), "it is severe, the worst I have had"),
    (("other", "along with", "also", "any of these"), "yes, I am short of breath as well"),
    (("spread", "radiat", "move"), "it spreads into my left arm"),
]
OPENING = "I have had chest pain for two days"


# A location question gets a location answer every time it is asked, even if
# it was asked before. A real patient repeats themselves; more importantly, if
# the field did not fill the first time, answering something else guarantees it
# never will and the interview stalls on the same question.
SITE_KEYS = ("where", "which part", "located", "point to", "kahan")
SITE_REPLY = "behind my breastbone, in the centre of my chest"


def reply_for(question, asked):
    """Pick an answer that actually addresses the question just asked."""
    q = (question or "").lower()
    if any(k in q for k in SITE_KEYS):
        return SITE_REPLY
    for keys, text in REPLIES:
        if text in asked:
            continue
        if any(k in q for k in keys):
            return text
    for _, text in REPLIES:
        if text not in asked:
            return text
    return "I do not know"


def record_kiosk():
    print("== recording kiosk track ==")
    track = {}
    start = call("/session/start", {"lang": "en"})
    sid = start["session_id"]
    track["session"] = start
    print(f"   session {sid}")
    print(f"   q1: {start['first_question']['question']!r}")

    time.sleep(PACE)
    track["fields"] = call(f"/session/{sid}/fields", {"fields": SEED})
    print(f"   seeded {[f['name'] for f in track['fields']['extracted']]}")

    node_id = start["first_question"]["node_id"]
    question = start["first_question"]["question"]
    answers, asked = [], set()
    for i in range(1, 10):
        text = OPENING if i == 1 else reply_for(question, asked)
        asked.add(text)
        time.sleep(PACE)
        resp = call(f"/interview/{sid}/answer", {"node_id": node_id, "text": text, "lang": "en"})
        answers.append({"said": text, "response": resp})
        rf = (resp.get("red_flag") or {}).get("rule_id")
        print(f"   a{i} [{node_id:<15}] {text[:34]!r:<38} -> {resp.get('node_id')!r} "
              f"fields={len(resp.get('extracted', []))} rf={rf}")
        if resp.get("red_flag") or resp.get("done"):
            break
        node_id, question = resp["node_id"], resp.get("question")

    track["answers"] = answers
    time.sleep(PACE)
    track["summary"] = call(f"/summary/{sid}/generate")
    print(f"   summary: {track['summary'].get('chief_complaint')!r}")
    track["session_id"] = sid
    return track


def record_physician(sid):
    print("== recording physician track ==")
    sign_in()
    out = {}
    out["queue"] = get("/physician/queue")
    out["case"] = get(f"/physician/{sid}")
    out["fhir"] = get(f"/physician/{sid}/fhir")
    out["summary"] = get(f"/summary/{sid}")
    print(f"   queue rows: {len(out['queue'])}")
    print(f"   fhir entries: {len(out['fhir'].get('entry', []))}")
    return out


kiosk = record_kiosk()
physician = record_physician(kiosk["session_id"])

fixture = {
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "note": (
        "Recorded from a live session against the real Gemini API. Replayed "
        "verbatim when VITE_REPLAY=true so the kiosk demos with no network and "
        "no API quota. Regenerate with scripts/record_replay.py."
    ),
    "language": "en",
    "kiosk": kiosk,
    "physician": physician,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(fixture, indent=2, ensure_ascii=False))
print(f"\nwrote {OUT}  ({OUT.stat().st_size / 1024:.1f} kB)")
print(f"answers recorded: {len(kiosk['answers'])}")
print(f"red flag present: {any(a['response'].get('red_flag') for a in kiosk['answers'])}")

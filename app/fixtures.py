# Owner: Tharun
"""Canned interview content and demo records.

extraction, follow-up generation and summary generation are now genuinely
live (app/ai_bridge.py calls into ai/ with no fallback for those three), so
INTERVIEW_NODES / NODE_ORDER / render_node / first_node_id / next_node_id
are dead code — nothing calls them any more. Left in place rather than
deleted piecemeal; safe to remove together in one pass.

The red-flag rules that used to live here have been deleted outright — see the
note further down where they were.

Everything else here is still a live dependency, not a leftover:
  - DEMO_TOKEN / DEMO_ROOM: app/routers/session.py and app/routers/summary.py
    fall back to these — there is no real token/room allocation system.
  - DEMO_DOCUMENTS: app/routers/summary.py and app/routers/physician.py fall
    back to this when a session has no uploaded documents — ai.documents.extract
    isn't wired live yet, that's a separate pass.
  - DEMO_HISTORY / DEMO_PATIENT / DEMO_CHIEF_COMPLAINT / DEMO_QUEUE: only
    app/routers/physician.py, entirely untouched by the extraction/follow-up/
    summary wiring — the physician console still reads demo data.
  - fixtures.render_node: app/routers/interview.py's GET .../node/{node_id}
    falls back to it only if a node was never actually rendered into
    state.rendered_nodes for this session (e.g. after a process restart).

The node set and the red-flag trigger deliberately mirror
frontend/public/mocks/sample_session.json so that flipping VITE_USE_MOCKS to
false changes nothing the patient can see.

The real question set is ai/dashavidha/questions.py and is Nikki's to write.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _t(**kwargs: str) -> Dict[str, str]:
    """Shorthand for a per-language string map."""
    return kwargs


INTERVIEW_NODES: List[Dict[str, Any]] = [
    {
        "node_id": "duration",
        "node_type": "single_choice",
        "question": _t(
            en="How long have you had this problem?",
            hi="यह तकलीफ़ आपको कब से है?",
            kn="ಈ ತೊಂದರೆ ನಿಮಗೆ ಎಷ್ಟು ದಿನಗಳಿಂದ ಇದೆ?",
            ta="இந்தப் பிரச்சனை எவ்வளவு காலமாக உள்ளது?",
            te="ఈ సమస్య మీకు ఎంతకాలంగా ఉంది?",
            mr="हा त्रास तुम्हाला किती दिवसांपासून आहे?",
            bn="এই সমস্যা কতদিন ধরে আছে?",
        ),
        "options": [
            ("days", _t(en="1-2 days", hi="एक-दो दिन", kn="ಒಂದು-ಎರಡು ದಿನ", ta="ஒன்று-இரண்டு நாள்",
                        te="ఒకటి-రెండు రోజులు", mr="एक-दोन दिवस", bn="এক-দুই দিন")),
            ("week", _t(en="About a week", hi="करीब एक हफ़्ता", kn="ಸುಮಾರು ಒಂದು ವಾರ",
                        ta="சுமார் ஒரு வாரம்", te="సుమారు ఒక వారం", mr="सुमारे एक आठवडा",
                        bn="প্রায় এক সপ্তাহ")),
            ("month_plus", _t(en="More than a month", hi="एक महीने से ज़्यादा",
                              kn="ಒಂದು ತಿಂಗಳಿಗಿಂತ ಹೆಚ್ಚು", ta="ஒரு மாதத்திற்கு மேல்",
                              te="ఒక నెల కంటే ఎక్కువ", mr="एक महिन्यापेक्षा जास्त",
                              bn="এক মাসের বেশি")),
        ],
    },
    {
        "node_id": "severity",
        "node_type": "single_choice",
        "question": _t(
            en="How strong is the discomfort?",
            hi="तकलीफ़ कितनी तेज़ है?",
            kn="ತೊಂದರೆ ಎಷ್ಟು ತೀವ್ರವಾಗಿದೆ?",
            ta="தொந்தரவு எவ்வளவு கடுமையானது?",
            te="ఇబ్బంది ఎంత తీవ్రంగా ఉంది?",
            mr="त्रास किती तीव्र आहे?",
            bn="কষ্ট কতটা তীব্র?",
        ),
        "options": [
            ("mild", _t(en="Mild", hi="हल्की", kn="ಸೌಮ್ಯ", ta="லேசானது", te="తక్కువ",
                        mr="सौम्य", bn="হালকা")),
            ("moderate", _t(en="Moderate", hi="मध्यम", kn="ಮಧ್ಯಮ", ta="மிதமானது",
                            te="మధ్యస్థం", mr="मध्यम", bn="মাঝারি")),
            ("severe", _t(en="Severe", hi="बहुत तेज़", kn="ತೀವ್ರ", ta="கடுமையானது",
                          te="తీవ్రం", mr="तीव्र", bn="তীব্র")),
        ],
    },
    {
        "node_id": "pattern",
        "node_type": "single_choice",
        "question": _t(
            en="Is it there all the time, or does it come and go?",
            hi="क्या यह हर समय रहती है या आती-जाती है?",
            kn="ಇದು ಯಾವಾಗಲೂ ಇರುತ್ತದೆಯೇ ಅಥವಾ ಬಂದು ಹೋಗುತ್ತದೆಯೇ?",
            ta="இது எப்போதும் இருக்கிறதா அல்லது வந்து போகிறதா?",
            te="ఇది ఎప్పుడూ ఉంటుందా లేక వచ్చిపోతుందా?",
            mr="हे सतत असते की येते-जाते?",
            bn="এটি কি সবসময় থাকে নাকি আসে-যায়?",
        ),
        "options": [
            ("intermittent", _t(en="Comes and goes", hi="आती-जाती है", kn="ಬಂದು ಹೋಗುತ್ತದೆ",
                                ta="வந்து போகிறது", te="వచ్చిపోతుంది", mr="येते-जाते",
                                bn="আসে-যায়")),
            ("constant", _t(en="All the time", hi="हर समय", kn="ಯಾವಾಗಲೂ", ta="எப்போதும்",
                            te="ఎప్పుడూ", mr="सतत", bn="সবসময়")),
        ],
    },
    {
        "node_id": "associated",
        "node_type": "single_choice",
        "question": _t(
            en="Do you also have any of these?",
            hi="क्या आपको इनमें से कुछ भी है?",
            kn="ನಿಮಗೆ ಇವುಗಳಲ್ಲಿ ಏನಾದರೂ ಇದೆಯೇ?",
            ta="இவற்றில் ஏதேனும் உள்ளதா?",
            te="వీటిలో ఏవైనా ఉన్నాయా?",
            mr="यापैकी काही आहे का?",
            bn="এর মধ্যে কিছু আছে কি?",
        ),
        "options": [
            ("fever", _t(en="Fever", hi="बुखार", kn="ಜ್ವರ", ta="காய்ச்சல்", te="జ్వరం",
                         mr="ताप", bn="জ্বর")),
            ("vomiting", _t(en="Vomiting", hi="उल्टी", kn="ವಾಂತಿ", ta="வாந்தி",
                            te="వాంతులు", mr="उलटी", bn="বমি")),
            ("breathlessness", _t(en="Breathlessness", hi="साँस फूलना",
                                  kn="ಉಸಿರಾಟದ ತೊಂದರೆ", ta="மூச்சுத் திணறல்",
                                  te="ఊపిరి ఆడకపోవడం", mr="श्वास लागणे", bn="শ্বাসকষ্ট")),
            ("none", _t(en="None of these", hi="इनमें से कुछ नहीं",
                        kn="ಇವುಗಳಲ್ಲಿ ಯಾವುದೂ ಇಲ್ಲ", ta="இவை எதுவும் இல்லை",
                        te="వీటిలో ఏదీ లేదు", mr="यापैकी काहीही नाही",
                        bn="এগুলোর কোনোটিই নয়")),
        ],
    },
    {
        "node_id": "medicines",
        "node_type": "free_text",
        "question": _t(
            en="Are you taking any medicines now? Please say their names.",
            hi="क्या आप अभी कोई दवा ले रहे हैं? कृपया उनके नाम बताएँ।",
            kn="ನೀವು ಈಗ ಯಾವುದಾದರೂ ಔಷಧಿ ತೆಗೆದುಕೊಳ್ಳುತ್ತಿದ್ದೀರಾ? ದಯವಿಟ್ಟು ಹೆಸರು ಹೇಳಿ.",
            ta="நீங்கள் இப்போது ஏதேனும் மருந்து எடுக்கிறீர்களா? பெயரைச் சொல்லுங்கள்.",
            te="మీరు ప్రస్తుతం ఏవైనా మందులు వాడుతున్నారా? పేర్లు చెప్పండి.",
            mr="तुम्ही सध्या काही औषध घेत आहात का? कृपया नावे सांगा.",
            bn="আপনি কি এখন কোনো ওষুধ খাচ্ছেন? নাম বলুন।",
        ),
        "options": [],
    },
    {
        "node_id": "conditions",
        "node_type": "single_choice",
        "question": _t(
            en="Do you have any of these long-term illnesses?",
            hi="क्या आपको इनमें से कोई पुरानी बीमारी है?",
            kn="ನಿಮಗೆ ಇವುಗಳಲ್ಲಿ ಯಾವುದಾದರೂ ದೀರ್ಘಕಾಲದ ಕಾಯಿಲೆ ಇದೆಯೇ?",
            ta="இவற்றில் ஏதேனும் நீண்டகால நோய் உள்ளதா?",
            te="వీటిలో ఏవైనా దీర్ఘకాల వ్యాధులు ఉన్నాయా?",
            mr="यापैकी काही जुना आजार आहे का?",
            bn="এর মধ্যে কোনো দীর্ঘমেয়াদী রোগ আছে কি?",
        ),
        "options": [
            ("diabetes", _t(en="Diabetes", hi="मधुमेह", kn="ಮಧುಮೇಹ", ta="நீரிழிவு",
                            te="మధుమేహం", mr="मधुमेह", bn="ডায়াবেটিস")),
            ("hypertension", _t(en="Blood pressure", hi="रक्तचाप", kn="ರಕ್ತದೊತ್ತಡ",
                                ta="இரத்த அழுத்தம்", te="రక్తపోటు", mr="रक्तदाब",
                                bn="রক্তচাপ")),
            ("asthma", _t(en="Asthma", hi="दमा", kn="ಅಸ್ತಮಾ", ta="ஆஸ்துமா", te="ఆస్తమా",
                          mr="दमा", bn="হাঁপানি")),
            ("none", _t(en="None of these", hi="इनमें से कुछ नहीं",
                        kn="ಇವುಗಳಲ್ಲಿ ಯಾವುದೂ ಇಲ್ಲ", ta="இவை எதுவும் இல்லை",
                        te="వీటిలో ఏదీ లేదు", mr="यापैकी काहीही नाही",
                        bn="এগুলোর কোনোটিই নয়")),
        ],
    },
]

NODE_ORDER: List[str] = [n["node_id"] for n in INTERVIEW_NODES]
_BY_ID: Dict[str, Dict[str, Any]] = {n["node_id"]: n for n in INTERVIEW_NODES}


def localise(value: Any, lang: str) -> str:
    """Pick the patient's language out of a string map, falling back to English."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.get(lang) or value.get("en") or ""


def render_node(node_id: str, lang: str) -> Optional[Dict[str, Any]]:
    """Shape one node for the API response, translated. None if unknown."""
    node = _BY_ID.get(node_id)
    if node is None:
        return None
    return {
        "node_id": node["node_id"],
        "question": localise(node["question"], lang),
        "options": [{"value": v, "label": localise(lbl, lang)} for v, lbl in node["options"]],
        "allow_free_text": True,
        "node_type": node["node_type"],
    }


def first_node_id() -> str:
    return NODE_ORDER[0]


def next_node_id(current: Optional[str]) -> Optional[str]:
    """The node after `current`, or None when the interview is finished."""
    if current is None:
        return NODE_ORDER[0]
    if current not in NODE_ORDER:
        return NODE_ORDER[0]
    index = NODE_ORDER.index(current) + 1
    return NODE_ORDER[index] if index < len(NODE_ORDER) else None


# Red-flag rules used to live here. They are gone on purpose.
#
# They matched English literals ("chest pain", "bleeding") as substrings of the
# raw transcript, which silently did nothing for six of the seven languages the
# kiosk speaks: a Hindi speaker saying "मुझे सीने में दर्द है" matched no rule
# and saw no emergency screen, while the identical English sentence did.
#
# ai/safety/red_flags.py is the only red-flag authority now. It evaluates
# already-extracted fields, which extraction has translated into English
# clinical terms, so all seven languages behave identically. It is still pure
# Python with no model call, so it still runs inline on every answer.


# ------------------------------------------------------------- demo records

DEMO_TOKEN = "A-42"
DEMO_ROOM = "12"

DEMO_SECTIONS: Dict[str, str] = {
    "past_history": "Type 2 diabetes mellitus, 12 years. Hypertension, 8 years.",
    "drugs_allergies": "Metformin 500 mg twice daily. Amlodipine 5 mg once daily. No known allergy.",
    "family": "Father died of a heart attack at 60.",
    "personal": "Non-smoker. No alcohol. Sedentary.",
    "ros": "Cardiovascular: chest discomfort, exertional breathlessness. Respiratory: no cough.",
}

DEMO_HPI_NARRATIVE = (
    "Central chest discomfort for 2 days, constant, moderate in intensity, with "
    "associated breathlessness on exertion. No radiation to the arm or jaw reported."
)

DEMO_CHIEF_COMPLAINT = "Chest discomfort for 2 days"

DEMO_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "doc_id": "doc-1",
        "type": "lab_report",
        "status": "done",
        "title": "Lipid profile - District Lab",
        "date": "2026-06-12",
        "extracted": {},
        "findings": [
            {"label": "Total cholesterol", "value": 244, "unit": "mg/dL", "ref": "<200",
             "out_of_range": True},
            {"label": "LDL", "value": 168, "unit": "mg/dL", "ref": "<100", "out_of_range": True},
            {"label": "HDL", "value": 38, "unit": "mg/dL", "ref": ">40", "out_of_range": True},
        ],
    },
    {
        "doc_id": "doc-2",
        "type": "lab_report",
        "status": "done",
        "title": "HbA1c - District Lab",
        "date": "2026-07-03",
        "extracted": {},
        "findings": [
            {"label": "HbA1c", "value": 8.9, "unit": "%", "ref": "<7.0", "out_of_range": True},
        ],
    },
]

DEMO_QUEUE: List[Dict[str, Any]] = [
    {
        "session_id": "mock-session-001",
        "token": "A-42",
        "name": "Lakshmi Devi",
        "age": 65,
        "sex": "F",
        "complaint": "Chest discomfort, 2 days",
        "red_flag": "Breathlessness",
        "waiting_since": "09:14",
    },
    {
        "session_id": "mock-session-002",
        "token": "A-43",
        "name": "Ramesh Kumar",
        "age": 48,
        "sex": "M",
        "complaint": "Joint pain, 3 months",
        "red_flag": None,
        "waiting_since": "09:21",
    },
    {
        "session_id": "mock-session-003",
        "token": "A-44",
        "name": "Fatima Bi",
        "age": 71,
        "sex": "F",
        "complaint": "Fever, 4 days",
        "red_flag": None,
        "waiting_since": "09:26",
    },
]

DEMO_PATIENT: Dict[str, Any] = {
    "name": "Lakshmi Devi",
    "age": 65,
    "sex": "F",
    "abha": "14-2233-4455-6677",
}


# Structured demo history.
#
# FHIR needs lists, not prose. The console renders DEMO_SECTIONS as paragraphs;
# app/fhir.py builds Condition / MedicationStatement / AllergyIntolerance from
# these lists instead. Nothing regexes clinical facts out of free text — a
# wrongly parsed drug name is a patient safety problem, not a formatting one.
DEMO_HISTORY: Dict[str, Any] = {
    "chief_complaint": DEMO_CHIEF_COMPLAINT,
    "past_medical": ["Type 2 diabetes mellitus", "Hypertension"],
    "past_surgical": [],
    "medications": ["Metformin 500 mg twice daily", "Amlodipine 5 mg once daily"],
    "allergies": [],
    "family": ["Father: myocardial infarction at 60"],
    "personal": {"tobacco": "never", "alcohol": "never", "activity": "sedentary"},
    "ros": {"cardiovascular": "chest discomfort, exertional breathlessness",
            "respiratory": "no cough"},
}

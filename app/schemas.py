# Owned by Tharun. Written after the extraction spike. Nobody else edits this file.
"""Pydantic contract for MediKiosk.

Every model here is passed between the kiosk, the AI layer and the physician
console, so shapes are deliberately permissive: a real OPD interview is half
empty. Almost everything is Optional, and list/dict fields default to empty
rather than being required, because a model that demands fields returns 422 to
a 65-year-old standing at a kiosk who cannot read the error.

Field descriptions are attached with Field(description=...) rather than written
as comments so they surface in the OpenAPI schema at /docs — that page is the
frontend's reference.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp. Naive datetimes cause ordering bugs."""
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------- enums


class Language(str, Enum):
    """The seven languages the kiosk speaks. Matches frontend i18n codes."""

    en = "en"
    hi = "hi"
    kn = "kn"
    ta = "ta"
    te = "te"
    mr = "mr"
    bn = "bn"


class Sex(str, Enum):
    """Patient sex as collected by the kiosk's three-tile selector."""

    male = "male"
    female = "female"
    other = "other"


class NodeType(str, Enum):
    """How the frontend should render an interview node."""

    single_choice = "single_choice"
    multi_choice = "multi_choice"
    free_text = "free_text"
    numeric = "numeric"
    terminal = "terminal"


class DocumentType(str, Enum):
    """Kind of paper the patient photographed."""

    prescription = "prescription"
    lab_report = "lab_report"
    discharge_summary = "discharge_summary"
    imaging = "imaging"
    other = "other"


class DocumentStatus(str, Enum):
    """Lifecycle of an uploaded document. Uploads ack immediately at `queued`."""

    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"


class FlagSeverity(str, Enum):
    """How urgently a red flag needs a human. `critical` shows the emergency screen."""

    critical = "critical"
    high = "high"
    moderate = "moderate"
    low = "low"


class FieldSource(str, Enum):
    """Where an extracted value came from. Drives provenance in the console.

    `touch` is not a lesser form of `speech`: the patient tapped a tile whose
    value is already a canonical English token, so nothing was transcribed,
    translated or inferred. It is the most reliable provenance of the three.
    """

    speech = "speech"
    touch = "touch"
    document = "document"
    # Not stated by the patient in so many words, but implied by something
    # they DID state — "back pain" implies the site is the back. Derived by
    # ai/interview/reconcile.py from a lookup table, never by a model. Kept
    # distinct from `speech` so the console can show the physician which
    # values the patient said and which the kiosk worked out.
    derived = "derived"


class FindingKind(str, Enum):
    """What a document finding actually is.

    The discriminator on DocumentFinding. app/fhir.py maps each value straight
    onto a FHIR resource type, so adding a member here means adding a builder
    there:

        diagnosis  -> Condition
        medication -> MedicationStatement
        lab        -> Observation
        procedure  -> Procedure
    """

    diagnosis = "diagnosis"
    medication = "medication"
    lab = "lab"
    procedure = "procedure"


class TerminalReason(str, Enum):
    """Why an interview stopped.

    A red flag used to return node_id=None, question=None, done=False — neither
    a question nor an ending, which the kiosk had no state for. A stopped
    interview now always sets done=True and says which of these it was.
    """

    completed = "completed"
    red_flag = "red_flag"


class VerifyAction(str, Enum):
    """What the physician did with a draft record."""

    accept = "accept"
    amend = "amend"
    reject = "reject"


class SessionStatus(str, Enum):
    """Session lifecycle."""

    in_progress = "in_progress"
    awaiting_physician = "awaiting_physician"
    verified = "verified"
    rejected = "rejected"
    abandoned = "abandoned"
    ended = "ended"


# ---------------------------------------------------------------- core models


class Identity(BaseModel):
    """Who the patient is. Every field optional — walk-ins give us nothing.

    Note there is no full Aadhaar field anywhere in this contract. Only the last
    four digits are ever accepted, held or returned.
    """

    abha_id: Optional[str] = Field(None, description="14-digit ABHA number, formatted or bare.")
    aadhaar_last4: Optional[str] = Field(
        None,
        max_length=4,
        description="Last four Aadhaar digits only. The full number is never stored.",
    )
    name: Optional[str] = Field(None, description="Patient name as spoken or typed at the kiosk.")
    age: Optional[int] = Field(None, ge=0, le=130, description="Age in years.")
    sex: Optional[Sex] = Field(None, description="Patient sex.")


class ConsentRecord(BaseModel):
    """The three consent toggles, captured before any clinical question is asked.

    Consent is recorded per-purpose rather than as one blanket flag so a patient
    can allow the interview but refuse document reading or ABHA linkage.
    """

    record_history: bool = Field(..., description="May we record the medical history interview?")
    read_documents: bool = Field(..., description="May we read photographed prescriptions/reports?")
    link_abha: bool = Field(..., description="May we link this encounter to the ABHA record?")
    timestamp: datetime = Field(default_factory=_utcnow, description="When consent was given.")
    language: Language = Field(
        Language.en, description="Language the consent was played and understood in."
    )
    method: str = Field(
        "audio_guided",
        description="How consent was obtained. Always audio_guided at a kiosk.",
    )


class Answer(BaseModel):
    """One patient response to one interview node.

    Accepts the frontend's field names as aliases: it sends {value, text, lang}
    while this contract calls them {selected_option, raw_transcript, language}.
    """

    model_config = ConfigDict(populate_by_name=True)

    node_id: str = Field(..., description="Which interview node this answers.")
    raw_transcript: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("raw_transcript", "transcript", "text"),
        description="What speech recognition heard. Discarded when the session ends.",
    )
    selected_option: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("selected_option", "value", "option"),
        description="Value of the tapped option tile, when the patient tapped instead of spoke.",
    )
    language: Language = Field(
        Language.en,
        validation_alias=AliasChoices("language", "lang"),
        description="Language the answer was given in.",
    )
    timestamp: datetime = Field(default_factory=_utcnow, description="When the answer arrived.")


class ExtractedField(BaseModel):
    """A single structured value pulled out of speech or a document by ai/."""

    name: str = Field(..., description="Field name, e.g. 'onset' or 'hba1c'.")
    value: Any = Field(..., description="Extracted value. Typed loosely — ai/ decides.")
    display: Optional[str] = Field(
        None,
        description=(
            "The value as the patient should SEE it, in their language — the "
            "label of the option they tapped. Display only. Every rule, the "
            "summary, the FHIR builder and storage read `value`, never this: "
            "the canonical token is what makes red flags fire identically in "
            "all seven languages. Absent when nothing better than the value "
            "itself is known."
        ),
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence 0-1. Low values are shown to the doctor."
    )
    source: FieldSource = Field(..., description="Whether this came from speech or a document.")


class HPI(BaseModel):
    """History of present illness, SOCRATES-structured. All fields optional.

    A patient rarely volunteers all eight. Missing entries mean 'not asked or
    not answered', never 'absent' — the console must not read a None as normal.
    """

    site: Optional[str] = Field(None, description="Where the problem is.")
    onset: Optional[str] = Field(None, description="When and how it started.")
    character: Optional[str] = Field(None, description="What it feels like.")
    radiation: Optional[str] = Field(None, description="Whether it moves elsewhere.")
    timing: Optional[str] = Field(None, description="Constant, intermittent, worse at a time of day.")
    severity: Optional[str] = Field(None, description="How bad, in the patient's own terms.")
    aggravating: Optional[str] = Field(None, description="What makes it worse.")
    relieving: Optional[str] = Field(None, description="What makes it better.")


class ClinicalHistory(BaseModel):
    """The structured record built up across the interview."""

    chief_complaint: Optional[str] = Field(None, description="Why the patient came today.")
    hpi: HPI = Field(default_factory=HPI, description="SOCRATES breakdown of the complaint.")
    past_medical: List[str] = Field(default_factory=list, description="Known chronic illnesses.")
    past_surgical: List[str] = Field(default_factory=list, description="Previous operations.")
    medications: List[str] = Field(default_factory=list, description="Current medicines named.")
    allergies: List[str] = Field(default_factory=list, description="Reported drug/food allergies.")
    family: List[str] = Field(default_factory=list, description="Relevant family history.")
    personal: Dict[str, Any] = Field(
        default_factory=dict, description="Tobacco, alcohol, diet, sleep, occupation."
    )
    ros: Dict[str, Any] = Field(
        default_factory=dict, description="Review of systems, keyed by system name."
    )


class RedFlag(BaseModel):
    """A deterministic safety trigger.

    Red flags never come from the LLM. They are rule-matched in ai/safety so the
    result is reproducible and explainable to a clinician.
    """

    rule_id: str = Field(..., description="Stable rule identifier, e.g. RESP_DISTRESS.")
    label: str = Field(..., description="Human-readable reason, shown to staff.")
    severity: FlagSeverity = Field(..., description="Urgency. `critical` interrupts the interview.")
    triggered_by: List[str] = Field(
        default_factory=list, description="Field names or answers that fired the rule."
    )
    detected_at: datetime = Field(default_factory=_utcnow, description="When the rule fired.")


class DocumentFinding(BaseModel):
    """One line item read off a document. Shapes the console's timeline table.

    One list with a discriminator, not three parallel lists: a prescription and
    a lab report arrive as the same kind of row and stay in document order.
    `kind` is what app/fhir.py switches on to pick a FHIR resource type.

    The remaining fields are shared but not all apply to every kind. A
    medication uses label + value ("Metformin", "500 mg twice daily") and leaves
    unit/ref/out_of_range empty; a lab uses all five.
    """

    kind: FindingKind = Field(
        FindingKind.lab,
        description=(
            "What this row is: diagnosis, medication, lab or procedure. "
            "Defaults to lab because every finding predating this field came "
            "from a lab report."
        ),
    )
    label: str = Field(..., description="Test, drug, diagnosis or procedure name, e.g. 'HbA1c'.")
    value: Any = Field(..., description="Measured value, dosage, or descriptive detail.")
    unit: Optional[str] = Field(None, description="Unit of measure. Empty for non-numeric rows.")
    ref: Optional[str] = Field(None, description="Reference range as printed, e.g. '<7.0'.")
    out_of_range: bool = Field(
        False, description="True renders this value in alert red on the console. Labs only."
    )


class DocumentRecord(BaseModel):
    """An uploaded document and whatever ai/ has managed to read from it.

    `doc_id` is the canonical key; `id` is emitted as an alias because the
    console's timeline reads `id`.
    """

    model_config = ConfigDict(populate_by_name=True)

    doc_id: str = Field(..., description="Server-assigned document identifier.")
    type: DocumentType = Field(DocumentType.other, description="Kind of document.")
    captured_at: datetime = Field(default_factory=_utcnow, description="When it was photographed.")
    status: DocumentStatus = Field(
        DocumentStatus.queued, description="Extraction progress. Starts queued, never blocks upload."
    )
    extracted: Dict[str, Any] = Field(
        default_factory=dict, description="Raw structured output from ai/documents."
    )
    title: Optional[str] = Field(None, description="Display title for the console timeline.")
    date: Optional[str] = Field(None, description="Date printed on the document, ISO or as-read.")
    findings: List[DocumentFinding] = Field(
        default_factory=list, description="Parsed line items for the timeline table."
    )


class ClinicalSummary(BaseModel):
    """The physician-facing summary. Draft until a doctor accepts it.

    `verified_by` staying None is what the console's 'Unverified draft' banner
    keys off. Nothing is written outbound while it is None.
    """

    chief_complaint: Optional[str] = Field(None, description="One-line reason for the visit.")
    hpi_narrative: Optional[str] = Field(
        None, description="HPI written as prose for the doctor to read at a glance."
    )
    sections: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Clinical sections keyed by name: past_history, drugs_allergies, "
            "family, personal, ros. Flattened for the console by the physician route."
        ),
    )
    document_timeline: List[DocumentRecord] = Field(
        default_factory=list, description="Uploaded documents in chronological order."
    )
    red_flags: List[RedFlag] = Field(
        default_factory=list, description="All flags raised during the session."
    )
    low_confidence_fields: List[str] = Field(
        default_factory=list,
        description=(
            "Names of fields the AI extracted with low confidence. The console "
            "renders these hedged rather than stated, so an uncertain value does "
            "not read identically to a confident one. Names match the keys used "
            "in `sections` and the flat physician payload."
        ),
    )
    generated_at: datetime = Field(default_factory=_utcnow, description="When the summary was built.")
    verified_by: Optional[str] = Field(
        None, description="Physician identifier. None means unverified draft."
    )
    verified_at: Optional[datetime] = Field(None, description="When the physician accepted it.")
    token: Optional[str] = Field(None, description="Queue token shown on the kiosk's Done screen.")
    room: Optional[str] = Field(None, description="Consulting room number shown to the patient.")


class Session(BaseModel):
    """Everything known about one kiosk encounter.

    Note the absence of any audio field. Raw audio is never persisted anywhere
    in this system; only the transcript exists, and only until the session ends.
    """

    session_id: str = Field(..., description="Server-assigned session identifier.")
    language: Language = Field(Language.en, description="Language chosen at the kiosk.")
    identity: Identity = Field(default_factory=Identity, description="Who the patient is.")
    consent: Optional[ConsentRecord] = Field(
        None, description="None until the consent screen is completed."
    )
    current_node: Optional[str] = Field(None, description="Interview node awaiting an answer.")
    answers: List[Answer] = Field(default_factory=list, description="Every answer given so far.")
    documents: List[DocumentRecord] = Field(
        default_factory=list, description="Documents uploaded this session."
    )
    history: ClinicalHistory = Field(
        default_factory=ClinicalHistory, description="Structured record built from the answers."
    )
    summary: Optional[ClinicalSummary] = Field(
        None, description="None until the summary is generated."
    )
    created_at: datetime = Field(default_factory=_utcnow, description="Session start time.")
    status: SessionStatus = Field(SessionStatus.in_progress, description="Session lifecycle state.")


# ------------------------------------------------------- request / response


class HealthResponse(BaseModel):
    """GET /health"""

    status: str = Field("ok", description="Always 'ok' when the process is serving.")


class QuestionOption(BaseModel):
    """One tappable answer tile."""

    value: str = Field(..., description="Stable machine value sent back as selected_option.")
    label: str = Field(..., description="Display text, already translated into the patient's language.")
    label_en: Optional[str] = Field(
        None,
        description=(
            "The same label in English, shown beneath it at ~60% size. None "
            "when the patient's language IS English, so the kiosk renders it "
            "once rather than twice. Family members and passing clinicians "
            "read these tiles too."
        ),
    )


class Progress(BaseModel):
    """How far through the interview the patient is."""

    answered: int = Field(0, ge=0, description="Nodes answered so far.")
    total: int = Field(0, ge=0, description="Best estimate of total nodes. May grow.")


class InterviewNode(BaseModel):
    """A question to render.

    `options` is ALWAYS present, empty list when the node is free-text only —
    the frontend's rendering breaks if the key is ever absent.
    """

    node_id: str = Field(..., description="Identifier to send back with the answer.")
    question: str = Field(..., description="Question text, translated.")
    question_en: Optional[str] = Field(
        None, description="Same question in English; None when the language is English."
    )
    options: List[QuestionOption] = Field(
        default_factory=list, description="Answer tiles. Always present, [] when free-text."
    )
    allow_free_text: bool = Field(True, description="Whether the mic is offered on this node.")
    node_type: NodeType = Field(NodeType.free_text, description="How to render this node.")
    phase: Optional[str] = Field(
        None,
        description=(
            "Patient-facing stage name, same field as AnswerResponse.phase. "
            "Present here too so the opening question carries a phase label "
            "without a second round trip."
        ),
    )


class SessionStartRequest(BaseModel):
    """POST /api/session/start"""

    language: Language = Field(
        Language.en,
        validation_alias=AliasChoices("language", "lang"),
        description="Language chosen on the kiosk's language screen.",
    )
    model_config = ConfigDict(populate_by_name=True)


class SessionStartResponse(BaseModel):
    """POST /api/session/start"""

    session_id: str = Field(..., description="Identifier for every subsequent call.")
    language: Language = Field(..., description="Language the session will be conducted in.")
    status: SessionStatus = Field(SessionStatus.in_progress, description="Lifecycle state.")
    started_at: datetime = Field(default_factory=_utcnow, description="Session start time.")
    first_question: Optional[InterviewNode] = Field(
        None, description="Opening node, so the kiosk can render without a second round trip."
    )


class ConsentRequest(BaseModel):
    """POST /api/session/{id}/consent

    Accepts the frontend's toggle names (history/documents/abha) as aliases.
    """

    model_config = ConfigDict(populate_by_name=True)

    record_history: bool = Field(
        ...,
        validation_alias=AliasChoices("record_history", "history"),
        description="Consent to record the interview.",
    )
    read_documents: bool = Field(
        ...,
        validation_alias=AliasChoices("read_documents", "documents"),
        description="Consent to read uploaded documents.",
    )
    link_abha: bool = Field(
        ...,
        validation_alias=AliasChoices("link_abha", "abha"),
        description="Consent to link to the ABHA record.",
    )
    language: Language = Field(
        Language.en,
        validation_alias=AliasChoices("language", "lang"),
        description="Language consent was played in.",
    )


class KnownFieldsRequest(BaseModel):
    """POST /api/session/{id}/fields

    The kiosk collects identity and consent on its own dedicated screens
    (name, age, sex, the three consent toggles) before the generic interview
    loop starts. Without handing those over, the state machine sees them as
    unfilled and asks for them all over again — a patient who has just typed
    their name is immediately asked "What is your name?".

    Values here are already structured, so they are stored at confidence 1.0
    with `touch` provenance and cost no model call.
    """

    fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Field name to value, using the names in ai/interview/nodes.py.",
    )


class KnownFieldsResponse(BaseModel):
    """POST /api/session/{id}/fields"""

    ok: bool = Field(True, description="Whether the fields were stored.")
    extracted: List[ExtractedField] = Field(
        default_factory=list, description="Everything understood so far, cumulative."
    )
    red_flag: Optional[RedFlag] = Field(
        None,
        description=(
            "Safety rules run on seeded fields too. A patient whose ABHA "
            "profile or intake screen carries a danger sign must not have to "
            "wait for the interview loop to reach it."
        ),
    )


class ConsentResponse(BaseModel):
    """POST /api/session/{id}/consent"""

    ok: bool = Field(True, description="Whether consent was recorded.")
    consent: ConsentRecord = Field(..., description="What was stored, echoed back for the audit log.")


class SessionEndResponse(BaseModel):
    """POST /api/session/{id}/end"""

    ok: bool = Field(True, description="Whether the session closed cleanly.")
    session_id: str = Field(..., description="Session that was closed.")
    transcripts_purged: bool = Field(
        True, description="Raw transcripts are deleted on end. Audio was never stored at all."
    )


class AnswerRequest(BaseModel):
    """POST /api/interview/{id}/answer

    Field aliases accept the frontend's {node_id, value, text, lang} exactly as
    client.js already sends it.
    """

    model_config = ConfigDict(populate_by_name=True)

    node_id: str = Field(..., description="Node being answered.")
    transcript: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("transcript", "text", "raw_transcript"),
        description="What the patient said, if they spoke.",
    )
    selected_option: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("selected_option", "value", "option"),
        description="Option value, if the patient tapped a tile.",
    )
    selected_options: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("selected_options", "values", "options"),
        description=(
            "Option values for a multi_choice node, where the patient can tap "
            "several tiles (the ROS screening question). Empty for every "
            "single-choice node, which uses selected_option instead."
        ),
    )
    language: Language = Field(
        Language.en,
        validation_alias=AliasChoices("language", "lang"),
        description="Language of this answer.",
    )


class AnswerResponse(BaseModel):
    """POST /api/interview/{id}/answer and GET /api/interview/{id}/node/{node_id}

    One shape covers three outcomes so the frontend has a single branch:
      - another question  -> node_id/question/options populated, done False
      - interview finished -> done True
      - safety stop        -> red_flag populated, handled before anything else

    red_flag is an object rather than a bool because the emergency screen
    renders its reason text. It is still truthy, so a boolean check works.
    """

    node_id: Optional[str] = Field(None, description="Next node to render. None when done.")
    question: Optional[str] = Field(None, description="Next question text, translated.")
    question_en: Optional[str] = Field(
        None,
        description=(
            "The same question in English, rendered beneath it at ~60% size. "
            "None when the patient's language IS English. The interview screen "
            "is seen ~25 times a session and is what a relative or a passing "
            "doctor most needs to be able to read."
        ),
    )
    options: List[QuestionOption] = Field(
        default_factory=list,
        description="Answer tiles. ALWAYS present, [] when empty. Never omitted.",
    )
    allow_free_text: bool = Field(True, description="Whether to offer the mic.")
    node_type: NodeType = Field(NodeType.free_text, description="How to render the node.")
    progress: Progress = Field(default_factory=Progress, description="Interview progress.")
    phase: Optional[str] = Field(
        None,
        description=(
            "Patient-facing name of the stage the interview is in, passed "
            "through from the current node's phase_label. The kiosk shows this "
            "instead of a progress count: the interview has no fixed length, "
            "so any count desyncs. None when the interview has ended — the "
            "kiosk then renders nothing rather than falling back to a count."
        ),
    )
    extracted: List[ExtractedField] = Field(
        default_factory=list,
        description=(
            "Every field understood so far this session, cumulative — not just "
            "this turn — because the kiosk's understanding panel accumulates. "
            "Each carries its own confidence as a float so the panel can hedge "
            "anything below 0.7, and its source so a tapped answer is not shown "
            "as though it were transcribed. Contains structured fields ONLY; "
            "raw transcripts never appear in this payload."
        ),
    )
    red_flag: Optional[RedFlag] = Field(
        None, description="Set when a safety rule fired. Interrupts the interview immediately."
    )
    done: bool = Field(False, description="True when no questions remain.")
    terminal_reason: Optional[TerminalReason] = Field(
        None,
        description=(
            "Why the interview ended, when done is True. `completed` means every "
            "stage was answered; `red_flag` means a safety rule stopped it early. "
            "None while the interview is still running."
        ),
    )


class DocumentUploadResponse(BaseModel):
    """POST /api/documents/{id}/upload

    Returns the moment the bytes land. Extraction happens afterwards — the
    patient is never held behind OCR.
    """

    doc_id: str = Field(..., description="Canonical document identifier.")
    document_id: str = Field(..., description="Alias of doc_id; the frontend reads this name.")
    status: DocumentStatus = Field(
        DocumentStatus.queued, description="Always queued on ack. Poll GET /documents/{id}."
    )


class DocumentListResponse(BaseModel):
    """GET /api/documents/{id}"""

    session_id: str = Field(..., description="Session these documents belong to.")
    documents: List[DocumentRecord] = Field(
        default_factory=list, description="All documents with current extraction status."
    )


class PhysicianQueueItem(BaseModel):
    """One row in the physician's waiting list. Red-flagged rows sort first."""

    session_id: str = Field(..., description="Session to open.")
    token: Optional[str] = Field(None, description="Queue token, e.g. 'A-42'.")
    name: Optional[str] = Field(None, description="Patient name.")
    age: Optional[int] = Field(None, description="Patient age.")
    sex: Optional[str] = Field(None, description="Display sex, e.g. 'F'.")
    complaint: Optional[str] = Field(None, description="One-line chief complaint.")
    red_flag: Optional[str] = Field(
        None, description="Flag label, or None. A string so the row can name the reason."
    )
    waiting_since: Optional[str] = Field(None, description="Arrival time, HH:MM.")


class PhysicianPatient(BaseModel):
    """Patient header block on the console."""

    name: Optional[str] = Field(None, description="Patient name.")
    age: Optional[int] = Field(None, description="Patient age.")
    sex: Optional[str] = Field(None, description="Display sex.")
    abha: Optional[str] = Field(None, description="ABHA number, or None.")


class FlatSummary(BaseModel):
    """ClinicalSummary.sections flattened into the seven keys the console reads.

    The console renders these as inline-editable fields in clinical order.
    """

    chief_complaint: str = Field("", description="Reason for the visit.")
    hpi: str = Field("", description="History of present illness, as prose.")
    past_history: str = Field("", description="Past medical and surgical history.")
    drugs_allergies: str = Field("", description="Current medications and allergies.")
    family: str = Field("", description="Family history.")
    personal: str = Field("", description="Personal and social history.")
    ros: str = Field("", description="Review of systems.")


class PhysicianCaseResponse(BaseModel):
    """GET /api/physician/{id} — everything the console renders for one patient."""

    session_id: str = Field(..., description="Session being reviewed.")
    patient: PhysicianPatient = Field(..., description="Patient header.")
    summary: FlatSummary = Field(..., description="Flattened clinical sections.")
    documents: List[DocumentRecord] = Field(
        default_factory=list, description="Document timeline with findings."
    )
    red_flags: List[RedFlag] = Field(
        default_factory=list,
        description=(
            "Flags as of RIGHT NOW, read live from the clinical record — never "
            "from the stored summary snapshot. A flag raised after the summary "
            "was generated must appear here, or this view and the queue "
            "disagree and the doctor trusts this one."
        ),
    )
    low_confidence_fields: List[str] = Field(
        default_factory=list,
        description=(
            "Fields the AI was unsure of. The console hedges these the same way "
            "the kiosk does, so an uncertain value never reads as a confident one."
        ),
    )
    mocked_fields: List[str] = Field(
        default_factory=list,
        description=(
            "Names of fields in this payload that are demo values, not real "
            "patient data — currently the demographics. Stated explicitly so "
            "the console can label them and nobody demonstrates invented data "
            "believing it was collected."
        ),
    )
    fhir: Dict[str, Any] = Field(
        default_factory=dict, description="FHIR R4 bundle, embedded so the panel needs no second call."
    )
    verified_by: Optional[str] = Field(
        None, description="None means the console shows the unverified-draft banner."
    )
    verified_at: Optional[datetime] = Field(None, description="When it was accepted.")


class VerifyRequest(BaseModel):
    """POST /api/physician/{id}/verify"""

    action: VerifyAction = Field(..., description="accept, amend or reject.")
    physician_id: Optional[str] = Field(
        None, description="Who acted. Written to the audit log verbatim."
    )
    amendments: Dict[str, str] = Field(
        default_factory=dict, description="Field-name to new-value map, for action=amend."
    )
    reason: Optional[str] = Field(None, description="Why, for action=reject.")


class VerifyResponse(BaseModel):
    """POST /api/physician/{id}/verify"""

    ok: bool = Field(True, description="Whether the action was applied.")
    status: SessionStatus = Field(..., description="Session status after the action.")
    verified_by: Optional[str] = Field(None, description="Physician identifier, once accepted.")
    verified_at: Optional[datetime] = Field(None, description="Acceptance timestamp.")


class LoginRequest(BaseModel):
    """POST /api/auth/login"""

    username: str = Field(..., description="Clinician username.")
    password: str = Field(
        ...,
        description=(
            "Plaintext, over TLS only. Hashed with bcrypt on arrival and never "
            "stored, logged or returned in any payload."
        ),
    )


class LoginResponse(BaseModel):
    """POST /api/auth/login

    Carries no password material of any kind, not even a hash.
    """

    access: str = Field(..., description="Access token, 15 minutes. Hold in memory only.")
    refresh: str = Field(..., description="Refresh token, 8 hours. Revocable via /auth/logout.")
    role: str = Field(..., description="doctor | triage | admin.")
    name: str = Field(..., description="Display name for the console header.")
    expires_in: int = Field(..., description="Access token lifetime in seconds.")


class RefreshRequest(BaseModel):
    """POST /api/auth/refresh and /api/auth/logout"""

    refresh: str = Field(..., description="A refresh token issued by /auth/login.")


class RefreshResponse(BaseModel):
    """POST /api/auth/refresh"""

    access: str = Field(..., description="A fresh access token.")
    role: str = Field(..., description="doctor | triage | admin.")
    name: str = Field(..., description="Display name.")
    expires_in: int = Field(..., description="Access token lifetime in seconds.")


class LogoutResponse(BaseModel):
    """POST /api/auth/logout

    Always ok, whether or not the token was valid — a truthful answer would let
    someone probe tokens against this endpoint.
    """

    ok: bool = Field(True, description="Always True.")


class MeResponse(BaseModel):
    """GET /api/auth/me"""

    username: str = Field(..., description="Clinician username.")
    role: str = Field(..., description="doctor | triage | admin.")
    name: str = Field(..., description="Display name.")


class AbhaVerifyRequest(BaseModel):
    """POST /api/identity/abha/verify — MOCKED, see app/routers/identity.py."""

    abha_id: str = Field(..., description="14-digit ABHA number, with or without separators.")


class AbhaVerifyResponse(BaseModel):
    """POST /api/identity/abha/verify — MOCKED. No real ABDM call is made."""

    mocked: bool = Field(True, description="Always True. This is not a real verification.")
    verified: bool = Field(..., description="Whether the number passed the format check.")
    abha_id: Optional[str] = Field(None, description="Normalised ABHA number.")
    identity: Optional[Identity] = Field(None, description="Fabricated demo patient record.")
    notice: str = Field(
        "MOCKED: no ABDM gateway call was made.",
        description="Carried in the payload so a demo can never be mistaken for real verification.",
    )

// Owner: Ranjith
// Every backend call lives in this file. Nothing else in the app calls fetch().
//
// VITE_USE_MOCKS=true serves everything from /mocks/sample_session.json with a
// 300ms delay, for walking the UI with the backend stopped.
//
// Mocks used to default ON, which quietly meant the kiosk never called app/ at
// all — a fully mocked session looked exactly like a real one, so none of the
// backend work was visible here. Opt IN now: real API is the default.
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

// The /api suffix is required: app/main.py mounts every router under
// API_PREFIX="/api" while the helpers below request bare paths such as
// "/session/start". Without it every single call 404s.
const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api';
const MOCK_DELAY = 300;

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

let mockPromise = null;
function loadMocks() {
  if (!mockPromise) {
    mockPromise = fetch('/mocks/sample_session.json').then((r) => {
      if (!r.ok) throw new Error(`mock fixture missing (${r.status})`);
      return r.json();
    });
  }
  return mockPromise;
}

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: isForm ? undefined : { 'Content-Type': 'application/json' },
    body: isForm ? body : body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${path} failed: ${res.status}`);
  if (res.status === 204) return null;
  return res.json();
}

/* ---------------------------------------------------------------- mock state */
// Where the mocked interview has got to. Reset whenever a session starts.
let mockCursor = 0;

function localise(field, lang) {
  // Mock question/option text is stored per language; fall back to English.
  if (field == null) return '';
  if (typeof field === 'string') return field;
  return field[lang] ?? field.en ?? '';
}

function shapeNode(node, lang) {
  return {
    node_id: node.node_id,
    question: localise(node.question, lang),
    options: (node.options ?? []).map((o) => ({
      value: o.value,
      label: localise(o.label, lang),
    })),
    allow_free_text: node.allow_free_text !== false,
  };
}

/* -------------------------------------------------------------------- session */

export async function startSession() {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    mockCursor = 0;
    return { ...data.session };
  }
  return request('/session/start', { method: 'POST' });
}

/**
 * Hand the backend the fields the kiosk already collected on its own screens
 * (name, age, sex, consent). Without this the state machine treats them as
 * unanswered and asks for them again — the patient types their name on the
 * name screen and is then asked "What is your name?".
 *
 * Costs no model call: these values are already structured.
 */
export async function recordKnownFields(sessionId, fields) {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    return { ok: true, extracted: [] };
  }
  return request(`/session/${sessionId}/fields`, { method: 'POST', body: { fields } });
}

export async function recordConsent(sessionId, consent) {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    return { ok: true, consent };
  }
  return request(`/session/${sessionId}/consent`, { method: 'POST', body: consent });
}

export async function endSession(sessionId) {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    return { ok: true };
  }
  return request(`/session/${sessionId}/end`, { method: 'POST' });
}

/* ------------------------------------------------------------------ interview */

/**
 * Submit an answer and get the next question.
 * Returns { done } | { red_flag } | a question node.
 * The Interview screen renders whatever comes back — it holds no clinical content.
 */
export async function submitAnswer(sessionId, payload) {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    const lang = payload?.lang ?? 'en';

    const trigger = data.red_flag_when;
    if (trigger && payload?.node_id === trigger.node_id && payload?.value === trigger.value) {
      return { red_flag: { reason: trigger.reason, code: trigger.code } };
    }

    const node = data.interview[mockCursor];
    mockCursor += 1;
    if (!node) return { done: true };
    return shapeNode(node, lang);
  }
  return request(`/interview/${sessionId}/answer`, { method: 'POST', body: payload });
}

/* ------------------------------------------------------------------ documents */

export async function uploadDocument(sessionId, blob, filename = 'page.jpg') {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    return { document_id: `mock-doc-${Math.random().toString(36).slice(2, 8)}`, status: 'received' };
  }
  const form = new FormData();
  form.append('file', blob, filename);
  return request(`/documents/${sessionId}/upload`, { method: 'POST', body: form, isForm: true });
}

/* -------------------------------------------------------------------- summary */

export async function generateSummary(sessionId) {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    return data.summary;
  }
  return request(`/summary/${sessionId}/generate`, { method: 'POST' });
}

export async function fetchSummary(sessionId) {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    return data.summary;
  }
  return request(`/summary/${sessionId}`);
}

/* ------------------------------------------------------------------ physician */

export async function fetchPatientList() {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    return data.physician.patients;
  }
  return request('/physician/queue');
}

export async function fetchCase(sessionId) {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    const found = data.physician.cases[sessionId];
    return found ?? data.physician.cases[Object.keys(data.physician.cases)[0]];
  }
  return request(`/physician/${sessionId}`);
}

export async function updateCase(sessionId, patch) {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    return { ok: true, patch };
  }
  return request(`/physician/${sessionId}`, { method: 'PUT', body: patch });
}

export async function confirmCase(sessionId) {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    return { ok: true, status: 'confirmed' };
  }
  return request(`/physician/${sessionId}/confirm`, { method: 'POST' });
}

export async function rejectCase(sessionId, reason) {
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    return { ok: true, status: 'rejected', reason };
  }
  return request(`/physician/${sessionId}/reject`, { method: 'POST', body: { reason } });
}

/* --------------------------------------------------------------- identity */

/**
 * TODO: MOCKED. Real ABHA / Aadhaar verification must happen server-side —
 * the kiosk must never hold or transmit these numbers directly. This resolves
 * true for any input of the expected length purely so the flow is walkable.
 */
export async function verifyIdentity(kind, number) {
  console.warn('[api] verifyIdentity is MOCKED — no real verification performed');
  await wait(600);
  const expected = kind === 'abha' ? 14 : 12;
  return { verified: number.length === expected, kind, masked: `••••${number.slice(-4)}` };
}

export const usingMocks = USE_MOCKS;

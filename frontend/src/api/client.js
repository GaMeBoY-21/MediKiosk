// Owner: Ranjith
// Every backend call lives in this file. Nothing else in the app calls fetch().
//
// VITE_USE_MOCKS=true serves everything from /mocks/sample_session.json with a
// 300ms delay, for walking the UI with the backend stopped.
//
// Mocks used to default ON, which quietly meant the kiosk never called app/ at
// all — a fully mocked session looked exactly like a real one, so none of the
// backend work was visible here. Opt IN now: real API is the default.
// Tokens live in memory only — see authStore.js for why.
import { accessToken, clearSession, refreshToken, setSession } from '../physician/authStore.js';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

// VITE_REPLAY=true serves a real recorded session from /replay/session.json:
// no network, no API quota, and the kiosk behaves exactly as it did live.
//
// This exists because the free Gemini tier has a hard daily cap and venue wifi
// fails. A dead kiosk in front of judges ends the round. The recording is a
// genuine session — real model output, real red flag — not hand-written mock
// text, so what is demonstrated is what the system actually did.
//
// The REPLAY badge (see Kiosk.jsx) is deliberately impossible to miss: replay
// must never be mistaken for a live run.
// Runtime-switchable, not a build-time constant. It starts from the Vite flag
// and can be turned on mid-session by the Ctrl+Shift+R handler (see
// components/ReplaySwitch.jsx) with no reload and no restart — because the
// moment you need it, restarting the stack means standing in front of judges
// watching a terminal.
//
// One-way on purpose: there is no way back to live from here. Coming back
// would mean a half-recorded, half-live session, and nobody could say which
// screen was which afterwards.
let replayActive = import.meta.env.VITE_REPLAY === 'true';
const replayWatchers = new Set();

/** Whether the app is serving the recording. Read it, never cache it. */
export function isReplay() {
  return replayActive;
}

/** Subscribe to the switch. Returns an unsubscribe function. */
export function subscribeReplay(listener) {
  replayWatchers.add(listener);
  return () => replayWatchers.delete(listener);
}

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

/** Thrown on 401 so callers can route to the login screen instead of showing
 *  a generic failure. */
export class Unauthorized extends Error {
  constructor(path) {
    super(`unauthorized: ${path}`);
    this.name = 'Unauthorized';
  }
}

function buildHeaders(isForm) {
  const headers = isForm ? {} : { 'Content-Type': 'application/json' };
  const token = accessToken();
  // Bearer, not a cookie: nothing here should ride along automatically on a
  // cross-site request.
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function request(path, { method = 'GET', body, isForm = false, retry = true } = {}) {
  const send = () =>
    fetch(`${BASE}${path}`, {
      method,
      headers: buildHeaders(isForm),
      body: isForm ? body : body ? JSON.stringify(body) : undefined,
    });

  let res = await send();

  // Access tokens last 15 minutes; a doctor reading one case can easily cross
  // that. Spend the refresh token once, transparently, before giving up and
  // sending them back to the login screen.
  if (res.status === 401 && retry && refreshToken()) {
    const renewed = await renewAccess();
    if (renewed) res = await send();
  }

  if (res.status === 401) {
    clearSession();
    throw new Unauthorized(path);
  }
  if (!res.ok) throw new Error(`${method} ${path} failed: ${res.status}`);
  if (res.status === 204) return null;
  return res.json();
}

/* -------------------------------------------------------------------- auth */

export async function login(username, password) {
  if (replayActive) {
    // Offline demo. The login form is still shown and still has to be filled,
    // so the flow demonstrates honestly, but there is no server to verify
    // against. Safe only because replay serves a recorded session and nothing
    // else: no live patient data exists in this mode, and the REPLAY badge is
    // on screen throughout.
    await wait(MOCK_DELAY);
    if (!username || !password) throw new Error('Invalid username or password.');
    const session = {
      access: 'replay',
      refresh: 'replay',
      role: 'doctor',
      name: 'Dr. A. Mehta (replay)',
      expires_in: 3600,
    };
    setSession({ ...session, username });
    return session;
  }
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    // The server deliberately returns one message for every failure mode.
    // Show exactly that; do not add detail it withheld on purpose.
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.detail || 'Invalid username or password.');
    err.status = res.status;
    throw err;
  }
  const data = await res.json();
  setSession({ ...data, username });
  return data;
}

/** Exchange the refresh token for a new access token. Returns true on success. */
export async function renewAccess() {
  if (replayActive) return true;
  const refresh = refreshToken();
  if (!refresh) return false;
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) {
      clearSession();
      return false;
    }
    setSession(await res.json());
    return true;
  } catch {
    clearSession();
    return false;
  }
}

export async function logout() {
  if (replayActive) {
    clearSession();
    return;
  }
  const refresh = refreshToken();
  // Clear locally first: even if the network call fails, this browser must
  // stop holding a usable token.
  clearSession();
  if (!refresh) return;
  try {
    await fetch(`${BASE}/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
  } catch {
    // Best effort. The token still expires on its own.
  }
}

let replayPromise = null;
function loadReplay() {
  if (!replayPromise) {
    replayPromise = fetch('/replay/session.json').then((r) => {
      if (!r.ok) throw new Error(`replay fixture missing (${r.status})`);
      return r.json();
    });
  }
  return replayPromise;
}

// How far through the recorded interview we are. Reset when a session starts.
let replayCursor = 0;

/**
 * Turn on replay for the rest of this session. Idempotent.
 *
 * Resets the cursor and drops the cached fixture so the recording plays from
 * its first turn, whatever the live session had already done.
 */
export function enableReplay() {
  if (replayActive) return false;
  replayActive = true;
  replayCursor = 0;
  replayPromise = null;
  for (const listener of replayWatchers) {
    try {
      listener(true);
    } catch (e) {
      console.warn('[replay] listener failed:', e);
    }
  }
  console.warn('[replay] switched to the recorded session at runtime');
  return true;
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

/** Refuse to build a URL around a session id that does not exist yet.
 *
 *  Every path below interpolates the id, so a null one produced a real request
 *  to /api/session/null/consent and a 404 that read like a backend fault. The
 *  screens are gated on a live id now (see NEEDS_SESSION in Kiosk.jsx); this is
 *  the backstop that keeps the invariant enforceable rather than remembered.
 *  It throws rather than resolving quietly — a caller that has lost track of
 *  the session must fail visibly, not silently skip the write. */
function requireSession(sessionId, what) {
  if (sessionId) return sessionId;
  throw new Error(`${what} called with no session id — the session is not open yet`);
}

/* -------------------------------------------------------------------- session */

export async function startSession(language = 'en') {
  if (replayActive) {
    const d = await loadReplay();
    replayCursor = 0;
    return d.kiosk.session;
  }
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    mockCursor = 0;
    return { ...data.session };
  }
  // The language MUST go with this call. Without it the session is created as
  // English, and the opening question the backend generates and stores comes
  // back in English no matter what the patient picked afterwards.
  return request('/session/start', { method: 'POST', body: { language } });
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
  requireSession(sessionId, 'recordKnownFields');
  if (replayActive) {
    const d = await loadReplay();
    return d.kiosk.fields;
  }
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    return { ok: true, extracted: [] };
  }
  return request(`/session/${sessionId}/fields`, { method: 'POST', body: { fields } });
}

export async function recordConsent(sessionId, consent) {
  requireSession(sessionId, 'recordConsent');
  if (replayActive) return { ok: true, consent };
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    return { ok: true, consent };
  }
  return request(`/session/${sessionId}/consent`, { method: 'POST', body: consent });
}

export async function endSession(sessionId) {
  requireSession(sessionId, 'endSession');
  if (replayActive) return { ok: true };
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
  requireSession(sessionId, 'submitAnswer');
  if (replayActive) {
    const d = await loadReplay();
    const recorded = d.kiosk.answers;
    // Walk the recording in order. Whatever the patient says or taps, the
    // questions play back exactly as they were answered live — including the
    // red flag the real session raised on the last turn.
    const step = recorded[replayCursor];
    replayCursor += 1;
    if (!step) return { done: true, terminal_reason: 'completed', extracted: [] };
    return step.response;
  }
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
  requireSession(sessionId, 'uploadDocument');
  if (replayActive) return { doc_id: 'replay-doc', document_id: 'replay-doc', status: 'queued' };
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
  requireSession(sessionId, 'generateSummary');
  if (replayActive) {
    const d = await loadReplay();
    return d.kiosk.summary;
  }
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    return data.summary;
  }
  return request(`/summary/${sessionId}/generate`, { method: 'POST' });
}

export async function fetchSummary(sessionId) {
  requireSession(sessionId, 'fetchSummary');
  if (replayActive) {
    const d = await loadReplay();
    return d.physician.summary;
  }
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    return data.summary;
  }
  return request(`/summary/${sessionId}`);
}

/* ------------------------------------------------------------------ physician */

export async function fetchPatientList() {
  if (replayActive) {
    const d = await loadReplay();
    return d.physician.queue;
  }
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    return data.physician.patients;
  }
  return request('/physician/queue');
}

export async function fetchCase(sessionId) {
  if (replayActive) {
    const d = await loadReplay();
    return d.physician.case;
  }
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    const found = data.physician.cases[sessionId];
    return found ?? data.physician.cases[Object.keys(data.physician.cases)[0]];
  }
  return request(`/physician/${sessionId}`);
}

export async function fetchCaseByToken(token) {
  const normalized = String(token || '').trim().toUpperCase();
  if (!normalized) throw new Error('Enter a patient token.');
  if (replayActive) {
    const d = await loadReplay();
    const match = d.physician.queue.find((p) => p.token?.toUpperCase() === normalized);
    if (!match) throw new Error(`No patient found for ${normalized}.`);
    return d.physician.case;
  }
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    const data = await loadMocks();
    const match = data.physician.patients.find((p) => p.token?.toUpperCase() === normalized);
    if (!match) throw new Error(`No patient found for ${normalized}.`);
    const found = data.physician.cases[match.session_id];
    return found ?? data.physician.cases[Object.keys(data.physician.cases)[0]];
  }
  return request(`/physician/token/${encodeURIComponent(normalized)}`);
}

export async function updateCase(sessionId, patch) {
  if (replayActive) return { ok: true, patch };
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    return { ok: true, patch };
  }
  return request(`/physician/${sessionId}`, { method: 'PUT', body: patch });
}

export async function confirmCase(sessionId) {
  if (replayActive) return { ok: true, status: 'verified' };
  if (USE_MOCKS) {
    await wait(MOCK_DELAY);
    return { ok: true, status: 'confirmed' };
  }
  return request(`/physician/${sessionId}/confirm`, { method: 'POST' });
}

export async function rejectCase(sessionId, reason) {
  if (replayActive) return { ok: true, status: 'rejected', reason };
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

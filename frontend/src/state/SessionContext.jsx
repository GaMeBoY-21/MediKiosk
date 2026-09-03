// Owner: Ranjith
// The whole patient session lives here. No Redux.
//
// Screen navigation is in this context too, because the idle timeout has to be
// able to wipe state and jump to Idle from outside any screen.

import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';
import { DEFAULT_LANG } from '../i18n/strings.js';
import { startSession } from '../api/client.js';

export const SCREENS = {
  IDLE: 'idle',
  LANGUAGE: 'language',
  IDENTIFY: 'identify',
  ABHA: 'abha',
  AADHAAR: 'aadhaar',
  NAME: 'name',
  AGE: 'age',
  SEX: 'sex',
  CONSENT: 'consent',
  CONSENT_DECLINED: 'consent-declined',
  COMPLAINT: 'complaint',
  INTERVIEW: 'interview',
  DOCUMENTS: 'documents',
  CONFIRM: 'confirm',
  DONE: 'done',
  EMERGENCY: 'emergency',
};

/** Where session creation has got to.
 *
 *  POST /api/session/start generates the opening question through the model,
 *  so it takes anywhere from one to fifteen seconds. Everything downstream of
 *  it — consent, seeding, the interview, the summary, ending the session —
 *  addresses the session by id, so the kiosk has to be able to say "not yet"
 *  rather than send `null` down the wire. `idle` is not "no session": it is
 *  "nobody has asked for one yet". */
export const SESSION_STATUS = {
  IDLE: 'idle',
  STARTING: 'starting',
  READY: 'ready',
  FAILED: 'failed',
};

const INITIAL = {
  language: DEFAULT_LANG,
  // Whether the patient has actually PICKED a language, as opposed to us
  // sitting on the default. Without this the app could not tell "English
  // because they chose it" from "English because nobody has chosen yet", so
  // pre-selection screens rendered in whatever happened to be in state.
  languageChosen: false,
  sessionId: null,
  sessionStatus: SESSION_STATUS.IDLE,
  patient: { name: '', age: '', sex: '', idKind: null, idMasked: null },
  consentGiven: null, // null = not asked, false = refused
  consentOptions: { history: true, documents: true, abha: false },
  currentNode: null,
  answers: [],
  // Every field the backend has understood so far, cumulative. Held here
  // rather than inside the Interview screen because the Confirm screen has to
  // read it too: it is what tells Confirm about fields nobody was asked for
  // directly, like the ones reconcile.py derives.
  extracted: [],
  documents: [],
  summary: null,
  redFlag: null,
};

// Node ids whose question has already been read aloud this session.
// A plain Set in a ref, not state: marking one spoken must not trigger a
// re-render, and speaking is a side effect on the device rather than
// something the UI renders.

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [state, setState] = useState(INITIAL);

  // The navigation stack is the single source of truth; the current screen is
  // derived from it. Keeping `screen` as separate state meant back() had to
  // call setScreen from inside a setHistory updater, which StrictMode can
  // invoke twice.
  const [history, setHistory] = useState([SCREENS.IDLE]);
  const screen = history[history.length - 1];

  const go = useCallback((next) => {
    setHistory((h) => [...h, next]);
  }, []);

  const back = useCallback(() => {
    setHistory((h) => (h.length <= 1 ? [SCREENS.IDLE] : h.slice(0, -1)));
  }, []);

  // In flight already? A ref rather than reading sessionStatus, because two
  // callers in the same tick would both still see `idle` in state and open two
  // sessions — the patient's answers would then be split across two rows and
  // the doctor would get half an interview.
  const starting = useRef(false);

  // Wipe everything. Patient data must never sit on screen for the next person.
  const reset = useCallback(() => {
    starting.current = false;
    setState(INITIAL);
    setHistory([SCREENS.IDLE]);
  }, []);

  const patch = useCallback((fields) => {
    setState((s) => ({ ...s, ...fields }));
  }, []);

  const setLanguage = useCallback(
    (language) => patch({ language, languageChosen: true }),
    [patch],
  );
  /** Open the patient's session and hold the id. The ONLY way sessionId is
   *  ever set — there is deliberately no public setter beside it.
   *
   *  It used to be a fire-and-forget effect in Kiosk.jsx that no screen waited
   *  on, so consent, the seeding call and the first interview answer all went
   *  out addressed to `null` whenever the model took more than a few seconds
   *  to produce the opening question. Resolving with the id (rather than only
   *  writing it to state) lets a caller sequence off it directly; the status
   *  is what the screens gate on. */
  const beginSession = useCallback(async (language) => {
    if (starting.current) return null;
    starting.current = true;
    setState((s) => ({ ...s, sessionStatus: SESSION_STATUS.STARTING }));
    try {
      const opened = await startSession(language);
      const sessionId = opened?.session_id ?? null;
      // A 200 with no id is still a failed start. Treating it as success is
      // what put the string "null" into every URL that followed.
      if (!sessionId) throw new Error('/session/start returned no session_id');
      setState((s) => ({ ...s, sessionId, sessionStatus: SESSION_STATUS.READY }));
      return sessionId;
    } catch (e) {
      // Left `true`: a retry belongs to reset(), not to the next render.
      setState((s) => ({ ...s, sessionStatus: SESSION_STATUS.FAILED }));
      throw e;
    }
  }, []);

  const setSummary = useCallback((summary) => patch({ summary }), [patch]);
  const setCurrentNode = useCallback((currentNode) => patch({ currentNode }), [patch]);

  const setPatient = useCallback((fields) => {
    setState((s) => ({ ...s, patient: { ...s.patient, ...fields } }));
  }, []);

  const setConsent = useCallback((given, options) => {
    setState((s) => ({
      ...s,
      consentGiven: given,
      consentOptions: options ?? s.consentOptions,
    }));
  }, []);

  /** Record an answer, replacing any earlier answer to the same node. */
  // One row per QUESTION, not per node. Deduplicating by node_id silently
  // overwrote: every follow-up in the history-of-present-illness stage carries
  // node_id "hpi", so seven answers collapsed into one and the Confirm screen
  // showed two rows for a ten-question interview. The key still has to
  // deduplicate, though, or the edit pencil would append a second row instead
  // of correcting the first.
  const answerKey = (a) => a.key || `${a.node_id}:${a.question}`;

  const addAnswer = useCallback((answer) => {
    setState((s) => {
      const key = answerKey(answer);
      const existing = s.answers.findIndex((a) => answerKey(a) === key);
      if (existing === -1) return { ...s, answers: [...s.answers, answer] };
      const answers = [...s.answers];
      // Keep any fields already attributed to this row: re-answering a
      // question does not un-derive what it derived.
      answers[existing] = { ...answers[existing], ...answer };
      return { ...s, answers };
    });
  }, []);

  /** Record which clinical fields an answer turned out to fill.
   *
   * Attribution happens after the fact because the fields are only known once
   * the backend has replied. It is what lets Confirm show a derived field
   * beside the answer it came from rather than as a row of its own that the
   * patient was never asked. */
  const noteAnswerFields = useCallback((key, fields) => {
    if (!key || !fields?.length) return;
    setState((s) => {
      const i = s.answers.findIndex((a) => answerKey(a) === key);
      if (i === -1) return s;
      const answers = [...s.answers];
      // First claimer wins. The seeded batch that opens the interview carries
      // the identity fields too, and those rows already account for them —
      // counting them twice would hide a genuinely dropped field behind a
      // total that still looked right.
      const claimed = new Set(answers.flatMap((a, j) => (j === i ? [] : a.fields || [])));
      const merged = [
        ...new Set([...(answers[i].fields || []), ...fields.filter((f) => !claimed.has(f))]),
      ];
      answers[i] = { ...answers[i], fields: merged };
      return { ...s, answers };
    });
  }, []);

  const setExtracted = useCallback((extracted) => {
    setState((s) => (Array.isArray(extracted) ? { ...s, extracted } : s));
  }, []);

  const addDocument = useCallback((doc) => {
    setState((s) => ({ ...s, documents: [...s.documents, doc] }));
  }, []);

  const updateDocument = useCallback((localId, fields) => {
    setState((s) => ({
      ...s,
      documents: s.documents.map((d) => (d.localId === localId ? { ...d, ...fields } : d)),
    }));
  }, []);

  const removeDocument = useCallback((localId) => {
    setState((s) => {
      const doomed = s.documents.find((d) => d.localId === localId);
      if (doomed?.url) URL.revokeObjectURL(doomed.url);
      return { ...s, documents: s.documents.filter((d) => d.localId !== localId) };
    });
  }, []);

  const raiseRedFlag = useCallback(
    (redFlag) => {
      setState((s) => ({ ...s, redFlag }));
      go(SCREENS.EMERGENCY);
    },
    [go],
  );

  const clearRedFlag = useCallback(() => patch({ redFlag: null }), [patch]);

  // Auto-speak bookkeeping. Keyed on node id, not on the sentence: keying
  // on text re-spoke the question on back-navigation and after any
  // remount, and stayed silent when two nodes happened to share wording.
  const spokenNodes = useRef(new Set());
  const hasSpoken = useCallback((nodeId) => spokenNodes.current.has(nodeId), []);
  const markSpoken = useCallback((nodeId) => {
    if (nodeId) spokenNodes.current.add(nodeId);
  }, []);

  const value = useMemo(
    () => ({
      ...state,
      screen,
      go,
      back,
      reset,
      setLanguage,
      beginSession,
      setPatient,
      setConsent,
      setCurrentNode,
      addAnswer,
      noteAnswerFields,
      setExtracted,
      addDocument,
      updateDocument,
      removeDocument,
      setSummary,
      raiseRedFlag,
      clearRedFlag,
      hasSpoken,
      markSpoken,
    }),
    [
      state,
      screen,
      go,
      back,
      reset,
      setLanguage,
      beginSession,
      setPatient,
      setConsent,
      setCurrentNode,
      addAnswer,
      noteAnswerFields,
      setExtracted,
      addDocument,
      updateDocument,
      removeDocument,
      setSummary,
      raiseRedFlag,
      clearRedFlag,
      hasSpoken,
      markSpoken,
    ],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSession must be used inside <SessionProvider>');
  return ctx;
}

/** Session state if there is one, otherwise null — never throws.
 *
 *  For shared components that render on both sides of the app. The physician
 *  console lives outside SessionProvider, so anything reaching for session
 *  state there must degrade rather than crash the whole console. */
export function useOptionalSession() {
  return useContext(SessionContext);
}

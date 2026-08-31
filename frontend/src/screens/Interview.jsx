// Owner: Ranjith
// Screen 6. The workhorse — seen 15-20 times in one session. The layout never
// changes, so it stops needing to be read after the second question:
//
//   phase · question · optional tiles · mic · transcript · [Next] · bottom bar
//
// Fully data-driven. Question text and options come from the API response.
// There is no clinical content in this file, and there must never be any.

import { useCallback, useEffect, useRef, useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import MicButton from '../components/MicButton.jsx';
import TranscriptBox from '../components/TranscriptBox.jsx';
import UnderstandingPanel from '../components/UnderstandingPanel.jsx';
import { useT } from '../i18n/useT.js';
import { useSpeech } from '../speech/SpeechProvider.jsx';
import { useSpeechRecognition } from '../speech/useSpeechRecognition.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';
import { recordKnownFields, submitAnswer } from '../api/client.js';

export default function Interview({ onError }) {
  const { tx, voice, lang } = useT();
  const { speak } = useSpeech();
  const {
    sessionId,
    answers,
    currentNode,
    setCurrentNode,
    addAnswer,
    raiseRedFlag,
    go,
    patient,
    consentGiven,
  } = useSession();

  const [node, setNode] = useState(currentNode);
  // Cumulative from the API. Held separately from `node` so it survives the
  // holding screen between questions instead of flickering empty.
  const [understood, setUnderstood] = useState([]);
  const [thinking, setThinking] = useState(!currentNode);
  const [selected, setSelected] = useState(null);

  const { start, stop, reset, transcript, interim, listening, isSupported } =
    useSpeechRecognition(voice);

  // StrictMode double-invokes effects in dev; without this the mocked interview
  // would advance two questions on the first render.
  const bootstrapped = useRef(false);

  const applyResponse = useCallback(
    (res) => {
      if (Array.isArray(res?.extracted) && res.extracted.length) {
        setUnderstood(res.extracted);
      }
      if (res?.red_flag) {
        raiseRedFlag(res.red_flag);
        return;
      }
      if (res?.done) {
        setCurrentNode(null);
        go(SCREENS.DOCUMENTS);
        return;
      }
      setNode(res);
      setCurrentNode(res);
      setSelected(null);
      reset();
      setThinking(false);
    },
    [raiseRedFlag, setCurrentNode, go, reset],
  );

  const ask = useCallback(
    async (payload) => {
      setThinking(true);
      stop();
      // A spinner means nothing to this audience. Say the wait out loud.
      speak(tx('common.oneMoment').audio, voice);
      try {
        const res = await submitAnswer(sessionId, { ...payload, lang });
        applyResponse(res);
      } catch (e) {
        console.error('[interview] submit failed:', e);
        onError?.(e);
      }
    },
    [sessionId, lang, stop, speak, tx, voice, applyResponse, onError],
  );

  // Hand over what the earlier screens already collected, then send the chief
  // complaint to get the first question.
  //
  // The seeding step is not optional. The name, age, sex and consent screens
  // store their answers in SessionContext only; the backend's state machine
  // never saw them, so it treated the identity and consent stages as
  // unanswered and re-asked "What is your name?" to a patient who had just
  // typed it. Seeding costs no model call — the values are already structured.
  useEffect(() => {
    if (bootstrapped.current || currentNode) return;
    bootstrapped.current = true;

    const known = {};
    if (patient?.name) known.patient_name = patient.name;
    if (patient?.age) known.age = patient.age;
    if (patient?.sex) known.sex = patient.sex;
    if (consentGiven != null) known.consent_given = consentGiven ? 'yes' : 'no';

    const previous = answers[answers.length - 1];
    const firstAsk = () =>
      ask({
        node_id: previous?.node_id ?? 'chief_complaint',
        value: previous?.value ?? null,
        text: previous?.text ?? '',
      });

    if (!Object.keys(known).length) {
      firstAsk();
      return;
    }
    // Seed first, ask second. A failed seed must not strand the patient on a
    // blank screen, so the interview proceeds either way — it just costs the
    // identity questions being asked again.
    recordKnownFields(sessionId, known)
      .catch((e) => console.warn('[interview] could not seed known fields:', e))
      .finally(firstAsk);
  }, [answers, currentNode, ask, sessionId, patient, consentGiven]);

  useEffect(() => stop, [stop]);

  const answerText = selected
    ? node?.options?.find((o) => o.value === selected)?.label ?? ''
    : transcript.trim();

  const canAdvance = Boolean(selected || transcript.trim());

  const next = () => {
    if (!node || !canAdvance) return;
    addAnswer({
      node_id: node.node_id,
      question: node.question,
      value: selected,
      text: answerText,
    });
    ask({ node_id: node.node_id, value: selected, text: answerText });
  };

  const chooseOption = (value) => {
    setSelected(value);
    const label = node?.options?.find((o) => o.value === value)?.label;
    if (label) speak(label, voice);
  };

  if (thinking || !node) {
    return (
      <ScreenShell
        prompt={{ label: tx('common.oneMoment').label, audio: '' }}
        repeatAudio={tx('common.oneMoment').audio}
        phase={node?.phase}
      >
        {/* Static text only. No spinner — nothing else in this app moves. */}
        <p className="shell__caption">{tx('common.oneMoment').label}</p>
      </ScreenShell>
    );
  }

  return (
    <ScreenShell
      prompt={{ label: node.question, audio: node.question }}
      phase={node.phase}
      speechKey={node.node_id}
    >
      {node.options?.length ? (
        <div className={node.options.length > 4 ? 'grid-3' : 'grid-2'}>
          {node.options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`tile${selected === opt.value ? ' tile--selected' : ''}`}
              onClick={() => chooseOption(opt.value)}
              aria-pressed={selected === opt.value}
            >
              <span className="tile__label">{opt.label}</span>
            </button>
          ))}
        </div>
      ) : null}

      <MicButton
        listening={listening}
        onStart={start}
        onStop={stop}
        supported={isSupported}
        labelIdle={tx('common.tapToSpeak').label}
        labelListening={tx('common.listening').label}
        labelUnsupported={tx('common.micUnavailable').label}
      />

      <div className="interview__row">
        <TranscriptBox
          final={selected ? answerText : transcript}
          interim={selected ? '' : interim}
          placeholder={tx('common.tapToSpeak').label}
        />
        <UnderstandingPanel extracted={understood} />
      </div>

      <BigButton variant="primary" center onClick={next} disabled={!canAdvance}>
        {tx('common.next').label}
      </BigButton>
    </ScreenShell>
  );
}

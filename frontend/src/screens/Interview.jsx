// Owner: Ranjith
// Screen 6. The workhorse — seen 15-20 times in one session. The layout never
// changes, so it stops needing to be read after the second question:
//
//   phase · question · optional tiles · mic · answer box · [Next] · bottom bar
//
// The answer box takes typing on every question, always. Open-ended questions
// used to render a mic and nothing else, so a patient who cannot speak clearly
// — or who is standing in a noisy OPD where recognition just fails — could not
// answer them at all. When recognition is missing or has errored the mic is
// removed entirely and typing carries the screen.
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
import { useSpeechRecognition } from '../speech/useSpeechRecognition.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';
import { recordKnownFields, submitAnswer } from '../api/client.js';
import BilingualText from '../components/BilingualText.jsx';

// Interview stages that are rendered by their own screen instead of as a
// generic question. Keyed by the node id ai/interview/nodes.py uses.
const OWN_SCREEN = {
  documents: SCREENS.DOCUMENTS,
  confirm: SCREENS.CONFIRM,
};

export default function Interview({ onError }) {
  const { tx, voice, lang } = useT();
  const {
    sessionId,
    answers,
    currentNode,
    setCurrentNode,
    addAnswer,
    noteAnswerFields,
    extracted: understood,
    setExtracted: setUnderstood,
    raiseRedFlag,
    go,
    patient,
    consentGiven,
  } = useSession();

  const [node, setNode] = useState(currentNode);
  const [thinking, setThinking] = useState(!currentNode);
  // The answer waiting to be told which fields it filled, plus the fields
  // already known when it was sent. A ref, not state: it is bookkeeping
  // between a request and its reply, and must not cause a render.
  const pending = useRef(null);
  const [selected, setSelected] = useState(null);
  // What is actually in the answer box. Speech writes into it, the patient
  // can type into it, and either one alone is a complete answer. Held here
  // rather than read straight off the speech hook so an edit survives.
  const [answer, setAnswer] = useState('');

  const { start, stop, reset, transcript, interim, listening, isSupported, error } =
    useSpeechRecognition(voice);

  // No mic at all when recognition is missing or has failed. A dead button
  // next to a box that does work only invites the patient to keep pressing
  // it; typing carries the screen instead.
  const micUsable = isSupported && !error;
  const answerHint = micUsable ? tx('common.tapOrType') : tx('common.typeHere');

  // Speech overwrites the box, but only when new words actually arrive, so
  // a correction typed between utterances is not thrown away.
  const lastHeard = useRef('');

  // StrictMode double-invokes effects in dev; without this the mocked interview
  // would advance two questions on the first render.
  const bootstrapped = useRef(false);

  const applyResponse = useCallback(
    (res) => {
      if (Array.isArray(res?.extracted) && res.extracted.length) {
        setUnderstood(res.extracted);
        // Everything new since the answer went out belongs to that answer —
        // including fields reconcile.py derived rather than asked for.
        const p = pending.current;
        if (p) {
          noteAnswerFields(
            p.key,
            res.extracted.map((f) => f.name).filter((n) => !p.before.has(n)),
          );
          pending.current = null;
        }
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
      // Two of the state machine's stages already have a purpose-built screen.
      // Rendering them here as well asked the patient the same thing twice —
      // "Do you have any old prescriptions or reports with you?" in the
      // interview, then the documents screen asking it again one tap later.
      // The state machine still decides when these stages happen; the kiosk
      // just shows the right screen for them, and that screen answers the node.
      const own = OWN_SCREEN[res?.node_id];
      if (own) {
        setCurrentNode(res);
        go(own);
        return;
      }
      setNode(res);
      setCurrentNode(res);
      setSelected(null);
      setAnswer('');
      lastHeard.current = '';
      reset();
      setThinking(false);
    },
    [raiseRedFlag, setCurrentNode, go, reset, setUnderstood, noteAnswerFields],
  );

  const ask = useCallback(
    async (payload) => {
      setThinking(true);
      stop();
      // The wait is shown, not spoken. Audio is press-only now, and this
      // fired on every single submit.
      try {
        const res = await submitAnswer(sessionId, { ...payload, lang });
        applyResponse(res);
      } catch (e) {
        console.error('[interview] submit failed:', e);
        onError?.(e);
      }
    },
    [sessionId, lang, stop, applyResponse, onError],
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

    // A tapped complaint tile is seeded, not submitted as an answer. The
    // complaint screen is the kiosk's own screen — the backend never rendered
    // that question, so it has no target field recorded for it and a tapped
    // value arriving as an answer is discarded with nowhere to go. That is
    // exactly what happened: a patient who tapped "Back" reached the doctor
    // with no complaint recorded at all.
    //
    // Seeding also runs it through reconciliation, so tapping "Back" fills the
    // site the same way saying "back pain" does.
    if (previous?.node_id === 'chief_complaint' && previous?.value) {
      known.chief_complaint = previous.value;
    }

    // The opening exchange fills the seeded fields — the complaint itself and
    // anything reconcile.py derives from it, such as the body site. They belong
    // to the complaint the patient tapped, not to the first follow-up.
    if (previous) {
      pending.current = {
        key: previous.key || `${previous.node_id}:${previous.question}`,
        before: new Set(),
      };
    }

    const firstAsk = () =>
      ask({
        node_id: previous?.node_id ?? 'chief_complaint',
        value: null,
        // Free speech still goes as a transcript for extraction; a tapped tile
        // has already been seeded above and sends nothing.
        text: previous?.value ? '' : previous?.text ?? '',
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

  useEffect(() => {
    const heard = transcript.trim();
    if (!heard || heard === lastHeard.current) return;
    lastHeard.current = heard;
    setAnswer(heard);
    // Speaking after tapping means the patient changed their mind.
    setSelected(null);
  }, [transcript]);

  const typed = answer.trim();
  // Three independent ways to have answered. Any one of them is enough — that
  // is the whole point: no question may be reachable with no usable input.
  const canAdvance = Boolean(selected || typed);

  const handleType = (text) => {
    setAnswer(text);
    // Typing over a tapped tile replaces it rather than sending both.
    if (selected) setSelected(null);
  };

  const next = () => {
    if (!node || !canAdvance) return;
    const label = node?.options?.find((o) => o.value === selected)?.label ?? '';
    // A tapped tile sends NO text. Its value is already a canonical English
    // token, so app/ files it straight into the target field with no model
    // call; sending the label as a transcript as well sent the tap down the
    // extraction path instead, spending a request and a round trip to
    // re-derive what we already knew.
    const text = selected ? '' : typed;
    const key = `${node.node_id}:${node.question}`;
    addAnswer({
      key,
      node_id: node.node_id,
      question: node.question,
      // Confirm renders both lines; without this the readback is the one place
      // in the app where a question loses its English.
      question_en: node.question_en,
      value: selected,
      text: selected ? label : typed,
      text_en: selected ? node.options?.find((o) => o.value === selected)?.label_en : null,
    });
    // Which fields this answer fills is only known once the backend answers.
    pending.current = { key, before: new Set(understood.map((f) => f.name)) };
    ask({ node_id: node.node_id, value: selected, text });
  };

  const chooseOption = (value) => {
    setSelected(value);
    const label = node?.options?.find((o) => o.value === value)?.label;
    if (label) {
      setAnswer(label);
    }
  };

  if (thinking || !node) {
    // No audio on this screen at all. Not even behind the Listen button: with
    // nothing to speak, ScreenShell renders no speaker control here, so there
    // is no way to make the kiosk announce a wait. The wait is shown — the
    // caption below and the phase label above.
    return (
      <ScreenShell
        prompt={{ label: tx('common.oneMoment').label, audio: '' }}
        repeatAudio=""
        phase={node?.phase}
      >
        {/* Static text only. No spinner — nothing else in this app moves. */}
        <BilingualText as="p" className="shell__caption">{tx('common.oneMoment').label}</BilingualText>
      </ScreenShell>
    );
  }

  return (
    <ScreenShell
      prompt={{ label: node.question, audio: node.question }}
      repeatAudio={`${node.question} ${answerHint.audio}`}
      phase={node.phase}
      listening={listening}
      promptEnglish={node.question_en}
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
              <BilingualText className="tile__label" english={opt.label_en}>
                {opt.label}
              </BilingualText>
            </button>
          ))}
        </div>
      ) : null}

      {micUsable ? (
        <MicButton
          listening={listening}
          onStart={start}
          onStop={stop}
          supported
          labelIdle={tx('common.tapToSpeak').label}
          labelListening={tx('common.listening').label}
          labelUnsupported={tx('common.micUnavailable').label}
        />
      ) : null}

      <div className="interview__row">
        <TranscriptBox
          value={answer}
          interim={selected ? '' : interim}
          onChange={handleType}
          placeholder={answerHint.label}
          ariaLabel={node.question}
        />
        <UnderstandingPanel extracted={understood} />
      </div>

      <BigButton variant="primary" center onClick={next} disabled={!canAdvance}>
        {tx('common.next').label}
      </BigButton>
    </ScreenShell>
  );
}

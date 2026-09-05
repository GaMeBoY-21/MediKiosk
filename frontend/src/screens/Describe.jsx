// Owner: Ranjith
// The opening description. The one screen where the kiosk asks nothing
// specific and lets the patient say what is wrong in their own words.
//
// Everything after this is a follow-up. The interview used to walk a fixed
// scaffold regardless of what the patient had already volunteered, so someone
// who said "chest pain for two days, it goes to my left arm, worse when I
// walk" was still asked where it hurts, when it started, whether it spreads
// and what makes it worse — four questions they had just answered. This
// screen sends that sentence through extraction once, across every clinical
// stage, and the state machine then asks only for what is genuinely still
// empty.
//
// Three ways to answer, as everywhere else: speak, type, or tap a body area
// for a patient who will not or cannot talk. Tapping is not a lesser path —
// it seeds the complaint exactly as the old first question did.
//
// No time limit and no character limit. A patient mid-sentence must never be
// cut off by a control.

import { useEffect, useRef, useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import IconTile from '../components/IconTile.jsx';
import MicButton from '../components/MicButton.jsx';
import TranscriptBox from '../components/TranscriptBox.jsx';
import { ICONS } from '../components/Icons.jsx';
import { useT } from '../i18n/useT.js';
import { useSpeechRecognition } from '../speech/useSpeechRecognition.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';

const AREAS = ['head', 'chest', 'stomach', 'back', 'joints', 'skin', 'fever', 'breathing', 'other'];

export default function Describe() {
  const { tx, voice } = useT();
  const { addAnswer, go } = useSession();
  const { start, stop, transcript, interim, listening, isSupported, error } =
    useSpeechRecognition(voice);

  const [answer, setAnswer] = useState('');
  const lastHeard = useRef('');

  const micUsable = isSupported && !error;
  const answerHint = micUsable ? tx('common.tapOrType') : tx('common.typeHere');

  useEffect(() => stop, [stop]);

  useEffect(() => {
    const heard = transcript.trim();
    if (!heard || heard === lastHeard.current) return;
    lastHeard.current = heard;
    setAnswer(heard);
  }, [transcript]);

  // The narration is recorded as an answer so it appears in the readback the
  // patient checks at the end. `narration: true` is what tells the interview
  // screen to send it down the multi-stage extraction path rather than
  // treating it as an answer to a question nobody asked.
  const commit = (value, text) => {
    stop();
    addAnswer({
      key: 'describe:narration',
      node_id: 'chief_complaint',
      screen: SCREENS.DESCRIBE,
      question: tx('complaint.describeTitle').label,
      value,
      text,
      narration: !value,
      fields: value ? ['chief_complaint'] : [],
    });
    go(SCREENS.INTERVIEW);
  };

  const typed = answer.trim();

  return (
    <ScreenShell
      prompt={tx('complaint.describeTitle')}
      repeatAudio={`${tx('complaint.describeTitle').audio} ${answerHint.audio}`}
      listening={listening}
    >
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

      <TranscriptBox
        value={answer}
        interim={interim}
        onChange={setAnswer}
        placeholder={answerHint.label}
        ariaLabel={tx('complaint.describeTitle').label}
      />

      {typed ? (
        <BigButton variant="primary" center onClick={() => commit(null, typed)}>
          {tx('common.doneSpeaking').label}
        </BigButton>
      ) : null}

      {/* The tap path, for a patient who will not speak. Kept below the box so
          the invitation to talk comes first — this screen exists to get them
          talking — but present and complete either way. */}
      <p className="describe__or">{tx('complaint.describeTiles').label}</p>
      <div className="grid-3">
        {AREAS.map((area) => (
          <IconTile
            key={area}
            icon={ICONS[area]}
            label={tx(`complaint.${area}`).label}
            onSelect={() => commit(area, tx(`complaint.${area}`).label)}
          />
        ))}
      </div>
    </ScreenShell>
  );
}

// Owner: Ranjith
// Screen 5. The first real question, so it carries every answer path at once:
// tap a body area, speak freely, or type. Any one of them is a complete answer.
//
// Four controls: the tile grid (one control), the mic, the answer box and
// "Done speaking". The box counts against the three-control budget now that it
// takes input rather than only displaying it — accepted deliberately, because
// a question with no path for a patient who cannot speak is not answerable at
// all, and that is the worse failure.

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

export default function ChiefComplaint() {
  const { tx, voice } = useT();
  const { addAnswer, go } = useSession();
  const { start, stop, transcript, interim, listening, isSupported, error } =
    useSpeechRecognition(voice);

  // The answer box is typeable here too. This is the first real question,
  // and a patient who cannot speak clearly must not be stuck on it with
  // only nine tiles and a mic that does not hear them.
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

  const commit = (value, text) => {
    stop();
    addAnswer({ node_id: 'chief_complaint', question: tx('complaint.title').label, value, text });
    go(SCREENS.INTERVIEW);
  };

  const typed = answer.trim();

  return (
    <ScreenShell
      prompt={tx('complaint.title')}
      repeatAudio={`${tx('complaint.title').audio} ${answerHint.audio}`}
      listening={listening}
    >
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
        ariaLabel={tx('complaint.title').label}
      />

      {typed ? (
        <BigButton variant="primary" center onClick={() => commit(null, typed)}>
          {tx('common.doneSpeaking').label}
        </BigButton>
      ) : null}
    </ScreenShell>
  );
}

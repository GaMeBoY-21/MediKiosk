// Owner: Ranjith
// Screen 5. The first real question, so it carries both answer paths at once:
// tap a body area, or speak freely. Either one is a complete answer.
//
// Three controls: the tile grid, the mic, and "Done speaking".

import { useEffect } from 'react';
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
  const { start, stop, transcript, interim, listening, isSupported } = useSpeechRecognition(voice);

  useEffect(() => stop, [stop]);

  const commit = (value, text) => {
    stop();
    addAnswer({ node_id: 'chief_complaint', question: tx('complaint.title').label, value, text });
    go(SCREENS.INTERVIEW);
  };

  const hasSpeech = Boolean(transcript.trim());

  return (
    <ScreenShell prompt={tx('complaint.title')}>
      <div className="grid-3">
        {AREAS.map((area) => (
          <IconTile
            key={area}
            icon={ICONS[area]}
            label={tx(`complaint.${area}`).label}
            audio={tx(`complaint.${area}`).audio}
            voice={voice}
            onSelect={() => commit(area, tx(`complaint.${area}`).label)}
          />
        ))}
      </div>

      <MicButton
        listening={listening}
        onStart={start}
        onStop={stop}
        supported={isSupported}
        labelIdle={tx('common.tapToSpeak').label}
        labelListening={tx('common.listening').label}
        labelUnsupported={tx('common.micUnavailable').label}
      />

      <TranscriptBox
        final={transcript}
        interim={interim}
        placeholder={tx('common.tapToSpeak').label}
      />

      {hasSpeech ? (
        <BigButton variant="primary" center onClick={() => commit(null, transcript.trim())}>
          {tx('common.doneSpeaking').label}
        </BigButton>
      ) : null}
    </ScreenShell>
  );
}

// Owner: Ranjith
// New patient, part 1 of 3: name. By voice or by touch.
//
// The A-Z keypad exists because speech recognition for Indian names is poor
// even when the API works at all. Touch must be a complete path, not a fallback.

import { useEffect, useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import MicButton from '../components/MicButton.jsx';
import Keypad from '../components/Keypad.jsx';
import { useT } from '../i18n/useT.js';
import { useSpeechRecognition } from '../speech/useSpeechRecognition.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';

export default function NameEntry() {
  const { tx, voice } = useT();
  const { setPatient, addAnswer, go } = useSession();
  const [typed, setTyped] = useState('');
  const { start, stop, transcript, listening, isSupported, error } =
    useSpeechRecognition(voice);

  // Same rule as every other question: when recognition is missing or has
  // failed the mic goes away rather than sitting there disabled. The A-Z
  // keypad below is a complete path on its own, and on a 800px-high panel
  // the dead button was also what pushed the keypad's last row off screen.
  const micUsable = isSupported && !error;

  useEffect(() => stop, [stop]);

  // Whatever the patient typed wins; otherwise use what we heard.
  const name = typed || transcript.trim();

  // First keypress after speaking continues from the heard text rather than
  // throwing it away — correcting one wrong letter is the common case.
  const handleKey = (k) => {
    setTyped((v) => (v === '' && transcript.trim() ? transcript.trim() + k : v + k));
  };

  const submit = () => {
    stop();
    setPatient({ name });
    addAnswer({
      key: 'identity:patient_name',
      node_id: 'identity',
      screen: SCREENS.NAME,
      question: tx('identify.nameTitle').label,
      text: name,
      fields: ['patient_name'],
    });
    go(SCREENS.AGE);
  };

  return (
    <ScreenShell prompt={tx('identify.nameTitle')}>
      <div
        className={`keypad__display keypad__display--text${
          name ? '' : ' keypad__display--empty'
        }`}
      >
        {name || tx(micUsable ? 'common.tapToSpeak' : 'common.typeHere').label}
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

      <Keypad
        mode="alpha"
        onKey={handleKey}
        onDelete={() => setTyped((v) => (v || transcript.trim()).slice(0, -1))}
        deleteLabel="Delete"
      />

      <BigButton variant="primary" center onClick={submit} disabled={!name}>
        {tx('common.next').label}
      </BigButton>
    </ScreenShell>
  );
}

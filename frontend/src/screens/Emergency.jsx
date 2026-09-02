// Owner: Ranjith
// Screen 10. Interstitial shown when the API returns a red flag.
//
// The patient cannot dismiss this — that is the point. It clears only on a
// deliberate 3-second staff press-and-hold, which a confused or distressed
// patient will not produce by accident.
//
// --alert is reserved for exactly this screen.

import { useEffect, useRef, useState } from 'react';
import BilingualText from '../components/BilingualText.jsx';
import { Warning } from '../components/Icons.jsx';
import { useT } from '../i18n/useT.js';
import { DEFAULT_LANG, bcp47, t } from '../i18n/strings.js';
import { useSpeech } from '../speech/SpeechProvider.jsx';
import { useSession, SCREENS } from '../state/SessionContext.jsx';

const HOLD_MS = 3000;
const TICK_MS = 50;


export default function Emergency() {
  const { tx, voice } = useT();
  const { speak } = useSpeech();
  const { redFlag, clearRedFlag, go } = useSession();
  const [held, setHeld] = useState(0);
  const timer = useRef(null);

  const patient = tx('emergency.patient');
  // The ONLY place in the app that will speak a language the patient did not
  // choose. Marathi has no installed voice on the demo machine, and the rule
  // everywhere else — no voice means silence — turned the alert into a screen
  // that lights up red and says nothing. A patient in distress who cannot read
  // is exactly who this screen is for. So: their language if it can be spoken,
  // English if it cannot, never nothing.
  const englishAlert = t(DEFAULT_LANG, 'emergency.patient');

  useEffect(() => {
    speak(patient.audio, voice, {
      text: englishAlert.audio || englishAlert.label,
      lang: bcp47(DEFAULT_LANG),
    });
    return () => clearInterval(timer.current);
  }, [patient.audio, voice, speak, englishAlert.audio, englishAlert.label]);

  const startHold = () => {
    clearInterval(timer.current);
    const began = Date.now();
    timer.current = setInterval(() => {
      const progress = Math.min(1, (Date.now() - began) / HOLD_MS);
      setHeld(progress);
      if (progress >= 1) {
        clearInterval(timer.current);
        clearRedFlag();
        go(SCREENS.DOCUMENTS);
      }
    }, TICK_MS);
  };

  const cancelHold = () => {
    clearInterval(timer.current);
    setHeld(0);
  };

  return (
    <div className="emergency" role="alertdialog" aria-modal="true">
      <div className="emergency__inner">
        <Warning size={96} />

        <BilingualText as="h1" className="emergency__headline" always>
          {patient.label}
        </BilingualText>

        {/* Staff-facing, always English — the person reading this is clinical.
            The API field is `label` (see app/schemas.py RedFlag); this used to
            read `reason`, which does not exist, so staff never saw why the
            alarm fired. */}
        <p className="emergency__staff">
          {tx('emergency.staff').label}
          {redFlag?.label ? ` (${redFlag.label})` : ''}
        </p>

        <button
          type="button"
          className="emergency__hold"
          onPointerDown={startHold}
          onPointerUp={cancelHold}
          onPointerLeave={cancelHold}
          onPointerCancel={cancelHold}
        >
          <span
            className="emergency__hold-fill"
            style={{ width: `${held * 100}%` }}
            aria-hidden="true"
          />
          <span>{tx('emergency.hold').label}</span>
        </button>
      </div>
    </div>
  );
}

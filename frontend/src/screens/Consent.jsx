// Owner: Ranjith
// Screen 4. Legally the most important screen, and it must work for someone
// who cannot read a word of it.
//
// The explanation auto-plays the moment the screen loads (~20s). The same text
// is on screen at 24px as the backup. Each toggle speaks itself when tapped.
// "I do not agree" is the same size and weight as "I agree" — refusing is
// never made harder than accepting.

import { useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import SpeakerButton from '../components/SpeakerButton.jsx';
import Toggle from '../components/Toggle.jsx';
import { useT } from '../i18n/useT.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';
import { recordConsent } from '../api/client.js';

export default function Consent() {
  const { tx, voice } = useT();
  const { sessionId, consentOptions, setConsent, go } = useSession();
  const [opts, setOpts] = useState(consentOptions);

  const explanation = tx('consent.explanation');

  const set = (key) => (value) => setOpts((o) => ({ ...o, [key]: value }));

  const agree = () => {
    setConsent(true, opts);
    // Fire and forget: the patient should never wait on the network here.
    recordConsent(sessionId, opts).catch((e) => console.warn('[consent] not saved:', e));
    go(SCREENS.COMPLAINT);
  };

  const decline = () => {
    setConsent(false, opts);
    go(SCREENS.CONSENT_DECLINED);
  };

  return (
    <ScreenShell
      prompt={{ label: tx('consent.title').label, audio: explanation.audio }}
      repeatAudio={explanation.audio}
    >
      <p className="consent__text">{explanation.label}</p>

      <SpeakerButton
        text={explanation.audio}
        voice={voice}
        label={tx('consent.playAgain').label}
      />

      <div className="stack">
        <Toggle
          checked={opts.history}
          onChange={set('history')}
          label={tx('consent.optHistory').label}
          audio={tx('consent.optHistory').audio}
          voice={voice}
        />
        <Toggle
          checked={opts.documents}
          onChange={set('documents')}
          label={tx('consent.optDocuments').label}
          audio={tx('consent.optDocuments').audio}
          voice={voice}
        />
        <Toggle
          checked={opts.abha}
          onChange={set('abha')}
          label={tx('consent.optAbha').label}
          audio={tx('consent.optAbha').audio}
          voice={voice}
        />
      </div>

      <div className="consent__actions">
        <BigButton variant="primary" center onClick={agree}>
          {tx('consent.agree').label}
        </BigButton>
        <BigButton variant="outline" center onClick={decline}>
          {tx('consent.decline').label}
        </BigButton>
      </div>
    </ScreenShell>
  );
}

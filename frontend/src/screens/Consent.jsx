// Owner: Ranjith
// Screen 4. Legally the most important screen, and it must work for someone
// who cannot read a word of it.
//
// The explanation is on screen at 24px, and the Listen button on the question
// speaks it on demand — nothing here plays on its own. Each toggle speaks
// itself when tapped. "I do not agree" is the same size and weight as
// "I agree" — refusing is never made harder than accepting.

import { useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import Toggle from '../components/Toggle.jsx';
import { useT } from '../i18n/useT.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';
import { recordConsent } from '../api/client.js';
import BilingualText from '../components/BilingualText.jsx';

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
      <BilingualText as="p" className="consent__text">{explanation.label}</BilingualText>

      <div className="stack">
        <Toggle
          checked={opts.history}
          onChange={set('history')}
          label={tx('consent.optHistory').label}
        />
        <Toggle
          checked={opts.documents}
          onChange={set('documents')}
          label={tx('consent.optDocuments').label}
        />
        <Toggle
          checked={opts.abha}
          onChange={set('abha')}
          label={tx('consent.optAbha').label}
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

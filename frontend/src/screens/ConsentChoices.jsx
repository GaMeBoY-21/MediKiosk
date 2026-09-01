// Owner: Ranjith
// Screen 4b of the two consent screens: the three permissions, then the
// decision.
//
// Split from the explanation (Consent) so both halves fit 1280x800 without
// scrolling. Everything together came to 1110px, which put these toggles and
// both buttons below the fold — a patient who does not know to scroll would
// never have seen what they were agreeing to, or the option to refuse.
//
// Each toggle speaks itself when tapped. "I do not agree" is the same size,
// weight and prominence as "I agree": refusing is never made harder than
// accepting.

import { useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import Toggle from '../components/Toggle.jsx';
import { useT } from '../i18n/useT.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';
import { recordConsent } from '../api/client.js';

export default function ConsentChoices() {
  const { tx, voice } = useT();
  const { sessionId, consentOptions, setConsent, go } = useSession();
  const [opts, setOpts] = useState(consentOptions);

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
      prompt={{ label: tx('consent.choicesTitle').label, audio: tx('consent.choicesTitle').audio }}
    >
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

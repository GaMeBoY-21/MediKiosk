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

// Two steps, not one screen.
//
// The explanation and four bilingual toggles do not fit together at 1280x800:
// in Tamil the agree/decline buttons ended up 46px BEHIND the bottom bar,
// which on the one screen that legally must be reachable is not a cosmetic
// problem. Splitting is the right answer rather than shrinking the type —
// this text is what the patient is agreeing to and it is already at the
// app's body size.
//
// Step 1 explains. Step 2 is the choices. Both are readable on their own, and
// the patient can go back.
export default function Consent() {
  const { tx, voice } = useT();
  const { sessionId, consentOptions, setConsent, addAnswer, go } = useSession();
  const [opts, setOpts] = useState(consentOptions);
  const [step, setStep] = useState(0);

  const explanation = tx('consent.explanation');

  // What Listen reads out: the explanation, then each toggle in order.
  //
  // Tapping a toggle is silent — audio plays only on an explicit press, and
  // per-tap noise was intolerable in a shared hall. But that left a patient
  // who cannot read agreeing to four things they had never heard, which is
  // not informed consent in any sense DPDP would recognise. One press, one
  // utterance, numbered so they can be told apart.
  const OPTIONS = ['optHistory', 'optDocuments', 'optAbha', 'optGovernment'];
  const spokenConsent = [
    explanation.audio,
    ...OPTIONS.map((key, i) => `${i + 1}. ${tx(`consent.${key}`).audio || tx(`consent.${key}`).label}`),
  ].join(' ');

  const set = (key) => (value) => setOpts((o) => ({ ...o, [key]: value }));

  const agree = () => {
    setConsent(true, opts);
    addAnswer({
      key: 'identity:consent_given',
      node_id: 'consent',
      screen: SCREENS.CONSENT,
      question: tx('consent.title').label,
      text: tx('common.yes').label,
      fields: ['consent_given'],
    });
    // Fire and forget: the patient should never wait on the network here.
    recordConsent(sessionId, opts).catch((e) => console.warn('[consent] not saved:', e));
    go(SCREENS.DESCRIBE);
  };

  const decline = () => {
    setConsent(false, opts);
    go(SCREENS.CONSENT_DECLINED);
  };

  return (
    <ScreenShell
      prompt={{ label: tx('consent.title').label, audio: spokenConsent }}
      repeatAudio={spokenConsent}
    >
      {step === 0 ? (
        <BilingualText as="p" className="consent__text">{explanation.label}</BilingualText>
      ) : null}

      {step === 1 ? (
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
        {/* Independent of the other three. Refusing it withholds only the
            outward sharing — the interview, the summary and seeing the doctor
            all proceed exactly the same way. */}
        <Toggle
          checked={opts.government}
          onChange={set('government')}
          label={tx('consent.optGovernment').label}
        />
      </div>

      ) : null}

      {step === 0 ? (
        <BigButton variant="primary" center onClick={() => setStep(1)}>
          {tx('common.next').label}
        </BigButton>
      ) : null}

      {step === 1 ? (
      <div className="consent__actions">
        <BigButton variant="primary" center onClick={agree}>
          {tx('consent.agree').label}
        </BigButton>
        <BigButton variant="outline" center onClick={decline}>
          {tx('consent.decline').label}
        </BigButton>
      </div>
      ) : null}
    </ScreenShell>
  );
}

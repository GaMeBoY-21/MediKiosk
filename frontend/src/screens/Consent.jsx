// Owner: Ranjith
// Screen 4a of the two consent screens. Legally the most important screen in
// the app, and it must work for someone who cannot read a word of it.
//
// Split from the choices (Consent2) because everything on one screen came to
// 1110px in an 800px viewport once the English line was added. It scrolled,
// and a first-time elderly patient does not know to scroll — which means the
// toggles and the two buttons were simply below the fold, unseen. An unread
// consent is a DPDP problem, not a layout nit.
//
// Splitting rather than shrinking: nothing on a patient screen goes below
// 24px, so there was no type size left to give back.
//
// The explanation auto-plays once the moment this screen loads (~20s). The
// same text is on screen at 24px as the backup.

import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import SpeakerButton from '../components/SpeakerButton.jsx';
import { useT } from '../i18n/useT.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';
import BilingualText from '../components/BilingualText.jsx';

export default function Consent() {
  const { tx, voice } = useT();
  const { go } = useSession();

  const explanation = tx('consent.explanation');

  return (
    <ScreenShell
      prompt={{ label: tx('consent.title').label, audio: explanation.audio }}
      repeatAudio={explanation.audio}
    >
      <BilingualText as="p" className="consent__text">{explanation.label}</BilingualText>

      <SpeakerButton
        text={explanation.audio}
        voice={voice}
        label={tx('consent.playAgain').label}
      />

      <BigButton variant="primary" center onClick={() => go(SCREENS.CONSENT_CHOICES)}>
        {tx('common.next').label}
      </BigButton>
    </ScreenShell>
  );
}

// Owner: Ranjith
// Screen 1. Attract mode. The whole screen is the button.
//
// The call to action cycles through all seven languages every 3 seconds so a
// passer-by sees their own script without touching anything. No bottom bar and
// no progress dots here — the journey has not started.

import { useEffect, useState } from 'react';
import { HandTouch } from '../components/Icons.jsx';
import { LANGUAGES, t } from '../i18n/strings.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';

const CYCLE_MS = 3000;
const HOSPITAL = 'District Government Hospital';

export default function Idle() {
  const { go, setLanguage } = useSession();
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setIndex((i) => (i + 1) % LANGUAGES.length);
    }, CYCLE_MS);
    return () => clearInterval(id);
  }, []);

  const lang = LANGUAGES[index];
  const cta = t(lang.code, 'idle.begin').label;

  const begin = () => {
    // Start in whichever script was showing. The Language screen is next
    // regardless, so this only decides what they read on the way there.
    setLanguage(lang.code);
    go(SCREENS.LANGUAGE);
  };

  return (
    <button type="button" className="idle fade-in" onClick={begin}>
      <header className="idle__header">
        <div className="idle__ministry">{t('en', 'idle.subtitle').label}</div>
        <div className="idle__hospital">{HOSPITAL}</div>
      </header>

      <div className="idle__body">
        <span className="idle__icon idle__icon--beckon">
          <HandTouch size={140} />
        </span>
        {/* Centred here on purpose: this is a call to action, not body text. */}
        <span className="idle__cta" lang={lang.code}>
          {cta}
        </span>
        <span className="idle__cycle">{LANGUAGES.map((l) => l.native).join(' · ')}</span>
      </div>
    </button>
  );
}

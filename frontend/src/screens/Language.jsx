// Owner: Ranjith
// Screen 2. Seven tiles, each showing the language name in its own script and
// nothing else. No flags (a script is not a country), no English subtitle
// (English is what we are trying to get away from).
//
// Tapping is silent: it sets the language and advances.
// Everything after this screen is in the chosen language.

import { useEffect, useRef, useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import { DEFAULT_LANG, LANGUAGES, bcp47, t } from '../i18n/strings.js';
import { useSpeech } from '../speech/SpeechProvider.jsx';
import { useSession, SCREENS } from '../state/SessionContext.jsx';

const ADVANCE_MS = 1000;

export default function Language() {
  const { setLanguage, go } = useSession();
  const { speak } = useSpeech();
  const [picked, setPicked] = useState(null);
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  // The only screen in the app that speaks on its own, and only once.
  // A patient who cannot read has no way to discover the Listen button unless
  // something speaks first; from here on every sound is a button press.
  const { hasSpoken, markSpoken } = useSession();
  const greeting = t(DEFAULT_LANG, 'language.title');
  useEffect(() => {
    if (hasSpoken('screen:language')) return;
    markSpoken('screen:language');
    speak(greeting.audio || greeting.label, bcp47(DEFAULT_LANG));
  }, [hasSpoken, markSpoken, speak, greeting]);

  const choose = (code) => {
    if (picked) return; // ignore double taps while the screen advances
    setPicked(code);
    setLanguage(code);
    timer.current = setTimeout(() => go(SCREENS.IDENTIFY), ADVANCE_MS);
  };

  return (
    // English, always. Reading the session language here meant that coming
    // BACK to this screen rendered it in whatever had been chosen — the one
    // screen that cannot be translated, because it is where the choice is made.
    <ScreenShell prompt={t(DEFAULT_LANG, 'language.title')} englishOnly>
      <div className="language__grid">
        {LANGUAGES.map((l) => (
          <button
            key={l.code}
            type="button"
            lang={l.code}
            className={`tile tile--language${picked === l.code ? ' tile--selected' : ''}`}
            onClick={() => choose(l.code)}
          >
            {l.native}
          </button>
        ))}
      </div>
    </ScreenShell>
  );
}

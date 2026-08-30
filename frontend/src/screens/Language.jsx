// Owner: Ranjith
// Screen 2. Seven tiles, each showing the language name in its own script and
// nothing else. No flags (a script is not a country), no English subtitle
// (English is what we are trying to get away from).
//
// Tapping speaks a greeting in that language as confirmation, then advances.
// Everything after this screen is in the chosen language.

import { useEffect, useRef, useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import { LANGUAGES, bcp47, t } from '../i18n/strings.js';
import { useSpeech } from '../speech/SpeechProvider.jsx';
import { useSession, SCREENS } from '../state/SessionContext.jsx';

const ADVANCE_MS = 1000;

export default function Language() {
  const { language, setLanguage, go } = useSession();
  const { speak } = useSpeech();
  const [picked, setPicked] = useState(null);
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  const choose = (code) => {
    if (picked) return; // ignore double taps while the greeting plays
    setPicked(code);
    setLanguage(code);
    speak(t(code, 'language.greeting').audio, bcp47(code));
    timer.current = setTimeout(() => go(SCREENS.IDENTIFY), ADVANCE_MS);
  };

  return (
    <ScreenShell prompt={t(language, 'language.title')}>
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

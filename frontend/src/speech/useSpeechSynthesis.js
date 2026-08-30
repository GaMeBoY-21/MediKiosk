// Owner: Ranjith
// Text-to-speech. Every screen speaks its instruction on mount, so this hook
// must never be the reason a screen fails to appear.
//
// Two hazards it handles:
//   1. getVoices() is empty on the first call in Chrome — voices arrive later
//      on the 'voiceschanged' event. We wait for it, with a timeout fallback.
//   2. Many devices have no voice for kn/ta/te/mr/bn. We log and speak with the
//      default voice rather than blocking. Text on screen is the backup.

import { useCallback, useEffect, useRef, useState } from 'react';

const RATE = 0.9; // slightly slow — the audience is 65 and anxious

export function useSpeechSynthesis() {
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;
  const [speaking, setSpeaking] = useState(false);
  const voicesRef = useRef([]);

  useEffect(() => {
    if (!supported) {
      console.info('[speech] speechSynthesis unsupported; running silent');
      return;
    }
    const load = () => {
      const v = window.speechSynthesis.getVoices();
      if (v.length) voicesRef.current = v;
    };
    load();
    window.speechSynthesis.addEventListener('voiceschanged', load);
    return () => window.speechSynthesis.removeEventListener('voiceschanged', load);
  }, [supported]);

  const pickVoice = useCallback((lang) => {
    const voices = voicesRef.current;
    if (!voices.length) return null;
    const base = lang.split('-')[0];
    return (
      voices.find((v) => v.lang?.toLowerCase() === lang.toLowerCase()) ||
      voices.find((v) => v.lang?.toLowerCase().startsWith(base)) ||
      null
    );
  }, []);

  const cancel = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setSpeaking(false);
  }, [supported]);

  const speak = useCallback(
    (text, lang = 'en-IN') => {
      if (!supported || !text) return;

      const utter = () => {
        const u = new SpeechSynthesisUtterance(text);
        u.lang = lang;
        u.rate = RATE;
        const voice = pickVoice(lang);
        if (voice) u.voice = voice;
        else console.info(`[speech] no voice installed for ${lang}; using device default`);

        u.onstart = () => setSpeaking(true);
        u.onend = () => setSpeaking(false);
        u.onerror = (e) => {
          // 'interrupted' is normal — we cancel on every screen change.
          if (e.error !== 'interrupted' && e.error !== 'canceled') {
            console.warn('[speech] utterance failed:', e.error);
          }
          setSpeaking(false);
        };
        window.speechSynthesis.speak(u);
      };

      window.speechSynthesis.cancel();

      if (voicesRef.current.length || window.speechSynthesis.getVoices().length) {
        // Chrome drops an utterance queued in the same tick as cancel().
        setTimeout(utter, 60);
        return;
      }

      // First call of the session: voices have not loaded yet.
      let fired = false;
      const run = () => {
        if (fired) return;
        fired = true;
        voicesRef.current = window.speechSynthesis.getVoices();
        utter();
      };
      window.speechSynthesis.addEventListener('voiceschanged', run, { once: true });
      setTimeout(run, 300); // fallback: speak with whatever exists
    },
    [supported, pickVoice],
  );

  useEffect(() => cancel, [cancel]);

  return { speak, cancel, speaking, isSupported: supported };
}

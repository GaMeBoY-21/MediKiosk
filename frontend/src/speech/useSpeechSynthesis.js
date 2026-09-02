// Owner: Ranjith
// Text-to-speech. The ONLY place in the app that touches the Web Speech API —
// ai/test_audio_sources.py fails the build if a component reaches around it.
// Sound plays on a press of the speaker button and nowhere else, with two
// exceptions kept deliberately: the language screen, which is shown before a
// language exists, and the emergency alert.
//
// Two hazards it handles:
//   1. getVoices() is empty on the first call in Chrome — voices arrive later
//      on the 'voiceschanged' event. We wait for it, with a timeout fallback.
//   2. Many devices have no voice for kn/ta/te/mr/bn. We then say NOTHING and
//      log it. This used to fall back to the device default, which meant an
//      English voice reading out Marathi text — sounds that are not the
//      language, to a patient who cannot read the screen either. Silence is
//      the better failure: the text is still there, and staff can see the
//      patient is stuck. Marathi has no voice on the demo machine, so this
//      path is real, not theoretical.
//
//      ONE caller opts out: the emergency alert passes a `fallback`, because
//      an alert nobody hears is worse than an alert in the wrong language.
//      Nothing else may. The decision is made HERE rather than by the caller
//      because the voice list loads asynchronously — a component checking
//      "is there a Telugu voice?" on mount can be told no simply because the
//      list has not arrived yet, and would then wrongly speak English.

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
    /**
     * @param {string} text     what to say, in the patient's language
     * @param {string} lang     BCP-47 tag for that language
     * @param {{text: string, lang: string}} [fallback]
     *   Say THIS instead if the device has no voice for `lang`. Reserved for
     *   the emergency alert. Everywhere else the absence of a voice must mean
     *   silence, not a substitution the patient cannot understand.
     */
    (text, lang = 'en-IN', fallback = null) => {
      if (!supported || !text) return;

      const utter = () => {
        // Resolved here, not by the caller: by this point the voice list has
        // finished loading, so "no voice" means no voice rather than "not yet".
        let voice = pickVoice(lang);
        let sayText = text;
        let sayLang = lang;

        if (!voice && fallback?.text) {
          const alt = pickVoice(fallback.lang);
          if (alt) {
            console.warn(
              `[speech] no voice installed for ${lang}; speaking this one in ` +
                `${fallback.lang} instead because it is an alert — being heard ` +
                `matters more here than being understood`,
            );
            voice = alt;
            sayText = fallback.text;
            sayLang = fallback.lang;
          }
        }

        if (!voice) {
          console.warn(
            `[speech] no voice installed for ${lang}; staying silent rather ` +
              `than speaking ${lang} text with another language's voice`,
          );
          setSpeaking(false);
          return;
        }

        const u = new SpeechSynthesisUtterance(sayText);
        u.lang = sayLang;
        u.rate = RATE;
        u.voice = voice;

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
      // Explicit: a refused utterance never fires onend, so without this the
      // button would stay stuck showing "Stop" for a language it cannot speak.
      setSpeaking(false);

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

// Owner: Ranjith
// Screen-local string lookup bound to the session's chosen language.

import { useCallback } from 'react';
import { DEFAULT_LANG, bcp47, englishFor, t } from './strings.js';
import { useSession } from '../state/SessionContext.jsx';

export function useT() {
  const { language, languageChosen } = useSession();

  // Until the patient picks a language there is nothing to honour, so fall
  // back to English deliberately rather than rendering whatever happens to be
  // sitting in session state.
  const lang = languageChosen ? language : DEFAULT_LANG;

  // tx('consent.agree') -> { label, audio }
  const tx = useCallback((path) => t(lang, path), [lang]);

  // Convenience: just the on-screen text.
  const label = useCallback((path) => t(lang, path).label, [lang]);

  // The English counterpart of an already-rendered label, or undefined.
  const english = useCallback((text) => englishFor(text, lang), [lang]);

  return {
    tx,
    label,
    english,
    lang,
    chosen: languageChosen,
    // Audio is single-language on purpose: speaking both would double the
    // length of every question.
    voice: bcp47(lang),
  };
}

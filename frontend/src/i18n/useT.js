// Owner: Ranjith
// Screen-local string lookup bound to the session's chosen language.

import { useCallback } from 'react';
import { bcp47, t } from './strings.js';
import { useSession } from '../state/SessionContext.jsx';

export function useT() {
  const { language } = useSession();

  // tx('consent.agree') -> { label, audio }
  const tx = useCallback((path) => t(language, path), [language]);

  // Convenience: just the on-screen text.
  const label = useCallback((path) => t(language, path).label, [language]);

  return { tx, label, lang: language, voice: bcp47(language) };
}

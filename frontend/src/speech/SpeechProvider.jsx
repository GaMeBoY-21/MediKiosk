// Owner: Ranjith
// One shared speech-synthesis instance for the whole app.
//
// window.speechSynthesis is a single global queue. If several components each
// held their own useSpeechSynthesis(), one screen's cancel() would silently
// stop another's utterance while leaving its `speaking` flag stuck true.

import { createContext, useContext } from 'react';
import { useSpeechSynthesis } from './useSpeechSynthesis.js';

const SpeechContext = createContext(null);

export function SpeechProvider({ children }) {
  const speech = useSpeechSynthesis();
  return <SpeechContext.Provider value={speech}>{children}</SpeechContext.Provider>;
}

export function useSpeech() {
  const ctx = useContext(SpeechContext);
  if (!ctx) throw new Error('useSpeech must be used inside <SpeechProvider>');
  return ctx;
}

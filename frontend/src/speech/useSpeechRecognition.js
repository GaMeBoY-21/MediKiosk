// Owner: Ranjith
// Speech-to-text. Continuous, with interim results so the patient sees words
// appear while they talk — that feedback is what tells a first-time user the
// machine is actually hearing them.
//
// Touch is always a complete path through the flow, so every consumer of this
// hook must still work when isSupported is false.

import { useCallback, useEffect, useRef, useState } from 'react';

function getRecognitionCtor() {
  if (typeof window === 'undefined') return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export function useSpeechRecognition(lang = 'en-IN') {
  const Ctor = getRecognitionCtor();
  const isSupported = Boolean(Ctor);

  const [transcript, setTranscript] = useState('');
  const [interim, setInterim] = useState('');
  const [listening, setListening] = useState(false);
  const [error, setError] = useState(null);

  const recRef = useRef(null);
  const wantListeningRef = useRef(false);
  const finalRef = useRef('');

  useEffect(() => {
    if (!isSupported) {
      console.info('[speech] SpeechRecognition unsupported; touch-only path');
      return undefined;
    }

    const rec = new Ctor();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = lang;

    rec.onresult = (event) => {
      let pending = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) finalRef.current += `${result[0].transcript} `;
        else pending += result[0].transcript;
      }
      setTranscript(finalRef.current.trim());
      setInterim(pending.trim());
    };

    rec.onerror = (event) => {
      // A patient pausing to think fires no-speech constantly. Not an error.
      if (event.error === 'no-speech' || event.error === 'aborted') return;
      console.warn('[speech] recognition error:', event.error);
      setError(event.error);
      wantListeningRef.current = false;
      setListening(false);
    };

    rec.onend = () => {
      // Chrome ends the session on its own every ~60s. Restart while we still
      // want to be listening, otherwise the mic silently goes dead mid-answer.
      if (wantListeningRef.current) {
        try {
          rec.start();
          return;
        } catch (e) {
          console.warn('[speech] could not restart recognition:', e);
        }
      }
      setListening(false);
    };

    recRef.current = rec;

    return () => {
      wantListeningRef.current = false;
      rec.onresult = null;
      rec.onerror = null;
      rec.onend = null;
      try {
        rec.abort();
      } catch {
        /* already stopped */
      }
      recRef.current = null;
    };
  }, [Ctor, isSupported, lang]);

  const start = useCallback(() => {
    if (!recRef.current) return;
    setError(null);
    wantListeningRef.current = true;
    try {
      recRef.current.start();
      setListening(true);
    } catch {
      // start() throws if already running — that is fine, we are listening.
      setListening(true);
    }
  }, []);

  const stop = useCallback(() => {
    wantListeningRef.current = false;
    setListening(false);
    if (!recRef.current) return;
    try {
      recRef.current.stop();
    } catch {
      /* already stopped */
    }
  }, []);

  const reset = useCallback(() => {
    finalRef.current = '';
    setTranscript('');
    setInterim('');
    setError(null);
  }, []);

  return { start, stop, reset, transcript, interim, listening, error, isSupported };
}

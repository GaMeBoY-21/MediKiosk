// Owner: Ranjith
// "Are you still there?" — spoken, with a visible countdown.

import { useEffect } from 'react';
import BigButton from './BigButton.jsx';
import { useT } from '../i18n/useT.js';
import { useSpeech } from '../speech/SpeechProvider.jsx';

export default function IdleTimeoutOverlay({ secondsLeft, onStay }) {
  const { tx, voice } = useT();
  const { speak } = useSpeech();
  const title = tx('timeout.title');

  useEffect(() => {
    speak(title.audio, voice);
  }, [title.audio, voice, speak]);

  return (
    <div className="overlay" role="alertdialog" aria-modal="true">
      <div className="overlay__inner">
        <h1 className="overlay__title">{title.label}</h1>
        <div className="overlay__count">{secondsLeft}</div>
        <BigButton variant="primary" center onClick={onStay}>
          {tx('timeout.continue').label}
        </BigButton>
      </div>
    </div>
  );
}

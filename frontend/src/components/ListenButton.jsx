// Owner: Ranjith
// The one control that produces audio.
//
// Sits on the question itself, not only in the bottom bar. The bottom bar is
// chrome a patient learns to ignore; this is part of the question they are
// looking at, which is where someone who cannot read needs to find it.
//
// Pressing while it is speaking stops playback. Two states, and they are
// distinguishable without colour or sound: the label changes and the icon
// changes with it.

import { Speaker } from './Icons.jsx';
import { useSpeech } from '../speech/SpeechProvider.jsx';

/** Square stop glyph. Deliberately not a second speaker icon — the two states
 *  must not look alike at a glance. */
function StopIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
    </svg>
  );
}

export default function ListenButton({ text, voice, label, stopLabel, className = '' }) {
  const { speak, cancel, speaking } = useSpeech();

  if (!text) return null;

  const toggle = () => {
    if (speaking) cancel();
    else speak(text, voice);
  };

  return (
    <button
      type="button"
      className={`listen${speaking ? ' listen--speaking' : ''} ${className}`.trim()}
      onClick={toggle}
      aria-pressed={speaking}
    >
      {speaking ? <StopIcon /> : <Speaker />}
      <span className="listen__label">{speaking ? stopLabel : label}</span>
    </button>
  );
}

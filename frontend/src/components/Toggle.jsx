// Owner: Ranjith
// A consent toggle. Speaks its own label aloud when tapped, so a patient who
// cannot read still hears exactly what they just agreed to.

import { Check } from './Icons.jsx';
import { useSpeech } from '../speech/SpeechProvider.jsx';

export default function Toggle({ checked, onChange, label, audio, voice }) {
  const { speak } = useSpeech();

  const handleClick = () => {
    const next = !checked;
    onChange(next);
    if (audio) speak(audio, voice);
  };

  return (
    <button
      type="button"
      className={`toggle${checked ? ' toggle--on' : ''}`}
      onClick={handleClick}
      role="switch"
      aria-checked={checked}
    >
      <span className="toggle__box">
        <Check />
      </span>
      <span>{label}</span>
    </button>
  );
}

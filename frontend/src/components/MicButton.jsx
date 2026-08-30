// Owner: Ranjith
// 140px circle. Pulses while listening — one of only two animations in the app.
// When recognition is unsupported the button is disabled and the hint tells the
// patient to tap their answer instead; the touch path is always complete.

import { Mic } from './Icons.jsx';

export default function MicButton({
  listening,
  onStart,
  onStop,
  supported = true,
  labelIdle,
  labelListening,
  labelUnsupported,
}) {
  const hint = !supported ? labelUnsupported : listening ? labelListening : labelIdle;

  return (
    <div className="mic-block">
      <button
        type="button"
        className={`mic${listening ? ' mic--listening' : ''}`}
        onClick={listening ? onStop : onStart}
        disabled={!supported}
        aria-label={hint}
        aria-pressed={listening}
      >
        <Mic />
      </button>
      <span className="mic-block__hint">{hint}</span>
    </div>
  );
}

// Owner: Ranjith
// Every patient screen wraps in this. It owns the three things that must be
// identical on every screen so they become familiar rather than read:
//
//   1. seven progress dots, top
//   2. the spoken prompt, fired automatically on mount
//   3. the fixed 96px bottom bar: [Repeat] [Back], same place, same size
//
// Note on the "max three interactive elements" rule: the bottom bar is chrome,
// not content. The budget applies to the screen's own controls, and a grid of
// option tiles counts as one control.

import { useEffect, useRef } from 'react';
import ProgressDots from './ProgressDots.jsx';
import { ArrowLeft, Speaker } from './Icons.jsx';
import { useSpeech } from '../speech/SpeechProvider.jsx';
import { useSession, PROGRESS_STEPS } from '../state/SessionContext.jsx';
import { useT } from '../i18n/useT.js';

export default function ScreenShell({
  /** { label, audio } — spoken on mount, shown as the 40px question */
  prompt,
  /** override what Repeat says, when the prompt is not the whole instruction */
  repeatAudio,
  /** hide the question heading but still speak the prompt */
  hideHeading = false,
  children,
  onBack,
  footer,
}) {
  const { screen, back } = useSession();
  const { voice, label } = useT();
  const { speak, cancel } = useSpeech();

  const spoken = prompt?.audio || prompt?.label || '';
  const toRepeat = repeatAudio ?? spoken;

  // Speak the instruction whenever the screen — or the question on it — changes.
  // The Interview screen keeps the same shell across many questions, so this
  // deliberately keys on the sentence rather than on mount alone.
  const lastSpoken = useRef(null);
  useEffect(() => {
    if (!spoken || lastSpoken.current === spoken) return;
    lastSpoken.current = spoken;
    speak(spoken, voice);
  }, [spoken, voice, speak]);

  // Never let one screen's audio bleed into the next.
  useEffect(() => cancel, [cancel, screen]);

  const handleBack = () => {
    cancel();
    (onBack ?? back)();
  };

  return (
    <div className="shell fade-in" key={screen}>
      <div className="shell__top">
        <ProgressDots step={PROGRESS_STEPS[screen]} />
      </div>

      <main className="shell__main">
        {prompt && !hideHeading ? <h1 className="shell__question">{prompt.label}</h1> : null}
        {children}
      </main>

      {footer}

      <nav className="shell__bar">
        <button
          type="button"
          className="shell__bar-btn"
          onClick={() => speak(toRepeat, voice)}
        >
          <Speaker />
          <span>{label('common.repeat')}</span>
        </button>
        <button type="button" className="shell__bar-btn" onClick={handleBack}>
          <ArrowLeft />
          <span>{label('common.back')}</span>
        </button>
      </nav>
    </div>
  );
}

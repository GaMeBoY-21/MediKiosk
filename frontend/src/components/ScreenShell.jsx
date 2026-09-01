// Owner: Ranjith
// Every patient screen wraps in this. It owns the three things that must be
// identical on every screen so they become familiar rather than read:
//
//   1. the phase label, top
//   2. the spoken prompt, fired automatically the first time each node is seen
//   3. the fixed 96px bottom bar: [Repeat] [Back], same place, same size
//
// Note on the "max three interactive elements" rule: the bottom bar is chrome,
// not content. The budget applies to the screen's own controls, and a grid of
// option tiles counts as one control.

import { useEffect } from 'react';
import BilingualText from './BilingualText.jsx';
import { ArrowLeft, Speaker } from './Icons.jsx';
import { useSpeech } from '../speech/SpeechProvider.jsx';
import { useSession } from '../state/SessionContext.jsx';
import { useT } from '../i18n/useT.js';

export default function ScreenShell({
  /** { label, audio } — spoken the first time this node is reached */
  prompt,
  /** override what Repeat says, when the prompt is not the whole instruction */
  repeatAudio,
  /** hide the question heading but still speak the prompt */
  hideHeading = false,
  /** patient-facing stage name from the API's `phase`. Absent renders nothing. */
  phase,
  /** force the English line even before a language is chosen — error and
   *  emergency screens, which staff read. */
  alwaysBilingual = false,
  /** English of the prompt, when it is clinical content from the API rather
   *  than a string with an entry in strings.js. */
  promptEnglish,
  /** identifies what is being spoken, so it is spoken exactly once */
  speechKey,
  children,
  onBack,
  footer,
}) {
  const { screen, back, hasSpoken, markSpoken } = useSession();
  const { voice, label } = useT();
  const { speak, cancel } = useSpeech();

  const spoken = prompt?.audio || prompt?.label || '';
  const toRepeat = repeatAudio ?? spoken;

  // Speak each question exactly once, the first time the patient reaches it.
  //
  // Keyed on node id (via speechKey), tracked in SessionContext. The previous
  // version compared the sentence text against a ref, which re-spoke on
  // back-navigation, re-spoke after any remount because the ref reset, and
  // stayed silent when two nodes shared wording. A ref cannot survive
  // navigation; session state can.
  //
  // Auto-speak stays. A patient who cannot read cannot find a Repeat button he
  // cannot read — Repeat is for asking again, not for hearing it the first time.
  const speakId = speechKey ?? `screen:${screen}`;
  useEffect(() => {
    if (!spoken || hasSpoken(speakId)) return;
    markSpoken(speakId);
    speak(spoken, voice);
  }, [spoken, speakId, voice, speak, hasSpoken, markSpoken]);

  // Never let one screen's audio bleed into the next.
  useEffect(() => cancel, [cancel, screen]);

  const handleBack = () => {
    cancel();
    (onBack ?? back)();
  };

  return (
    <div className="shell fade-in" key={screen}>
      {/* Phase label, not a progress count. The interview has no fixed
          length — it branches on what the patient says — so any "step 5 of 7"
          visibly desyncs. Nothing renders when the API sends no phase; there
          is deliberately no fallback to a count. */}
      <div className="shell__top">
        {phase ? <p className="shell__phase">{phase}</p> : null}
      </div>

      <main className="shell__main">
        {prompt && !hideHeading ? (
          <BilingualText
            as="h1"
            className="shell__question"
            always={alwaysBilingual}
            english={promptEnglish}
          >
            {prompt.label}
          </BilingualText>
        ) : null}
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
          <BilingualText always={alwaysBilingual}>{label('common.repeat')}</BilingualText>
        </button>
        <button type="button" className="shell__bar-btn" onClick={handleBack}>
          <ArrowLeft />
          <BilingualText always={alwaysBilingual}>{label('common.back')}</BilingualText>
        </button>
      </nav>
    </div>
  );
}

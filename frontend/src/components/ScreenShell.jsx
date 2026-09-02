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
import ListenButton from './ListenButton.jsx';
import { ArrowLeft } from './Icons.jsx';
import { useSpeech } from '../speech/SpeechProvider.jsx';
import { useSession } from '../state/SessionContext.jsx';
import { useT } from '../i18n/useT.js';
import { DEFAULT_LANG, bcp47, t, strings } from '../i18n/strings.js';

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
  /** Render this screen in English only, ignoring session language entirely.
   *  For the language screen, which is shown before a language exists — and
   *  which must still be English when the patient navigates BACK to it. */
  englishOnly = false,
  /** the mic is active. The transcript must stay on screen while it is, so
   *  the layout lets the option tiles give up their space instead. */
  listening = false,
  children,
  onBack,
  footer,
}) {
  const { screen, back } = useSession();
  const { voice: sessionVoice, label: sessionLabel } = useT();
  // On an English-only screen the chrome and the audio ignore session state
  // too, otherwise Back would bring a chosen language back with it.
  const label = englishOnly ? (key) => t(DEFAULT_LANG, key).label : sessionLabel;
  const voice = englishOnly ? bcp47(DEFAULT_LANG) : sessionVoice;
  const { cancel } = useSpeech();

  // The API sends a phase KEY ('hpi'), not a sentence, so the label resolves
  // here in the patient's language. Recordings made before that change still
  // carry the English sentence: anything that is not a known key falls through
  // and renders as it arrived, rather than disappearing off the screen.
  const isPhaseKey = Boolean(phase && strings[DEFAULT_LANG]?.phase?.[phase]);
  const phaseLabel = isPhaseKey ? label(`phase.${phase}`) : phase;

  // When the model gives us nothing usable the question comes back empty and
  // the stage label stands in as the heading. It is already translated, which
  // the stage label held on the node is not.
  const heading = prompt?.label || (isPhaseKey ? phaseLabel : '');

  const spoken = prompt?.audio || prompt?.label || '';
  const toRepeat = repeatAudio ?? spoken;

  // NO auto-speak. Audio plays only when the patient presses Listen.
  //
  // Every screen used to speak itself on arrival. In a shared OPD hall that is
  // a machine talking over the person using it, and it read a patient's own
  // answers back out loud within earshot of the queue. The language screen is
  // the single exception and speaks its own prompt there, so that a patient
  // who cannot read still discovers that the button exists.

  // Never let one screen's audio bleed into the next.
  // Also keyed on the text: `screen` stays SCREENS.INTERVIEW for every
  // question in the interview, so this only ever fired between screens and an
  // utterance the patient asked for on one question carried on into the wait
  // for the next one — which is what a kiosk talking to itself sounds like.
  useEffect(() => cancel, [cancel, screen, toRepeat]);

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
        {phaseLabel ? (
          <BilingualText as="p" className="shell__phase" always={alwaysBilingual}>
            {phaseLabel}
          </BilingualText>
        ) : null}
      </div>

      <main className={`shell__main${listening ? ' shell__main--listening' : ''}`}>
        {heading && !hideHeading ? (
          <BilingualText
            as="h1"
            className="shell__question"
            always={alwaysBilingual}
            englishOnly={englishOnly}
            english={promptEnglish}
          >
            {heading}
          </BilingualText>
        ) : null}

        {/* Attached to the question, not buried in the bottom bar. */}
        <ListenButton
          className="listen--question"
          text={toRepeat}
          voice={voice}
          label={label('common.listen')}
          stopLabel={label('common.stop')}
        />
        {children}
      </main>

      {footer}

      <nav className="shell__bar">
        <ListenButton
          className="shell__bar-btn"
          text={toRepeat}
          voice={voice}
          label={label('common.repeat')}
          stopLabel={label('common.stop')}
        />
        <button type="button" className="shell__bar-btn" onClick={handleBack}>
          <ArrowLeft />
          <BilingualText always={alwaysBilingual} englishOnly={englishOnly}>
            {label('common.back')}
          </BilingualText>
        </button>
      </nav>
    </div>
  );
}

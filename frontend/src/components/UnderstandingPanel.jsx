// Owner: Ranjith
// What the kiosk has understood so far, shown beside the transcript.
//
// This is the difference between a tape recorder and an intake system. The
// transcript shows what the patient said; this shows what became structured
// clinical data, filling in as they talk:
//
//     Where: chest      Since: 2 days      Spreads to: left arm
//
// Driven entirely by the `extracted` array on the answer response, which is
// cumulative for the whole session — so fields accumulate across questions and
// never reset per turn.

import { fieldLabel } from '../i18n/fieldNames.js';
import { useT } from '../i18n/useT.js';

// Below this, the model was not sure enough to state the value plainly.
// Matches ai/summary/generator.py's LOW_CONFIDENCE_THRESHOLD, so the kiosk and
// the physician's summary hedge the same fields.
const CONFIDENT = 0.7;

// The panel showed every field it was given and grew until the bottom of the
// list ran off the screen — at 1280x800 with a full history the last rows were
// simply cut off at the viewport edge, and the patient had no way to know
// anything was missing.
//
// Six, and a "+N more" line for the rest. Not an internal scrollbar: nothing
// else in this app scrolls, so a scrollbar here is a control the patient has to
// discover, and the ones who need this panel most are the ones least likely to
// find it. The count is what matters — it says the kiosk still holds the rest.
//
// The most RECENT six, because those are the ones the patient just said and is
// checking. The earlier ones they have already seen go right.
const MAX_VISIBLE = 6;

function displayValue(value) {
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'boolean') return value ? '✓' : '—';
  return String(value ?? '');
}

export default function UnderstandingPanel({ extracted }) {
  const { lang, label } = useT();

  // Nothing understood yet: render nothing at all. A placeholder box would
  // promise the patient something is happening when it is not.
  if (!Array.isArray(extracted) || extracted.length === 0) return null;

  const items = extracted.filter((f) => f && f.name && displayValue(f.value) !== '');
  if (items.length === 0) return null;

  const hidden = Math.max(0, items.length - MAX_VISIBLE);
  const visible = hidden ? items.slice(-MAX_VISIBLE) : items;

  return (
    <section className="understanding" aria-label={label('common.understood')}>
      <h2 className="understanding__title">{label('common.understood')}</h2>
      <ul className="understanding__list">
        {visible.map((f) => {
          const unsure = typeof f.confidence === 'number' && f.confidence < CONFIDENT;
          return (
            <li
              key={f.name}
              className={`understanding__item${unsure ? ' understanding__item--unsure' : ''}`}
            >
              <span className="understanding__key">{fieldLabel(f.name, lang)}</span>
              <span className="understanding__value">
                {displayValue(f.value)}
                {/* An uncertain field must never look like a confident one.
                    Lighter weight alone would not survive a projector or a
                    colour-blind viewer, so it carries a mark as well. */}
                {unsure ? (
                  <span
                    className="understanding__unsure-mark"
                    title={label('common.notSure')}
                    aria-label={label('common.notSure')}
                  >
                    ?
                  </span>
                ) : null}
              </span>
            </li>
          );
        })}
      </ul>
      {hidden ? (
        <p className="understanding__more">
          {label('common.moreFields').replace('{n}', String(hidden))}
        </p>
      ) : null}
    </section>
  );
}

// Owner: Ranjith
// The one place the bilingual rule lives.
//
//   before a language is chosen : English only — there is nothing to honour
//                                 yet, so do not guess
//   after, non-English chosen   : chosen language full size, English beneath
//                                 at ~60% in --ink-soft
//   after, English chosen       : rendered once, not twice
//
// Audio is deliberately untouched: speech stays in the single chosen language,
// because speaking both would double the length of every question.
//
// Text with no English counterpart renders once. That covers interview
// questions and option tiles, which arrive from the API already translated —
// there is no second version of them on the client to show.

import { englishFor } from '../i18n/strings.js';
import { useOptionalSession } from '../state/SessionContext.jsx';

export default function BilingualText({
  children,
  /** Render bilingually even before a language is chosen. Error and emergency
   *  screens set this: the person reading them is usually staff, who may not
   *  share the patient's language. */
  always = false,
  /** Render English once, never bilingually, whatever is in session state.
   *  The language screen sets this: it is shown before a language exists, so
   *  there is nothing to translate into and nothing to put underneath. */
  englishOnly = false,
  /** The English line, supplied explicitly. Clinical content — the interview
   *  question and its option tiles — is generated per patient, so it has no
   *  entry in strings.js to look up. The API returns its English alongside it
   *  (question_en / label_en) and it arrives here. Null means render once. */
  english: englishProp,
  className = '',
  as: Tag = 'span',
}) {
  // Deliberately NOT useT(): this component is used by BigButton and the
  // tiles, which the physician console could reasonably reuse — and that tree
  // renders outside SessionProvider. No session simply means no chosen
  // language, which already means English only.
  const session = useOptionalSession();
  const chosen = !englishOnly && Boolean(session?.languageChosen);
  const lang = chosen ? session.language : 'en';

  const text = typeof children === 'string' ? children : null;
  // An explicit English line always wins over the lookup: it came from the
  // same model call that produced the primary text, so it actually matches.
  const looked = text && (chosen || always) && lang !== 'en' ? englishFor(text, lang) : undefined;
  const candidate = englishProp ?? looked;
  // Never render the same sentence twice.
  const secondary = englishOnly ? undefined : (candidate && candidate !== text ? candidate : undefined);

  if (!secondary) {
    // One language: English is the choice, nothing is chosen yet, or this
    // string has no counterpart. Render plainly, with no wrapper that would
    // change layout.
    return <Tag className={className}>{children}</Tag>;
  }

  return (
    <Tag className={`bilingual ${className}`.trim()}>
      <span className="bilingual__primary">{text}</span>
      {/* aria-hidden: a screen reader already read the primary line. Reading
          the same sentence twice is noise, not accessibility. */}
      <span className="bilingual__english" aria-hidden="true">
        {secondary}
      </span>
    </Tag>
  );
}

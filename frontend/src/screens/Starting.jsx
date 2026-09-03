// Owner: Ranjith
// Shown while POST /api/session/start is open.
//
// Not a screen of the flow — it has no place in the navigation stack and the
// patient can neither advance nor go back from it. It stands in for whichever
// session-dependent screen is next until that screen has an id to work with
// (see NEEDS_SESSION in Kiosk.jsx). Opening a session takes as long as the
// model takes to compose the opening question, which is seconds, not
// milliseconds; the patient is told that rather than shown a screen whose
// buttons quietly 404.
//
// Static text, deliberately. Nothing else in this app moves, and a spinner
// here would be the only animation a patient sees all session.

import { DEFAULT_LANG, t } from '../i18n/strings.js';

// Matches Idle.jsx. Not a product name: this kiosk belongs to the hospital it
// stands in.
const HOSPITAL = 'District Government Hospital';


export default function Starting({ lang }) {
  // Before a language is picked there is nothing to honour, so English it is —
  // the same rule BilingualText follows.
  const chosen = lang || DEFAULT_LANG;
  const wait = t(chosen, 'common.oneMoment').label;

  return (
    <div className="starting fade-in" role="status" aria-live="polite">
      {/* The same header the idle screen carries. This is the one screen a
          patient may sit in front of for several seconds, so it says whose
          kiosk it is rather than nothing at all. */}
      <div className="starting__brand">{t(DEFAULT_LANG, 'idle.subtitle').label}</div>
      <div className="starting__hospital">{HOSPITAL}</div>
      <p className="starting__wait" lang={chosen}>
        {wait}
      </p>
      {/* English underneath, always. Staff read this screen too and do not
          necessarily share the patient's language. It is not a translation of
          the line above, so it stays readable rather than aria-hidden. */}
      <p className="starting__english">Starting your session…</p>
    </div>
  );
}

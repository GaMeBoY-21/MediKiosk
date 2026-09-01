// Owner: Ranjith
// Refusing must be a calm, complete ending — not a dead end or a nag screen.
// No retry button: they said no, and they are still seeing the doctor.

import { useEffect } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import { useT } from '../i18n/useT.js';
import { useSession } from '../state/SessionContext.jsx';
import BilingualText from '../components/BilingualText.jsx';

const RETURN_MS = 20000;

export default function ConsentDeclined() {
  const { tx } = useT();
  const { reset } = useSession();

  useEffect(() => {
    const id = setTimeout(reset, RETURN_MS);
    return () => clearTimeout(id);
  }, [reset]);

  const body = tx('consent.declinedBody');

  return (
    <ScreenShell
      prompt={{ label: tx('consent.declinedTitle').label, audio: body.audio }}
      repeatAudio={body.audio}
    >
      <BilingualText as="p" className="consent__text">{body.label}</BilingualText>
    </ScreenShell>
  );
}

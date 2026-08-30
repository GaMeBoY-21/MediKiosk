// Owner: Ranjith
// ABHA / Aadhaar entry. Huge 0-9 keys, masked display, no physical keyboard.
//
// The number is masked as it is typed: an OPD corridor is a public place and
// the person behind you can read a 12-digit number off a tablet easily.

import { useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import Keypad from '../components/Keypad.jsx';
import { useT } from '../i18n/useT.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';
import { verifyIdentity } from '../api/client.js';

const LENGTH = { abha: 14, aadhaar: 12 };

export default function NumberEntry({ kind }) {
  const { tx } = useT();
  const { setPatient, go } = useSession();
  const [digits, setDigits] = useState('');
  const [checking, setChecking] = useState(false);

  const max = LENGTH[kind];
  const prompt = tx(kind === 'abha' ? 'identify.abhaTitle' : 'identify.aadhaarTitle');

  const push = (d) => setDigits((v) => (v.length >= max ? v : v + d));
  const pop = () => setDigits((v) => v.slice(0, -1));

  const submit = async () => {
    setChecking(true);
    // TODO: MOCKED. Real verification is a server-side call against the ABDM
    // gateway — the kiosk must never hold or forward these numbers itself.
    const res = await verifyIdentity(kind, digits);
    setPatient({ idKind: kind, idMasked: res.masked });
    setChecking(false);
    go(SCREENS.CONSENT);
  };

  return (
    <ScreenShell prompt={prompt}>
      <div className={`keypad__display${digits ? '' : ' keypad__display--empty'}`}>
        {digits ? '•'.repeat(digits.length) : prompt.label}
      </div>

      <Keypad mode="numeric" onKey={push} onDelete={pop} deleteLabel="Delete" />

      <BigButton
        variant="primary"
        center
        onClick={submit}
        disabled={digits.length !== max || checking}
      >
        {checking ? tx('identify.checking').label : tx('common.next').label}
      </BigButton>
    </ScreenShell>
  );
}

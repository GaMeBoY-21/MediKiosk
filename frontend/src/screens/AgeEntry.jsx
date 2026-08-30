// Owner: Ranjith
// New patient, part 2 of 3: age. Numeric keypad only — no masking, an age is
// not sensitive the way an ID number is, and seeing it typed helps.

import { useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import Keypad from '../components/Keypad.jsx';
import { useT } from '../i18n/useT.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';

export default function AgeEntry() {
  const { tx } = useT();
  const { setPatient, go } = useSession();
  const [age, setAge] = useState('');

  const submit = () => {
    setPatient({ age });
    go(SCREENS.SEX);
  };

  return (
    <ScreenShell prompt={tx('identify.ageTitle')}>
      <div className={`keypad__display${age ? '' : ' keypad__display--empty'}`}>
        {age || tx('identify.ageTitle').label}
      </div>

      <Keypad
        mode="numeric"
        onKey={(d) => setAge((v) => (v.length >= 3 ? v : v + d))}
        onDelete={() => setAge((v) => v.slice(0, -1))}
        deleteLabel="Delete"
      />

      <BigButton variant="primary" center onClick={submit} disabled={!age}>
        {tx('common.next').label}
      </BigButton>
    </ScreenShell>
  );
}

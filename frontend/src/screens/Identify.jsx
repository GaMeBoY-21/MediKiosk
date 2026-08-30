// Owner: Ranjith
// Screen 3. Three stacked options, nothing else.

import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import { IdCard, Person } from '../components/Icons.jsx';
import { useT } from '../i18n/useT.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';

export default function Identify() {
  const { tx } = useT();
  const { go, setPatient } = useSession();

  const choose = (idKind, screen) => {
    setPatient({ idKind });
    go(screen);
  };

  return (
    <ScreenShell prompt={tx('identify.title')}>
      <div className="stack">
        <BigButton variant="surface" icon={IdCard} onClick={() => choose('abha', SCREENS.ABHA)}>
          {tx('identify.abha').label}
        </BigButton>
        <BigButton
          variant="surface"
          icon={IdCard}
          onClick={() => choose('aadhaar', SCREENS.AADHAAR)}
        >
          {tx('identify.aadhaar').label}
        </BigButton>
        <BigButton variant="surface" icon={Person} onClick={() => choose(null, SCREENS.NAME)}>
          {tx('identify.newHere').label}
        </BigButton>
      </div>
    </ScreenShell>
  );
}

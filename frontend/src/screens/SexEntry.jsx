// Owner: Ranjith
// New patient, part 3 of 3: sex. Three icon tiles, never a dropdown —
// a dropdown is a reading task and a fiddly touch target at once.

import ScreenShell from '../components/ScreenShell.jsx';
import IconTile from '../components/IconTile.jsx';
import { Female, Male, OtherSex } from '../components/Icons.jsx';
import { useT } from '../i18n/useT.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';

const OPTIONS = [
  { value: 'male', icon: Male, key: 'identify.male' },
  { value: 'female', icon: Female, key: 'identify.female' },
  { value: 'other', icon: OtherSex, key: 'identify.otherSex' },
];

export default function SexEntry() {
  const { tx } = useT();
  const { setPatient, go } = useSession();

  const choose = (value) => {
    setPatient({ sex: value });
    go(SCREENS.CONSENT);
  };

  return (
    <ScreenShell prompt={tx('identify.sexTitle')}>
      <div className="grid-3">
        {OPTIONS.map((o) => (
          <IconTile
            key={o.value}
            icon={o.icon}
            label={tx(o.key).label}
            onSelect={() => choose(o.value)}
          />
        ))}
      </div>
    </ScreenShell>
  );
}

// Owner: Ranjith
// A consent toggle. SILENT when tapped: audio in this app plays only on an
// explicit press of the speaker button, so this no longer reads itself back.
// The comment used to claim it spoke, which stopped being true when tap-to-
// speak was removed app-wide.

import { Check } from './Icons.jsx';
import BilingualText from './BilingualText.jsx';

export default function Toggle({ checked, onChange, label }) {
  const handleClick = () => {
    onChange(!checked);
  };

  return (
    <button
      type="button"
      className={`toggle${checked ? ' toggle--on' : ''}`}
      onClick={handleClick}
      role="switch"
      aria-checked={checked}
    >
      <span className="toggle__box">
        <Check />
      </span>
      <BilingualText>{label}</BilingualText>
    </button>
  );
}

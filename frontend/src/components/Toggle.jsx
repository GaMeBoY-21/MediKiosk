// Owner: Ranjith
// A consent toggle. Speaks its own label aloud when tapped, so a patient who
// cannot read still hears exactly what they just agreed to.

import { Check } from './Icons.jsx';

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
      <span>{label}</span>
    </button>
  );
}

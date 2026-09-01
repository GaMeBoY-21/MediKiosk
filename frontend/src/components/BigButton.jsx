// Owner: Ranjith
// Minimum 80px tall. Optional leading icon, always with its text label.
//
// Wraps its label in BilingualText, so every button in the app follows the
// bilingual rule without any screen passing anything extra.

import BilingualText from './BilingualText.jsx';

export default function BigButton({
  children,
  onClick,
  variant = 'primary',
  icon: Icon,
  disabled = false,
  center = false,
  type = 'button',
}) {
  return (
    <button
      type={type}
      className={`btn btn--${variant}${center ? ' btn--center' : ''}`}
      onClick={onClick}
      disabled={disabled}
    >
      {Icon ? <Icon /> : null}
      <BilingualText>{children}</BilingualText>
    </button>
  );
}

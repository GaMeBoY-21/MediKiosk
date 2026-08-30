// Owner: Ranjith
// Minimum 80px tall. Optional leading icon, always with its text label.

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
      <span>{children}</span>
    </button>
  );
}

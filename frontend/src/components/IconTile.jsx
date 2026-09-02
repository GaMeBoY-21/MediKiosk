// Owner: Ranjith
// A large icon paired with a text label. Tapping is SILENT: it speaks
// confirmation — a patient who cannot read needs to hear what they just chose.


import BilingualText from './BilingualText.jsx';

export default function IconTile({
  icon: Icon,
  label,
  onSelect,
  selected = false,
  variant = '',
}) {
  const handleClick = () => {
    onSelect?.();
  };

  return (
    <button
      type="button"
      className={`tile${variant ? ` tile--${variant}` : ''}${selected ? ' tile--selected' : ''}`}
      onClick={handleClick}
      aria-pressed={selected}
    >
      {Icon ? <Icon /> : null}
      <BilingualText className="tile__label">{label}</BilingualText>
    </button>
  );
}

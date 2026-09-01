// Owner: Ranjith
// A large icon paired with a text label. Tapping speaks the label back as
// confirmation — a patient who cannot read needs to hear what they just chose.

import { useSpeech } from '../speech/SpeechProvider.jsx';

import BilingualText from './BilingualText.jsx';

export default function IconTile({
  icon: Icon,
  label,
  audio,
  onSelect,
  selected = false,
  voice,
  variant = '',
}) {
  const { speak } = useSpeech();

  const handleClick = () => {
    if (audio) speak(audio, voice);
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

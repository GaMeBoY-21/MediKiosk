// Owner: Ranjith
// "Play again" control. Speaks a given sentence on demand.

import { Speaker } from './Icons.jsx';
import { useSpeech } from '../speech/SpeechProvider.jsx';

export default function SpeakerButton({ text, voice, label }) {
  const { speak } = useSpeech();
  return (
    <button type="button" className="speaker" onClick={() => speak(text, voice)}>
      <Speaker />
      <span>{label}</span>
    </button>
  );
}

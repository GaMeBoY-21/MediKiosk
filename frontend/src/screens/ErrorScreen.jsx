// Owner: Ranjith
// A patient never sees a stack trace or an error code. They get a spoken
// sentence and a staff-attention screen; the detail goes to the console.

import { useEffect } from 'react';
import BigButton from '../components/BigButton.jsx';
import { t, bcp47, DEFAULT_LANG } from '../i18n/strings.js';
import { useSpeechSynthesis } from '../speech/useSpeechSynthesis.js';
import BilingualText from '../components/BilingualText.jsx';


export default function ErrorScreen({ lang = DEFAULT_LANG, onRestart }) {
  const { speak } = useSpeechSynthesis();
  const title = t(lang, 'error.title');

  useEffect(() => {
  }, [title.audio, lang, speak]);

  return (
    <div className="errorscreen fade-in" role="alert">
      <BilingualText as="h1" className="errorscreen__title" always>
        {title.label}
      </BilingualText>
      <BilingualText as="p" className="errorscreen__body" always>
        {t(lang, 'error.body').label}
      </BilingualText>
      <p className="errorscreen__staff">{t(lang, 'error.staff').label}</p>
      <BigButton variant="outline" center onClick={onRestart}>
        {t(lang, 'error.restart').label}
      </BigButton>
    </div>
  );
}

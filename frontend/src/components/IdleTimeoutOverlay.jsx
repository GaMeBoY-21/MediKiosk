// Owner: Ranjith
// "Are you still there?" — spoken, with a visible countdown.

import BigButton from './BigButton.jsx';
import { useT } from '../i18n/useT.js';

export default function IdleTimeoutOverlay({ secondsLeft, onStay }) {
  const { tx } = useT();
  const title = tx('timeout.title');

  return (
    <div className="overlay" role="alertdialog" aria-modal="true">
      <div className="overlay__inner">
        <h1 className="overlay__title">{title.label}</h1>
        <div className="overlay__count">{secondsLeft}</div>
        <BigButton variant="primary" center onClick={onStay}>
          {tx('timeout.continue').label}
        </BigButton>
      </div>
    </div>
  );
}

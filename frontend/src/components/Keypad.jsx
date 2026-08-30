// Owner: Ranjith
// On-screen entry. No physical keyboard is assumed — the kiosk has none.
//
// mode="numeric" — huge 0-9 keys, for ABHA / Aadhaar / age
// mode="alpha"   — A-Z, so a patient whose speech recognition fails can still
//                  give a name by touch

import { Cross } from './Icons.jsx';

const DIGITS = ['1', '2', '3', '4', '5', '6', '7', '8', '9'];
const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

export default function Keypad({ mode = 'numeric', onKey, onDelete, deleteLabel }) {
  const keys = mode === 'alpha' ? LETTERS : DIGITS;

  return (
    <div className={`keypad${mode === 'alpha' ? ' keypad--alpha' : ''}`}>
      {keys.map((k) => (
        <button key={k} type="button" className="keypad__key" onClick={() => onKey(k)}>
          {k}
        </button>
      ))}

      {mode === 'alpha' ? (
        <button
          type="button"
          className="keypad__key keypad__key--wide"
          onClick={() => onKey(' ')}
        >
          ␣
        </button>
      ) : (
        <button type="button" className="keypad__key" onClick={() => onKey('0')}>
          0
        </button>
      )}

      <button
        type="button"
        className={`keypad__key${mode === 'numeric' ? ' keypad__key--wide' : ''}`}
        onClick={onDelete}
        aria-label={deleteLabel}
      >
        <Cross />
      </button>
    </div>
  );
}

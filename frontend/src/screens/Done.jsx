// Owner: Ranjith
// Screen 9. Token number, room, and a spoken instruction to wait.
// Returns to Idle after 30s — the next patient must not find this on screen.
//
// No bottom bar: there is nothing left to repeat or go back to.

import { useEffect } from 'react';
import { useT } from '../i18n/useT.js';
import { useSession } from '../state/SessionContext.jsx';
import { endSession } from '../api/client.js';

const RETURN_MS = 30000;

export default function Done() {
  const { tx } = useT();
  const { sessionId, summary, reset } = useSession();

  const token = summary?.token ?? '—';
  const room = summary?.room ?? '—';
  const wait = tx('done.wait');

  useEffect(() => {
    endSession(sessionId).catch((e) => console.warn('[done] endSession failed:', e));
    const id = setTimeout(reset, RETURN_MS);
    return () => clearTimeout(id);
    // Run once on mount: this screen never changes while it is up.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="done fade-in">
      <h1 className="done__title">{tx('done.title').label}</h1>

      <div className="done__panel">
        <div className="done__caption">{tx('done.token').label}</div>
        <div className="done__token">{token}</div>
      </div>

      <div className="done__panel">
        <div className="done__caption">{tx('done.room').label}</div>
        <div className="done__room">{room}</div>
      </div>

      <p className="done__wait">{wait.label}</p>
    </div>
  );
}

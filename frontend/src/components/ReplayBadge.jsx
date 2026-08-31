// Owner: Ranjith
// Persistent marker shown whenever VITE_REPLAY=true.
//
// Its whole job is to make it impossible to demo a recording while believing
// it is live. It never hides, never fades, and sits above everything — a
// replayed session is honest only if the person presenting it knows.

import { REPLAY } from '../api/client.js';

export default function ReplayBadge() {
  if (!REPLAY) return null;
  return (
    <div className="replay-badge" role="status" aria-live="off">
      REPLAY
    </div>
  );
}

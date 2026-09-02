// Owner: Ranjith
// Persistent marker shown whenever the app is serving the recording.
//
// Its whole job is to make it impossible to demo a recording while believing
// it is live. It never hides, never fades, and sits above everything — a
// replayed session is honest only if the person presenting it knows.
//
// Subscribes rather than reading once: replay can now be switched on mid-
// session from the keyboard, and a badge that only checked at mount would
// leave the screen looking live for the rest of the demo.

import { useEffect, useState } from 'react';
import { isReplay, subscribeReplay } from '../api/client.js';

export default function ReplayBadge() {
  const [on, setOn] = useState(isReplay);

  useEffect(() => {
    // Re-read on mount too: the switch may have fired before this mounted.
    setOn(isReplay());
    return subscribeReplay(setOn);
  }, []);

  if (!on) return null;
  return (
    <div className="replay-badge" role="status" aria-live="off">
      REPLAY
    </div>
  );
}

// Owner: Nikki
// The failure switch: Ctrl+Shift+R drops the kiosk into the recorded session.
//
// This is what gets pressed in front of judges when the wifi dies, the daily
// quota runs out, or a key turns out to be wrong. It has to work from
// wherever the demo happens to be standing — including the error screen,
// which is exactly where you will be when you need it.
//
// So it is mounted OUTSIDE the ErrorBoundary and outside Kiosk: if a screen
// has crashed or the API is unreachable, this component is still listening.
// It is registered on window in the capture phase for the same reason — no
// screen can swallow the key first.
//
// Ctrl+Shift+R is the browser's hard-reload shortcut and preventDefault()
// does stop it (verified in Chromium, headless and headed). That is also why
// the shortcut is worth having: it is the key a nervous person already
// reaches for when a page looks broken, and pressing it now does something
// useful instead of reloading a broken page.
//
// One way only. There is no keystroke back to live: a session half recorded
// and half real is one nobody could describe honestly afterwards.

import { useEffect } from 'react';
import { enableReplay, isReplay } from '../api/client.js';
import { useSession } from '../state/SessionContext.jsx';

export default function ReplaySwitch() {
  const { reset } = useSession();

  useEffect(() => {
    const onKey = (event) => {
      const isSwitch =
        (event.key === 'R' || event.key === 'r' || event.code === 'KeyR') &&
        event.ctrlKey &&
        event.shiftKey &&
        !event.altKey &&
        !event.metaKey;
      if (!isSwitch) return;

      // Stop the browser reloading the page out from under us. Without this
      // the tab reloads and comes straight back to the same live failure.
      event.preventDefault();
      event.stopPropagation();

      if (isReplay()) {
        // Already replaying: still restart, because the other reason to press
        // this is that the recording has run to the end and you want it again.
        reset();
        return;
      }
      enableReplay();
      // Back to the idle screen: the recording starts at its first turn, and
      // resuming a live session halfway into a recording would interleave two
      // different patients.
      reset();
    };

    window.addEventListener('keydown', onKey, true);
    return () => window.removeEventListener('keydown', onKey, true);
  }, [reset]);

  return null;
}

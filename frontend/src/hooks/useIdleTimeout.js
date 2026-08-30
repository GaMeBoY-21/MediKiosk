// Owner: Ranjith
// 90s of no interaction -> "Are you still there?" -> 15s countdown -> wipe.
//
// Patients walk away mid-session. Their medical history must never still be on
// the screen when the next person steps up.

import { useCallback, useEffect, useRef, useState } from 'react';

const IDLE_MS = 90000;
const COUNTDOWN_S = 15;
const ACTIVITY = ['pointerdown', 'keydown', 'touchstart'];

export function useIdleTimeout({ enabled, onTimeout }) {
  const [warning, setWarning] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(COUNTDOWN_S);

  const idleTimer = useRef(null);
  const countdownTimer = useRef(null);

  const clearAll = useCallback(() => {
    clearTimeout(idleTimer.current);
    clearInterval(countdownTimer.current);
  }, []);

  const armIdle = useCallback(() => {
    clearAll();
    setWarning(false);
    setSecondsLeft(COUNTDOWN_S);
    idleTimer.current = setTimeout(() => setWarning(true), IDLE_MS);
  }, [clearAll]);

  // Reset the clock on any interaction, but not while the warning is up —
  // there, only the explicit "Yes, continue" button counts as presence.
  useEffect(() => {
    if (!enabled) {
      clearAll();
      setWarning(false);
      return undefined;
    }
    if (warning) return undefined;

    armIdle();
    const onActivity = () => armIdle();
    ACTIVITY.forEach((e) => window.addEventListener(e, onActivity, { passive: true }));
    return () => {
      ACTIVITY.forEach((e) => window.removeEventListener(e, onActivity));
      clearAll();
    };
  }, [enabled, warning, armIdle, clearAll]);

  // Countdown, then wipe.
  useEffect(() => {
    if (!warning) return undefined;
    countdownTimer.current = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          clearInterval(countdownTimer.current);
          onTimeout();
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(countdownTimer.current);
  }, [warning, onTimeout]);

  const stayActive = useCallback(() => {
    setWarning(false);
    setSecondsLeft(COUNTDOWN_S);
    armIdle();
  }, [armIdle]);

  return { warning, secondsLeft, stayActive };
}

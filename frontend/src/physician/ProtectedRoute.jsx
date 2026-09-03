// Owner: Ranjith
// Gate on every /physician route.
//
// Two jobs:
//   1. No valid session -> show the login screen instead of the console.
//   2. Ten idle minutes -> log out, because this screen shows PHI for every
//      patient in the queue and doctors walk away from desks.
//
// The idle timer is separate from the kiosk's useIdleTimeout, which is tuned
// for a patient standing at a machine (90 seconds, with a spoken warning).
// A clinician needs a longer, quieter window and a hard logout at the end.

import { useCallback, useEffect, useRef, useState } from 'react';
import Login from './Login.jsx';
import { logout } from '../api/client.js';
import { snapshot, subscribe } from './authStore.js';

const IDLE_MS = 10 * 60 * 1000;
const ACTIVITY = ['pointerdown', 'keydown', 'touchstart', 'wheel'];

export default function ProtectedRoute({ children, onAuthenticated }) {
  const [auth, setAuth] = useState(snapshot);
  const [timedOut, setTimedOut] = useState(false);
  const timer = useRef(null);

  // authStore is the single source of truth: an API 401 clears it from under
  // us, and this re-renders straight to the login screen.
  useEffect(() => subscribe(setAuth), []);

  const signOut = useCallback(async (dueToIdle) => {
    setTimedOut(Boolean(dueToIdle));
    await logout();
  }, []);

  useEffect(() => {
    if (!auth.authenticated) return undefined;

    const arm = () => {
      clearTimeout(timer.current);
      timer.current = setTimeout(() => signOut(true), IDLE_MS);
    };
    arm();
    for (const ev of ACTIVITY) window.addEventListener(ev, arm, { passive: true });
    return () => {
      clearTimeout(timer.current);
      for (const ev of ACTIVITY) window.removeEventListener(ev, arm);
    };
  }, [auth.authenticated, signOut]);

  if (!auth.authenticated) {
    return (
      <>
        {timedOut ? (
          <p className="login__notice" role="status">
            Signed out after 10 minutes of inactivity.
          </p>
        ) : null}
        <Login
          onSignedIn={() => {
            setTimedOut(false);
            onAuthenticated?.();
          }}
        />
      </>
    );
  }

  return typeof children === 'function' ? children({ auth, signOut }) : children;
}

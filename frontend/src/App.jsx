// Owner: Ranjith
// Two destinations, one path check. A kiosk with a single linear flow and one
// console route does not need a router dependency.

import { useEffect, useState } from 'react';
import Kiosk from './Kiosk.jsx';
import Physician from './physician/Physician.jsx';
import ProtectedRoute from './physician/ProtectedRoute.jsx';
import ErrorBoundary from './components/ErrorBoundary.jsx';
import ReplayBadge from './components/ReplayBadge.jsx';
import ReplaySwitch from './components/ReplaySwitch.jsx';
import ErrorScreen from './screens/ErrorScreen.jsx';
import { SessionProvider } from './state/SessionContext.jsx';
import { SpeechProvider } from './speech/SpeechProvider.jsx';
import './components/components.css';
import './screens/screens.css';

function usePathname() {
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname);
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);
  return path;
}

export default function App() {
  const path = usePathname();

  // The badge wraps BOTH destinations: the physician console is replayed too,
  // and a recorded queue must not be mistaken for live patients either.
  // EVERY /physician route is behind the gate, including /physician/login
  // itself — ProtectedRoute renders the login form when there is no session,
  // so there is no path into the console that skips it.
  if (path.startsWith('/physician')) {
    return (
      <>
        <ReplayBadge />
        <ProtectedRoute>
          {({ auth, signOut }) => <Physician auth={auth} onSignOut={signOut} />}
        </ProtectedRoute>
      </>
    );
  }

  return (
    <SessionProvider>
      {/* Outside the ErrorBoundary on purpose: the switch has to work from
          the error screen, which is where it will be reached for. */}
      <ReplaySwitch />
      <ReplayBadge />
      <SpeechProvider>
        <ErrorBoundary
          fallback={(reset) => <ErrorScreen onRestart={reset} />}
          onReset={() => window.location.reload()}
        >
          <Kiosk />
        </ErrorBoundary>
      </SpeechProvider>
    </SessionProvider>
  );
}

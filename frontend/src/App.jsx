// Owner: Ranjith
// Two destinations, one path check. A kiosk with a single linear flow and one
// console route does not need a router dependency.

import { useEffect, useState } from 'react';
import Kiosk from './Kiosk.jsx';
import Physician from './physician/Physician.jsx';
import ErrorBoundary from './components/ErrorBoundary.jsx';
import ReplayBadge from './components/ReplayBadge.jsx';
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
  if (path.startsWith('/physician')) {
    return (
      <>
        <ReplayBadge />
        <Physician />
      </>
    );
  }

  return (
    <SessionProvider>
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

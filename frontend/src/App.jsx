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
import { Document, Person } from './components/Icons.jsx';
import { SessionProvider } from './state/SessionContext.jsx';
import { DEFAULT_LANG, t } from './i18n/strings.js';
import { SpeechProvider } from './speech/SpeechProvider.jsx';
import './components/components.css';
import './screens/screens.css';

// The kiosk's own name, as it appears in index.html and the web manifest.
const PRODUCT = 'MediKiosk';
// Matches Idle.jsx and Starting.jsx. This kiosk belongs to the hospital it
// stands in, and the landing page is the first place that is said.
const HOSPITAL = 'District Government Hospital';

function usePathname() {
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname);
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);
  const navigate = (next) => {
    window.history.pushState({}, '', next);
    setPath(window.location.pathname);
  };
  return [path, navigate];
}

function RoleSelection({ onChoosePatient, onChooseDoctor }) {
  return (
    <main className="role-select">
      <section className="role-select__intro" aria-labelledby="role-title">
        <p className="role-select__eyebrow">{PRODUCT}</p>
        {/* The attribution the idle screen carries, read from the same i18n
            entry rather than repeated as a literal. */}
        <h1 id="role-title">{t(DEFAULT_LANG, 'idle.subtitle').label}</h1>
        <p className="role-select__hospital">{HOSPITAL}</p>
        <p className="role-select__copy">
          Start a guided patient assessment or sign in to review clinical cases.
        </p>
      </section>

      <div className="role-select__choices">
        <button type="button" className="role-card" onClick={onChoosePatient}>
          <span className="role-card__icon">
            <Person size={48} />
          </span>
          <span className="role-card__title">Patient</span>
          <span className="role-card__text">
            Start your health assessment in your preferred language.
          </span>
          <span className="role-card__action">Continue</span>
        </button>

        <button type="button" className="role-card" onClick={onChooseDoctor}>
          <span className="role-card__icon">
            <Document size={48} />
          </span>
          <span className="role-card__title">Doctor</span>
          <span className="role-card__text">
            Sign in to review patient summaries and clinical cases.
          </span>
          <span className="role-card__action">Doctor Login</span>
        </button>
      </div>

      <p className="role-select__trust">Secure · Private · Clinician reviewed</p>
    </main>
  );
}

export default function App() {
  const [path, navigate] = usePathname();

  // The badge wraps BOTH destinations: the physician console is replayed too,
  // and a recorded queue must not be mistaken for live patients either.
  // EVERY /physician route is behind the gate, including /physician/login
  // itself — ProtectedRoute renders the login form when there is no session,
  // so there is no path into the console that skips it.
  if (path.startsWith('/physician') || path.startsWith('/doctor')) {
    const isDoctorPath = path.startsWith('/doctor');
    return (
      <>
        <ReplayBadge />
        <ProtectedRoute onAuthenticated={isDoctorPath ? () => navigate('/doctor/dashboard') : undefined}>
          {({ auth, signOut }) => <Physician auth={auth} onSignOut={signOut} />}
        </ProtectedRoute>
      </>
    );
  }

  if (path !== '/patient') {
    return (
      <RoleSelection
        onChoosePatient={() => navigate('/patient')}
        onChooseDoctor={() => navigate('/doctor')}
      />
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

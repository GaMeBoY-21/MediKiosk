// Owner: Ranjith
// The patient flow. One screen at a time, driven by SessionContext.

import { useCallback, useEffect, useRef, useState } from 'react';
import { SCREENS, useSession } from './state/SessionContext.jsx';
import { useIdleTimeout } from './hooks/useIdleTimeout.js';
import IdleTimeoutOverlay from './components/IdleTimeoutOverlay.jsx';
import ErrorScreen from './screens/ErrorScreen.jsx';

import Idle from './screens/Idle.jsx';
import Language from './screens/Language.jsx';
import Identify from './screens/Identify.jsx';
import NumberEntry from './screens/NumberEntry.jsx';
import NameEntry from './screens/NameEntry.jsx';
import AgeEntry from './screens/AgeEntry.jsx';
import SexEntry from './screens/SexEntry.jsx';
import Consent from './screens/Consent.jsx';
import ConsentChoices from './screens/ConsentChoices.jsx';
import ConsentDeclined from './screens/ConsentDeclined.jsx';
import ChiefComplaint from './screens/ChiefComplaint.jsx';
import Interview from './screens/Interview.jsx';
import Documents from './screens/Documents.jsx';
import Confirm from './screens/Confirm.jsx';
import Done from './screens/Done.jsx';
import Emergency from './screens/Emergency.jsx';

import { startSession } from './api/client.js';

export default function Kiosk() {
  const { screen, sessionId, setSessionId, language, reset } = useSession();
  const [failed, setFailed] = useState(false);

  // Open a session as soon as the patient leaves the idle screen.
  // The ref guards against StrictMode's double effect invocation in dev.
  const starting = useRef(false);
  useEffect(() => {
    if (screen === SCREENS.IDLE || sessionId || starting.current) return;
    starting.current = true;
    startSession()
      .then((s) => setSessionId(s.session_id))
      .catch((e) => {
        console.error('[kiosk] could not start session:', e);
        setFailed(true);
      });
  }, [screen, sessionId, setSessionId]);

  const wipe = useCallback(() => {
    starting.current = false;
    setFailed(false);
    reset();
  }, [reset]);

  // The timeout is meaningless on Idle (nothing to protect) and on Done
  // (which runs its own 30s return).
  const timeoutEnabled = screen !== SCREENS.IDLE && screen !== SCREENS.DONE;
  const { warning, secondsLeft, stayActive } = useIdleTimeout({
    enabled: timeoutEnabled,
    onTimeout: wipe,
  });

  if (failed) return <ErrorScreen lang={language} onRestart={wipe} />;

  const screens = {
    [SCREENS.IDLE]: <Idle />,
    [SCREENS.LANGUAGE]: <Language />,
    [SCREENS.IDENTIFY]: <Identify />,
    [SCREENS.ABHA]: <NumberEntry kind="abha" />,
    [SCREENS.AADHAAR]: <NumberEntry kind="aadhaar" />,
    [SCREENS.NAME]: <NameEntry />,
    [SCREENS.AGE]: <AgeEntry />,
    [SCREENS.SEX]: <SexEntry />,
    [SCREENS.CONSENT]: <Consent />,
    [SCREENS.CONSENT_CHOICES]: <ConsentChoices />,
    [SCREENS.CONSENT_DECLINED]: <ConsentDeclined />,
    [SCREENS.COMPLAINT]: <ChiefComplaint />,
    [SCREENS.INTERVIEW]: <Interview onError={() => setFailed(true)} />,
    [SCREENS.DOCUMENTS]: <Documents />,
    [SCREENS.CONFIRM]: <Confirm />,
    [SCREENS.DONE]: <Done />,
    [SCREENS.EMERGENCY]: <Emergency />,
  };

  return (
    <>
      {screens[screen] ?? <Idle />}
      {warning ? <IdleTimeoutOverlay secondsLeft={secondsLeft} onStay={stayActive} /> : null}
    </>
  );
}

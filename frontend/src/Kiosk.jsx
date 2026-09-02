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
import ConsentDeclined from './screens/ConsentDeclined.jsx';
import ChiefComplaint from './screens/ChiefComplaint.jsx';
import Interview from './screens/Interview.jsx';
import Documents from './screens/Documents.jsx';
import Confirm from './screens/Confirm.jsx';
import Done from './screens/Done.jsx';
import Emergency from './screens/Emergency.jsx';

import { startSession, subscribeReplay } from './api/client.js';

export default function Kiosk() {
  const { screen, sessionId, setSessionId, language, languageChosen, reset } = useSession();
  const [failed, setFailed] = useState(false);

  // Open the session once the patient has CHOSEN a language, not merely left
  // the idle screen. Starting it on the language screen itself meant the
  // session was created before a language existed, so the backend stored
  // English and generated its opening question in English.
  const starting = useRef(false);
  useEffect(() => {
    if (screen === SCREENS.IDLE || screen === SCREENS.LANGUAGE) return;
    if (!languageChosen || sessionId || starting.current) return;
    starting.current = true;
    startSession(language)
      .then((s) => setSessionId(s.session_id))
      .catch((e) => {
        console.error('[kiosk] could not start session:', e);
        setFailed(true);
      });
  }, [screen, sessionId, setSessionId, language, languageChosen]);

  const wipe = useCallback(() => {
    starting.current = false;
    setFailed(false);
    reset();
  }, [reset]);

  // The Ctrl+Shift+R failure switch. Clearing the session is not enough on its
  // own: `failed` lives here, so without this the kiosk switched to the
  // recording and carried on showing "Something went wrong" — which is the one
  // screen you press the switch to get away from.
  useEffect(() => subscribeReplay(() => wipe()), [wipe]);

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

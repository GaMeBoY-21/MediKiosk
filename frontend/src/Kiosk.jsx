// Owner: Ranjith
// The patient flow. One screen at a time, driven by SessionContext.

import { useCallback, useEffect, useState } from 'react';
import { SCREENS, SESSION_STATUS, useSession } from './state/SessionContext.jsx';
import { useIdleTimeout } from './hooks/useIdleTimeout.js';
import IdleTimeoutOverlay from './components/IdleTimeoutOverlay.jsx';
import ErrorScreen from './screens/ErrorScreen.jsx';
import Starting from './screens/Starting.jsx';

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

import { subscribeReplay } from './api/client.js';

// Screens that address the session by id. Not one of them may be mounted
// before the id exists: they call the API from an effect or from the first tap,
// so "rendered early" and "requested `/api/session/null/...`" are the same
// event. The identity screens above them are the kiosk's own and touch no
// session endpoint, which is what gives the start call time to land.
const NEEDS_SESSION = new Set([
  SCREENS.CONSENT,
  SCREENS.INTERVIEW,
  SCREENS.DOCUMENTS,
  SCREENS.CONFIRM,
  SCREENS.DONE,
]);

export default function Kiosk() {
  const { screen, sessionId, sessionStatus, beginSession, language, languageChosen, reset } =
    useSession();
  const [failed, setFailed] = useState(false);

  // Open the session once the patient has CHOSEN a language, not merely left
  // the idle screen. Starting it on the language screen itself meant the
  // session was created before a language existed, so the backend stored
  // English and generated its opening question in English.
  //
  // Still kicked off here rather than awaited inline, so the patient can carry
  // on typing their name while the model composes the opening question — but
  // the gate below is what makes that safe, and no screen that needs the id
  // renders until beginSession has actually produced one.
  useEffect(() => {
    if (screen === SCREENS.IDLE || screen === SCREENS.LANGUAGE) return;
    if (!languageChosen || sessionStatus !== SESSION_STATUS.IDLE) return;
    beginSession(language).catch((e) => console.error('[kiosk] could not start session:', e));
  }, [screen, sessionStatus, beginSession, language, languageChosen]);

  const wipe = useCallback(() => {
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

  // A session that could not be opened is a dead kiosk, not a slow one: there
  // is no id coming, so say so instead of holding the patient on a spinner.
  if (failed || sessionStatus === SESSION_STATUS.FAILED) {
    return <ErrorScreen lang={language} onRestart={wipe} />;
  }

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

  // The gate, and the whole fix: a screen that addresses the session by id is
  // not merely stopped from sending, it is not mounted to send from. It stands
  // in for that screen rather than replacing the render, so the idle timeout
  // still gets to warn a patient who walked off mid-wait.
  const gated = NEEDS_SESSION.has(screen) && !sessionId;

  return (
    <>
      {gated ? <Starting lang={language} /> : screens[screen] ?? <Idle />}
      {warning ? <IdleTimeoutOverlay secondsLeft={secondsLeft} onStay={stayActive} /> : null}
    </>
  );
}

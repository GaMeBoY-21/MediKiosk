// Owner: Ranjith
// Clinician tokens, held in memory and nowhere else.
//
// NOT localStorage, NOT sessionStorage, NOT a cookie readable by script. Both
// are readable by any injected script, and this console shows PHI for every
// patient in the queue — one XSS anywhere on the origin would hand over a
// token good for the whole clinic.
//
// The cost is honest and accepted: a page refresh logs the doctor out. On a
// console that auto-logs-out after ten idle minutes anyway, re-entering a
// password after a refresh is the cheaper half of the trade.

let state = {
  access: null,
  refresh: null,
  role: null,
  name: null,
  username: null,
};

const listeners = new Set();

function emit() {
  for (const fn of listeners) fn(snapshot());
}

export function snapshot() {
  // Never expose the raw tokens to render code — only whether we have one.
  return {
    authenticated: Boolean(state.access),
    role: state.role,
    name: state.name,
    username: state.username,
  };
}

export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

/** The access token, for the API layer only. */
export function accessToken() {
  return state.access;
}

export function refreshToken() {
  return state.refresh;
}

export function setSession({ access, refresh, role, name, username }) {
  state = {
    access: access ?? state.access,
    refresh: refresh ?? state.refresh,
    role: role ?? state.role,
    name: name ?? state.name,
    username: username ?? state.username,
  };
  emit();
}

export function clearSession() {
  state = { access: null, refresh: null, role: null, name: null, username: null };
  emit();
}

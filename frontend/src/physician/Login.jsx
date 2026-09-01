// Owner: Ranjith
// /physician/login. The only screen in this app that takes a password.
//
// Deliberately plain: no "forgot password", no account creation, no hint about
// whether a username exists. The server returns one message for every failure
// mode and this screen shows exactly that, adding nothing.

import { useState } from 'react';
import { login } from '../api/client.js';

export default function Login({ onSignedIn }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError('');
    try {
      await login(username.trim(), password);
      // Clear the password from component state the moment it is spent. It
      // still lived in memory; no reason to keep it there any longer.
      setPassword('');
      onSignedIn?.();
    } catch (err) {
      setError(err.message || 'Invalid username or password.');
      setPassword('');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login">
      <form className="login__card" onSubmit={submit}>
        <h1 className="login__title">MediKiosk — clinician sign in</h1>
        <p className="login__sub">This console shows patient data. Sign in to continue.</p>

        <label className="login__label" htmlFor="username">
          Username
        </label>
        <input
          id="username"
          className="login__input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          autoFocus
          required
        />

        <label className="login__label" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          className="login__input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />

        {/* role="alert" so a screen reader announces the failure rather than
            leaving the user waiting on a silent form. */}
        {error ? (
          <p className="login__error" role="alert">
            {error}
          </p>
        ) : null}

        <button type="submit" className="login__submit" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  );
}

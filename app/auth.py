# Owner: Tharun
"""Clinician authentication: password hashing, tokens, rate limiting.

The kiosk side is deliberately anonymous — a patient never logs in. This
protects the other side: the physician console shows PHI for every patient in
the queue, so it is the one surface where real authentication matters.

Design notes worth keeping:

  - Passwords are hashed with bcrypt and never stored, logged or returned. The
    hash never leaves this module.
  - Login always costs a bcrypt verification, even for an unknown username,
    so response time cannot be used to enumerate accounts.
  - The error text for "no such user" and "wrong password" is byte-identical,
    for the same reason.
  - Access tokens are short (15 min) because they live in browser memory and
    are replayable if captured. Refresh tokens last a clinic session (8 hours)
    and are revocable, which access tokens are not.
  - Refresh tokens carry a jti we track, so logout genuinely invalidates rather
    than relying on the client to forget.
"""

from __future__ import annotations

import hmac
import logging
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import bcrypt
import jwt

from app.config import settings

log = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(hours=8)

ROLES = ("doctor", "triage", "admin")

# Deliberately identical for every failure mode. A different message for
# "unknown user" would turn this endpoint into a directory of who works here.
GENERIC_LOGIN_ERROR = "Invalid username or password."

# Login rate limit, per username AND per client address.
MAX_ATTEMPTS = 5
LOCKOUT_WINDOW = timedelta(minutes=15)


class AuthError(Exception):
    """Authentication failed. Carries no detail the caller should show a user."""


class RateLimited(AuthError):
    """Too many failed attempts for this username or address."""


# --------------------------------------------------------------- passwords


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


# A real hash of a random string. Verified against when the username does not
# exist, so an unknown user costs the same ~100ms as a known one and cannot be
# distinguished by timing.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(32))


# ------------------------------------------------------------------ users


@dataclass
class User:
    username: str
    password_hash: str
    role: str
    name: str

    def public(self) -> dict:
        """Everything safe to send to a client. Never the hash."""
        return {"username": self.username, "role": self.role, "name": self.name}


class UserStore:
    """In-process user directory, seeded from the environment.

    One account is enough for the demo and keeps credentials out of the
    database and out of git. A real deployment replaces this with a table and
    an admin flow; the interface is small on purpose so that swap is contained.
    """

    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
        self._lock = threading.RLock()

    def seed_from_settings(self) -> None:
        username = (settings.CLINICIAN_USERNAME or "").strip()
        password = settings.CLINICIAN_PASSWORD or ""
        if not username or not password:
            log.warning(
                "no clinician account seeded: set CLINICIAN_USERNAME and "
                "CLINICIAN_PASSWORD in app/.env. The physician console will "
                "refuse every login until you do."
            )
            return
        role = (settings.CLINICIAN_ROLE or "doctor").strip().lower()
        if role not in ROLES:
            log.warning("unknown role %r for %s, defaulting to doctor", role, username)
            role = "doctor"
        with self._lock:
            self._users[username.lower()] = User(
                username=username,
                password_hash=hash_password(password),
                role=role,
                name=settings.CLINICIAN_NAME or username,
            )
        # Never log the password, and never log the hash.
        log.info("seeded clinician account %r with role %r", username, role)

    def get(self, username: str) -> Optional[User]:
        with self._lock:
            return self._users.get((username or "").strip().lower())

    def __len__(self) -> int:
        with self._lock:
            return len(self._users)


users = UserStore()


# ------------------------------------------------------------ rate limiting


@dataclass
class _Bucket:
    failures: int = 0
    first_failure: float = field(default_factory=time.time)


class LoginThrottle:
    """Counts failed logins per key within a rolling window.

    Keyed on both the username and the caller's address, so one attacker
    cannot lock every clinician out by failing against their usernames, and a
    single address cannot spray many usernames either.
    """

    def __init__(self) -> None:
        self._buckets: Dict[str, _Bucket] = {}
        self._lock = threading.RLock()

    def _fresh(self, bucket: _Bucket) -> bool:
        return (time.time() - bucket.first_failure) < LOCKOUT_WINDOW.total_seconds()

    def check(self, *keys: str) -> None:
        with self._lock:
            for key in keys:
                bucket = self._buckets.get(key)
                if bucket and self._fresh(bucket) and bucket.failures >= MAX_ATTEMPTS:
                    raise RateLimited(GENERIC_LOGIN_ERROR)

    def record_failure(self, *keys: str) -> None:
        with self._lock:
            for key in keys:
                bucket = self._buckets.get(key)
                if bucket is None or not self._fresh(bucket):
                    self._buckets[key] = _Bucket(failures=1)
                else:
                    bucket.failures += 1

    def clear(self, *keys: str) -> None:
        with self._lock:
            for key in keys:
                self._buckets.pop(key, None)


throttle = LoginThrottle()


# ----------------------------------------------------------------- tokens

# Refresh token ids that are still valid. Logout removes one, which is the
# whole reason refresh tokens are tracked server-side: an access token cannot
# be withdrawn once issued, so the revocable half has to be the long-lived one.
_active_refresh: Dict[str, str] = {}  # jti -> username
_refresh_lock = threading.RLock()


def _secret() -> str:
    secret = settings.AUTH_SECRET
    if not secret:
        # Fail loudly rather than fall back to a constant. A predictable
        # signing key means anyone can mint a doctor token.
        raise AuthError(
            "AUTH_SECRET is not set. Generate one with "
            "`python3 -c 'import secrets; print(secrets.token_urlsafe(48))'` "
            "and put it in app/.env."
        )
    return secret


def _encode(payload: dict, ttl: timedelta, kind: str) -> str:
    now = datetime.now(timezone.utc)
    # `iat`/`exp` are whole seconds, so two tokens minted in the same second
    # for the same user were byte-identical — refreshing immediately after
    # login handed back the original token, with the original expiry, and
    # silently failed to extend the session. A per-token id keeps every token
    # distinct and individually traceable in logs.
    body = {**payload, "kind": kind, "iat": now, "exp": now + ttl}
    body.setdefault("jti", uuid.uuid4().hex)
    return jwt.encode(body, _secret(), algorithm=ALGORITHM)


def issue_tokens(user: User) -> dict:
    jti = uuid.uuid4().hex
    with _refresh_lock:
        _active_refresh[jti] = user.username
    return {
        "access": _encode({"sub": user.username, "role": user.role}, ACCESS_TTL, "access"),
        "refresh": _encode({"sub": user.username, "jti": jti}, REFRESH_TTL, "refresh"),
        "role": user.role,
        "name": user.name,
        "expires_in": int(ACCESS_TTL.total_seconds()),
    }


def decode(token: str, *, kind: str) -> dict:
    """Decode and validate a token, or raise AuthError.

    `kind` is checked explicitly: a refresh token must never be accepted where
    an access token is required, or the 15-minute access window is meaningless.
    """
    try:
        claims = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Session expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Not authenticated.") from exc
    if claims.get("kind") != kind:
        raise AuthError("Not authenticated.")
    return claims


def authenticate(username: str, password: str, client: str) -> User:
    """Verify credentials. Raises AuthError with generic text on any failure."""
    keys = (f"user:{(username or '').strip().lower()}", f"addr:{client}")
    throttle.check(*keys)

    user = users.get(username)
    # Always run a real verification, even with no such user, so the timing of
    # a wrong username matches the timing of a wrong password.
    reference = user.password_hash if user else _DUMMY_HASH
    ok = verify_password(password or "", reference)

    if not user or not ok:
        throttle.record_failure(*keys)
        raise AuthError(GENERIC_LOGIN_ERROR)

    throttle.clear(*keys)
    return user


def refresh_access(refresh_token: str) -> dict:
    claims = decode(refresh_token, kind="refresh")
    jti = claims.get("jti", "")
    with _refresh_lock:
        owner = _active_refresh.get(jti)
    # Revoked (logged out) or never issued by us.
    if not owner or not hmac.compare_digest(owner, claims.get("sub", "")):
        raise AuthError("Not authenticated.")
    user = users.get(owner)
    if user is None:
        raise AuthError("Not authenticated.")
    return {
        "access": _encode({"sub": user.username, "role": user.role}, ACCESS_TTL, "access"),
        "role": user.role,
        "name": user.name,
        "expires_in": int(ACCESS_TTL.total_seconds()),
    }


def revoke(refresh_token: str) -> bool:
    """Invalidate a refresh token. Idempotent, and never reveals whether the
    token was real — logout must not become an oracle either."""
    try:
        claims = decode(refresh_token, kind="refresh")
    except AuthError:
        return False
    with _refresh_lock:
        return _active_refresh.pop(claims.get("jti", ""), None) is not None

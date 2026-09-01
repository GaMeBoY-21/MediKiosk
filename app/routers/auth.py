# Owner: Tharun
"""Clinician auth endpoints, and the dependency that guards PHI routes.

`require_clinician` is the only thing standing between the internet and every
patient in the queue, so it is deliberately small and has no fallback: no
token, a bad token, an expired token and a refresh-token-used-as-access all
end the same way, with a 401 and nothing else disclosed.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from app import auth, models
from app.database import get_db
from app.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

UNAUTHORIZED = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated.",
    headers={"WWW-Authenticate": "Bearer"},
)


def require_clinician(authorization: str | None = Header(default=None)) -> dict:
    """FastAPI dependency: a valid access token, or 401.

    Returns the token claims, so a route can check `role` when it needs to.
    Attach this to every route that reads or writes patient data.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UNAUTHORIZED
    token = authorization.split(" ", 1)[1].strip()
    try:
        return auth.decode(token, kind="access")
    except auth.AuthError:
        # Never echo the underlying reason: "expired" vs "malformed" tells an
        # attacker which half of their guess was right.
        raise UNAUTHORIZED from None


def _client(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: DbSession = Depends(get_db)):
    """Exchange credentials for an access and refresh token.

    Rate limited per username and per address. Every failure returns the same
    text so this cannot be used to discover who has an account.
    """
    client = _client(request)
    try:
        user = auth.authenticate(payload.username, payload.password, client)
    except auth.RateLimited:
        models.write_audit(
            db,
            action="auth.login.throttled",
            actor=payload.username or "unknown",
            detail={"client": client},
        )
        db.commit()
        log.warning("login throttled for %r from %s", payload.username, client)
        # 429 is honest about why, without revealing whether the account exists.
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, detail=auth.GENERIC_LOGIN_ERROR
        ) from None
    except auth.AuthError:
        models.write_audit(
            db,
            action="auth.login.failed",
            actor=payload.username or "unknown",
            detail={"client": client},
        )
        db.commit()
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail=auth.GENERIC_LOGIN_ERROR
        ) from None

    tokens = auth.issue_tokens(user)
    models.write_audit(
        db, action="auth.login", actor=user.username, detail={"client": client, "role": user.role}
    )
    db.commit()
    log.info("clinician %r logged in from %s", user.username, client)
    return LoginResponse(**tokens)


@router.post("/refresh", response_model=RefreshResponse)
def refresh(payload: RefreshRequest):
    """Trade a valid refresh token for a new access token."""
    try:
        return RefreshResponse(**auth.refresh_access(payload.refresh))
    except auth.AuthError:
        raise UNAUTHORIZED from None


@router.post("/logout", response_model=LogoutResponse)
def logout(payload: RefreshRequest, db: DbSession = Depends(get_db)):
    """Invalidate a refresh token server-side.

    Always reports ok, whether or not the token was real: a truthful "that was
    not a valid token" would let someone test tokens against this endpoint.
    """
    revoked = auth.revoke(payload.refresh)
    if revoked:
        models.write_audit(db, action="auth.logout", actor="clinician")
        db.commit()
    return LogoutResponse(ok=True)


@router.get("/me", response_model=MeResponse)
def me(claims: dict = Depends(require_clinician)):
    """Who the current access token belongs to. Used by the console on load."""
    user = auth.users.get(claims.get("sub", ""))
    if user is None:
        raise UNAUTHORIZED
    return MeResponse(**user.public())

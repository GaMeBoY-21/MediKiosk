# Owner: Tharun
"""FastAPI application entrypoint.

Every route lives under /api. The frontend needs no code change for this — it
builds URLs as VITE_API_BASE + path, so setting

    VITE_API_BASE=http://localhost:8000/api

makes client.js hit the right place as written.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.auth import users as auth_users
from app.database import init_db
from app.routers import auth, documents, identity, interview, physician, session, summary

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

API_PREFIX = "/api"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    # Hash the demo clinician's password once, at startup.
    auth_users.seed_from_settings()
    log.info("MediKiosk API up | env=%s | sqlite_fallback=%s", settings.APP_ENV, settings.using_sqlite)
    yield


app = FastAPI(
    title="MediKiosk API",
    version="0.1.0",
    description="Voice-first OPD intake. Backend for SIH PS 26047.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth.router,
    session.router,
    interview.router,
    documents.router,
    summary.router,
    physician.router,
    identity.router,
):
    app.include_router(router, prefix=API_PREFIX)


@app.get("/health", tags=["health"])
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


@app.get(f"{API_PREFIX}/health", tags=["health"])
def health_api() -> dict:
    """Same probe under /api, so a frontend pointed at the prefix can reach it."""
    return {"status": "ok"}


@app.get(f"{API_PREFIX}/health/providers", tags=["health"])
def health_providers() -> dict:
    """Which model/key combinations exist, which are spent, which is in use.

    For watching the pool during a demo: how much headroom is left, and which
    combination answered the question just now. Contains NO key material —
    combinations are identified by index ("key 3 of 5"), because this is the
    kind of endpoint someone opens on a projector.
    """
    from ai.adapters.base import MissingConfigError
    from ai.adapters.gemini import get_pool

    try:
        return {"configured": True, **get_pool().status()}
    except MissingConfigError as exc:
        # Not an error state worth a 500: it is the answer to the question.
        return {
            "configured": False,
            "detail": str(exc),
            "keys_configured": 0,
            "pools_total": 0,
            "pools_exhausted": 0,
            "pools_remaining": 0,
            "active": None,
            "combinations": [],
        }

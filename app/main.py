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
from app.database import init_db
from app.routers import documents, identity, interview, physician, session, summary

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

API_PREFIX = "/api"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
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

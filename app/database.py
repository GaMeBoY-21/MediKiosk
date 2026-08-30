# Owner: Tharun
"""SQLAlchemy engine, session factory and the FastAPI dependency.

Falls back to SQLite when DATABASE_URL is unset so the demo runs without
Postgres. SQLite is refused in production — losing an OPD's records to a stray
file delete is not an acceptable failure mode.
"""

from __future__ import annotations

import logging
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

log = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Declarative base for every ORM table."""


def _engine_kwargs() -> dict:
    if settings.using_sqlite:
        # check_same_thread=False: FastAPI serves requests on a threadpool.
        return {"connect_args": {"check_same_thread": False}}
    # pool_pre_ping survives Postgres closing idle connections overnight.
    return {"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10}


if settings.using_sqlite:
    if settings.is_production:
        raise RuntimeError(
            "DATABASE_URL is unset but APP_ENV=production. "
            "Refusing to run an OPD on the SQLite fallback."
        )
    log.warning("DATABASE_URL unset - using SQLite fallback at %s", settings.database_url)

engine = create_engine(settings.database_url, future=True, **_engine_kwargs())

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


if settings.using_sqlite:

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):
        """SQLite ignores foreign keys unless asked, and defaults to a fragile journal."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables and the audit-log immutability triggers.

    Imported for side effects: app.models must be loaded before create_all so
    the metadata is populated.
    """
    from app import models  # noqa: F401  (registers tables on Base.metadata)

    Base.metadata.create_all(bind=engine)

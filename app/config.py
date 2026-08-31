# Owner: Tharun
"""Environment-based settings, read once at import.

DATABASE_URL is optional on purpose: with it unset the app falls back to a local
SQLite file so the kiosk demo runs on a laptop with no Postgres installed.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Where the SQLite fallback lives, relative to the repo root.
SQLITE_FALLBACK = "sqlite:///./medikiosk.db"

# Anchored to THIS FILE, not the working directory. A bare env_file=".env" is
# resolved against wherever uvicorn happened to be started, so running from the
# repo root silently missed app/.env and every Gemini call died on a missing
# key. Both locations are read, app/.env last so it wins.
_APP_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _APP_DIR.parent
ENV_FILES = (_REPO_ROOT / ".env", _APP_DIR / ".env")


class Settings(BaseSettings):
    """Runtime configuration. Values come from the environment or a .env file."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    DATABASE_URL: Optional[str] = None
    """Postgres DSN. Unset falls back to SQLite so the demo runs anywhere."""

    GEMINI_API_KEY: Optional[str] = None
    """Key for the AI layer. Unset now fails loudly on first use by name."""

    GEMINI_MODEL: Optional[str] = None
    """Gemini model id, e.g. gemini-3.5-flash-lite.

    Deliberately no default: Google retires model names without notice, and a
    stale default here took the whole app down with 404s. Unset raises
    MissingConfigError naming this variable.
    """

    APP_ENV: str = "development"
    """development | production. Production refuses to start on SQLite."""

    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    """Origins allowed to call the API. Vite dev server and CRA dev server."""

    SESSION_TTL_SECONDS: int = 3600
    """How long an abandoned session lingers in memory before purge."""

    @property
    def database_url(self) -> str:
        """Effective DSN, with the SQLite fallback applied."""
        return self.DATABASE_URL or SQLITE_FALLBACK

    @property
    def using_sqlite(self) -> bool:
        """True when running on the fallback database."""
        return self.database_url.startswith("sqlite")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton. Import this, not Settings()."""
    return Settings()


settings = get_settings()

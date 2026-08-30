# Owner: Tharun
"""Environment-based application settings."""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables.

    TODO: replace with a pydantic BaseSettings model.
    """

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    APP_ENV: str = os.getenv("APP_ENV", "development")


settings = Settings()

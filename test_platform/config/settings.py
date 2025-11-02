"""Application settings using Pydantic Settings.

Supports environment-based configuration, type validation, and secure defaults.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, HttpUrl, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env as early as possible
load_dotenv(override=False)

EnvironmentType = Literal["development", "staging", "production"]


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Environment variables take precedence over defaults. Uses python-dotenv to
    load variables from a .env file in development.
    """

    # General
    environment: EnvironmentType = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")

    # Security
    secret_key: str = Field(min_length=16, alias="SECRET_KEY")
    admin_password: str = Field(default="afnanpathan123", alias="ADMIN_PASSWORD")

    # Database
    database_url: str = Field(alias="DATABASE_URL")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    # AI Providers
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL")

    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    # Streamlit logger level (optional)
    streamlit_logger_level: str = Field(default="info", alias="STREAMLIT_LOGGER_LEVEL")

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=None,  # dotenv already loaded
        env_ignore_empty=True,
        validate_assignment=True,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_staging(self) -> bool:
        return self.environment == "staging"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache settings. Raises with clear errors if invalid."""
    try:
        return Settings()
    except ValidationError as exc:
        # Re-raise with a concise message suitable for UI logs
        raise RuntimeError(f"Invalid application settings: {exc}")


# Singleton-like settings object for convenient import
settings: Settings = get_settings()

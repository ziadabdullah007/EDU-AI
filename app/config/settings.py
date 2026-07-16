"""
EduCore AI Platform — Application Configuration

Manages all environment-based configuration using pydantic-settings.
All secrets and environment-specific values are loaded from environment
variables, never hardcoded.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration model for the EduCore AI Platform.

    All values are loaded from environment variables or a .env file.
    This class is the single source of truth for application configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----------------------------- Application --------------------------------
    app_name: str = Field(default="EduCore AI Platform")
    app_version: str = Field(default="1.0.0")
    app_env: Literal["development", "staging", "production"] = Field(default="development")
    debug: bool = Field(default=False)

    # ----------------------------- Server ------------------------------------
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # ----------------------------- Database ----------------------------------
    database_url: str = Field(
        description="PostgreSQL connection URL (asyncpg dialect required)"
    )
    database_pool_size: int = Field(default=10, ge=1, le=50)
    database_max_overflow: int = Field(default=20, ge=0, le=100)
    database_pool_timeout: int = Field(default=30, ge=5)

    # ----------------------------- JWT ---------------------------------------
    jwt_secret_key: str = Field(description="Secret key for signing access tokens")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1)
    jwt_refresh_secret_key: str = Field(description="Secret key for signing refresh tokens")
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1)

    # ----------------------------- CORS --------------------------------------
    cors_origins: str = Field(default="http://localhost:3000")
    cors_allow_credentials: bool = Field(default=True)

    # ----------------------------- Security ----------------------------------
    bcrypt_rounds: int = Field(default=12, ge=10, le=16)

    # ----------------------------- Logging -----------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    log_format: Literal["json", "text"] = Field(default="json")

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure the database URL uses the asyncpg driver."""
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the asyncpg dialect: "
                "postgresql+asyncpg://user:password@host:port/database"
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string to list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if the application is running in production mode."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if the application is running in development mode."""
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings instance.

    Uses lru_cache to ensure only one Settings instance is created
    across the entire application lifecycle.
    """
    return Settings()  # type: ignore[call-arg]

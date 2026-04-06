import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    debug: bool = True
    app_secret_key: str = "CHANGE_ME_super_secret_key"
    allowed_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    # JWT
    jwt_secret_key: str = "CHANGE_ME_jwt_secret_key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def database_url_sync(self) -> str:
        """Sync database URL for Alembic (replaces async prefix)."""
        return self.database_url.replace("+aiosqlite", "").replace("+asyncpg", "")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

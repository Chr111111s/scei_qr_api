from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables / .env."""

    database_url: str = "postgresql+asyncpg://scei:scei_dev@localhost:5432/scei_qr"
    direct_url: str | None = None

    jwt_secret: str = "dev-secret-cambiar-en-produccion-32-bytes-minimo"
    jwt_expiration: str = "8h"

    port: int = 3000
    cors_origin: str = "*"

    storage_driver: str = "local"
    upload_dir: str = "uploads"

    firebase_service_account: str | None = None
    seed_on_start: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origin.split(",") if origin.strip()]

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

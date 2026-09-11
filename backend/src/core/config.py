"""Конфигурация приложения.

Единственное место, где читается окружение. Все значения проверяются при старте:
отсутствующая переменная — это падение с внятным сообщением, а не строка подключения
с литералом ``None`` внутри (A6) и не молча проигнорированный ``CELERY_BROKER_URL`` (A3).
"""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "backend-db"
    # PGPORT задаёт порт самого Postgres (см. И6) — читаем оба имени, чтобы переезд
    # на POSTGRES_PORT не требовал одновременной правки окружения.
    postgres_port: int = Field(
        default=5432,
        validation_alias=AliasChoices("POSTGRES_PORT", "PGPORT"),
    )

    celery_broker_url: str = Field(
        default="redis://backend-redis:6379/0",
        validation_alias=AliasChoices("CELERY_BROKER_URL", "REDIS_URL"),
    )
    celery_result_backend: str | None = None

    storage_dir: Path = BASE_DIR / "storage" / "files"
    # Больше этого не принимаем вовсе (A10); порог «подозрительного» размера — отдельно,
    # он часть правил детекта, а не транспорта.
    max_upload_size: int = 100 * 1024 * 1024
    suspicious_size: int = 10 * 1024 * 1024

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    log_level: str = "INFO"

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.celery_broker_url


@lru_cache
def get_settings() -> Settings:
    return Settings()

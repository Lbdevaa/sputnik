"""Общая обвязка интеграционных тестов.

База — SQLite в файле во временном каталоге, хранилище — тот же временный каталог.
Postgres и Redis не нужны: сервис получает сессию и хранилище снаружи (Б2, Б4), поэтому
подменить их в тесте — вопрос двух фикстур, а не поднятого докера.

Что при этом не проверяется и остаётся на smoke-прогоне (scripts/smoke.sh): особенности
Postgres (типы, каскад на уровне СУБД в бою) и доставка через Celery.
"""

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import Settings
from src.models import Base
from src.services import FileService
from src.storage import LocalFileStorage

MAX_UPLOAD = 128
SUSPICIOUS = 100

SAMPLE_TXT = b"line one\nline two\nline three\n"
SAMPLE_EXE = b"MZ\x90\x00fake exe\n"
TWO_PAGES_PDF = b"%PDF-1.4\n<< /Type/Page >>\n<< /Type /Page >>\n%%EOF\n"


async def stream(data: bytes, chunk_size: int = 5) -> AsyncIterator[bytes]:
    for start in range(0, len(data), chunk_size):
        yield data[start : start + chunk_size]


@pytest.fixture
async def engine(tmp_path: Path) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(connection, _record):
        # В SQLite внешние ключи по умолчанию выключены, а нам нужен ON DELETE CASCADE (A1).
        connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def session(session_maker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_maker() as session:
        yield session


@pytest.fixture
async def storage(tmp_path: Path) -> LocalFileStorage:
    instance = LocalFileStorage(tmp_path / "files")
    await instance.ensure_ready()
    return instance


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        postgres_user="test",
        postgres_password="test",
        postgres_db="test",
        storage_dir=tmp_path / "files",
        max_upload_size=MAX_UPLOAD,
        suspicious_size=SUSPICIOUS,
    )


@pytest.fixture
def service(session: AsyncSession, storage: LocalFileStorage, settings: Settings) -> FileService:
    return FileService(session=session, storage=storage, settings=settings)

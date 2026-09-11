"""Движок и сессии SQLAlchemy.

Движок создаётся лениво, а не на импорте модуля (Б3). Для веб-процесса разницы почти нет,
а для Celery она принципиальна: при создании на импорте пул asyncpg открывается в
родительском процессе **до** ``fork``, и дочерние процессы наследуют чужие сокеты (В3).
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    global _session_maker
    if _session_maker is None:
        _session_maker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_maker


async def dispose_engine() -> None:
    """Закрыть пул. Вызывается при остановке приложения и в дочернем процессе Celery."""
    global _engine, _session_maker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_maker = None


def reset_engine() -> None:
    """Забыть движок, не закрывая пул.

    Нужно после ``fork``: наследованные сокеты принадлежат родителю, закрывать их из
    дочернего процесса нельзя, а пользоваться — тем более.
    """
    global _engine, _session_maker
    _engine = None
    _session_maker = None


async def get_session() -> AsyncIterator[AsyncSession]:
    """Зависимость FastAPI: одна сессия на запрос."""
    async with get_session_maker()() as session:
        yield session

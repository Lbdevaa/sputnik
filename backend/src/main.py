"""Сборка приложения.

Здесь только композиция: настройки, логи, middleware, роутеры и обработчики ошибок.
Ни бизнес-логики, ни доступа к данным.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.errors import register_error_handlers
from src.api.v1 import router as v1_router
from src.core.config import get_settings
from src.core.db import dispose_engine
from src.core.logging import configure_logging
from src.storage import get_storage


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    # Каталог хранилища создаётся при старте, а не как побочный эффект импорта (Б3).
    await get_storage().ensure_ready()
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(title="File storage", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(v1_router)
    return app


app = create_app()

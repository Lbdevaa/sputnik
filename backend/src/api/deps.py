"""Зависимости FastAPI: что откуда берётся."""

from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.db import get_session
from src.schemas import DEFAULT_LIMIT, MAX_LIMIT, PageParams
from src.services import AlertService, FileService
from src.storage import FileStorage, get_storage

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def storage_dependency() -> FileStorage:
    return get_storage()


StorageDep = Annotated[FileStorage, Depends(storage_dependency)]


def file_service(session: SessionDep, storage: StorageDep, settings: SettingsDep) -> FileService:
    return FileService(session=session, storage=storage, settings=settings)


def alert_service(session: SessionDep) -> AlertService:
    return AlertService(session)


def page_params(
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PageParams:
    return PageParams(limit=limit, offset=offset)


FileServiceDep = Annotated[FileService, Depends(file_service)]
AlertServiceDep = Annotated[AlertService, Depends(alert_service)]
PageDep = Annotated[PageParams, Depends(page_params)]

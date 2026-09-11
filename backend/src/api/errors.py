"""Перевод доменных ошибок в коды ответов.

Единственное место во всём приложении, которое знает про HTTP-семантику ошибок. Сервисы
и домен бросают ошибки предметной области и про существование HTTP не подозревают (Б1).
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette import status
from starlette.requests import Request

from src.core.exceptions import (
    DomainError,
    EmptyFile,
    FileNotFound,
    FileTooLarge,
    StoredFileMissing,
)

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    FileNotFound: status.HTTP_404_NOT_FOUND,
    StoredFileMissing: status.HTTP_404_NOT_FOUND,
    EmptyFile: status.HTTP_400_BAD_REQUEST,
    FileTooLarge: status.HTTP_413_CONTENT_TOO_LARGE,
}

DETAIL_BY_ERROR: dict[type[DomainError], str] = {
    FileNotFound: "File not found",
    StoredFileMissing: "Stored file not found",
    EmptyFile: "File is empty",
}


async def handle_domain_error(_: Request, error: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=STATUS_BY_ERROR.get(type(error), status.HTTP_400_BAD_REQUEST),
        content={"detail": DETAIL_BY_ERROR.get(type(error), str(error))},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, handle_domain_error)

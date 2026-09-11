"""Страница результатов.

``GET /files`` и ``GET /alerts`` раньше отдавали таблицу целиком (Б7): на тысяче записей
это лишний трафик и seq scan с сортировкой, а клиент всё равно показывает экран за раз.
"""

from pydantic import BaseModel, Field

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class PageParams(BaseModel):
    limit: int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)
    offset: int = Field(default=0, ge=0)

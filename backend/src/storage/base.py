"""Контракт хранилища файлов.

Хранилище описано протоколом, а не классом с наследованием: реализации ничего не наследуют,
достаточно совпадения сигнатур. Локальный диск — одна из реализаций, а не устройство системы,
поэтому переезд на S3 — это новый класс, а не правка сервисов (Б4).

Все методы работают потоком: файл не обязан помещаться в память ни при записи, ни при чтении
(В2).
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SavedFile:
    """Результат сохранения: то, что известно только после того, как файл целиком записан."""

    stored_name: str
    size: int
    head: bytes


class StorageLimitExceeded(Exception):
    """Поток оказался длиннее разрешённого. Бросается посреди записи, файл не остаётся."""

    def __init__(self, limit: int) -> None:
        super().__init__(f"file exceeds limit of {limit} bytes")
        self.limit = limit


class FileStorage(Protocol):
    async def save(
        self,
        stored_name: str,
        chunks: AsyncIterator[bytes],
        max_size: int | None = None,
    ) -> SavedFile: ...

    def open(self, stored_name: str) -> AsyncIterator[bytes]: ...

    async def read_head(self, stored_name: str, size: int) -> bytes: ...

    async def delete(self, stored_name: str) -> None: ...

    async def exists(self, stored_name: str) -> bool: ...

    def path_for(self, stored_name: str) -> str: ...

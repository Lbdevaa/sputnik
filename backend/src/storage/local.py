"""Хранилище на локальном диске.

Вся работа с диском — через aiofiles, то есть в пуле потоков. Раньше файл писался
синхронным ``write_bytes`` прямо в корутине: вызов выглядел асинхронным, но на время
записи блокировал event loop целиком, и приложение переставало отвечать на все запросы
разом (В1).

Второе отличие — потоковость. Исходный код читал загрузку целиком в память
(``await upload_file.read()``), затем писал её копию на диск, а потом задача читала тот же
файл заново: пик памяти — два-три размера файла на каждую параллельную загрузку (В2).
Здесь файл проходит чанками, а размер и первые байты (нужные для определения типа)
считаются тем же единственным проходом.
"""

from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles
import aiofiles.os

from src.storage.base import SavedFile, StorageLimitExceeded

CHUNK_SIZE = 1024 * 1024
HEAD_SIZE = 4096


class LocalFileStorage:
    def __init__(self, root: Path, chunk_size: int = CHUNK_SIZE) -> None:
        self._root = root
        self._chunk_size = chunk_size

    async def ensure_ready(self) -> None:
        await aiofiles.os.makedirs(self._root, exist_ok=True)

    def path_for(self, stored_name: str) -> str:
        return str(self._root / stored_name)

    async def save(
        self,
        stored_name: str,
        chunks: AsyncIterator[bytes],
        max_size: int | None = None,
    ) -> SavedFile:
        target = self._root / stored_name
        size = 0
        head = b""

        try:
            async with aiofiles.open(target, "wb") as target_file:
                async for chunk in chunks:
                    if not chunk:
                        continue
                    size += len(chunk)
                    if max_size is not None and size > max_size:
                        raise StorageLimitExceeded(max_size)
                    if len(head) < HEAD_SIZE:
                        head += chunk[: HEAD_SIZE - len(head)]
                    await target_file.write(chunk)
        except BaseException:
            # Оборванная загрузка не должна оставлять после себя обрубок файла.
            await self.delete(stored_name)
            raise

        return SavedFile(stored_name=stored_name, size=size, head=head)

    async def open(self, stored_name: str) -> AsyncIterator[bytes]:
        async with aiofiles.open(self._root / stored_name, "rb") as source:
            while chunk := await source.read(self._chunk_size):
                yield chunk

    async def read_head(self, stored_name: str, size: int = HEAD_SIZE) -> bytes:
        async with aiofiles.open(self._root / stored_name, "rb") as source:
            return await source.read(size)

    async def delete(self, stored_name: str) -> None:
        try:
            await aiofiles.os.remove(self._root / stored_name)
        except FileNotFoundError:
            pass

    async def exists(self, stored_name: str) -> bool:
        return await aiofiles.os.path.exists(self._root / stored_name)

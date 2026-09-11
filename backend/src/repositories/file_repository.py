"""Доступ к данным по файлам.

Репозиторий отвечает только на вопрос «дай/сохрани данные» и ничего не знает ни про HTTP,
ни про файловую систему. Не нашли запись — вернули ``None``, решение о том, что это ошибка
и какая, принимает слой выше (Б1).

Транзакцией репозиторий тоже не владеет: ``commit`` вызывает сервис, потому что граница
транзакции — это граница сценария, а не отдельного запроса (Б2).
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import StoredFile


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, file_id: str) -> StoredFile | None:
        return await self._session.get(StoredFile, file_id)

    async def list(self, limit: int | None = None, offset: int = 0) -> list[StoredFile]:
        query = select(StoredFile).order_by(StoredFile.created_at.desc()).offset(offset)
        if limit is not None:
            query = query.limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(StoredFile))
        return result.scalar_one()

    def add(self, file_item: StoredFile) -> None:
        self._session.add(file_item)

    async def delete(self, file_item: StoredFile) -> None:
        await self._session.delete(file_item)

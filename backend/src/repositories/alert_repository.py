"""Доступ к данным по алертам."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import AlertLevel
from src.models import Alert


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, limit: int | None = None, offset: int = 0) -> list[Alert]:
        query = select(Alert).order_by(Alert.created_at.desc()).offset(offset)
        if limit is not None:
            query = query.limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(Alert))
        return result.scalar_one()

    async def exists_for_file(self, file_id: str, level: AlertLevel) -> bool:
        """Есть ли уже такой алерт по файлу.

        Нужно для идемпотентности задач: повторная доставка сообщения не должна
        порождать второй одинаковый алерт (A5).
        """
        result = await self._session.execute(
            select(Alert.id).where(Alert.file_id == file_id, Alert.level == level).limit(1)
        )
        return result.scalar_one_or_none() is not None

    def add(self, alert: Alert) -> None:
        self._session.add(alert)

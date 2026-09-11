"""Сценарии по алертам."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Alert
from src.repositories import AlertRepository


class AlertService:
    def __init__(self, session: AsyncSession) -> None:
        self._alerts = AlertRepository(session)

    async def list(self, limit: int | None, offset: int) -> tuple[list[Alert], int]:
        return await self._alerts.list(limit, offset), await self._alerts.count()

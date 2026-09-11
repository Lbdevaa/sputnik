"""Сценарии работы с файлами.

Сервис владеет транзакцией и порядком шагов, репозиторий — запросами, домен — правилами.
HTTP тут нет: наружу летят доменные ошибки, а в коды ответов их переводит ``api/errors.py``.

Один и тот же сервис вызывается и из HTTP-обработчика, и из celery-задачи — потому что
сессия приходит снаружи, а не создаётся внутри каждой функции (Б2).
"""

import logging
from collections.abc import AsyncIterator
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.core.exceptions import EmptyFile, FileNotFound, FileTooLarge, StoredFileMissing
from src.domain.enums import AlertLevel, ProcessingStatus, ScanStatus
from src.domain.media_type import detect_media_type
from src.domain.metadata import base_metadata, collector_for
from src.domain.scanner import extension_of, scan
from src.models import Alert, StoredFile
from src.repositories import AlertRepository, FileRepository
from src.storage import FileStorage, StorageLimitExceeded

logger = logging.getLogger(__name__)


class FileService:
    def __init__(
        self,
        session: AsyncSession,
        storage: FileStorage,
        settings: Settings,
    ) -> None:
        self._session = session
        self._storage = storage
        self._settings = settings
        self._files = FileRepository(session)
        self._alerts = AlertRepository(session)

    async def list(self, limit: int | None, offset: int) -> tuple[list[StoredFile], int]:
        return await self._files.list(limit, offset), await self._files.count()

    async def get(self, file_id: str) -> StoredFile:
        file_item = await self._files.get(file_id)
        if file_item is None:
            raise FileNotFound(file_id)
        return file_item

    async def upload(
        self,
        title: str,
        filename: str,
        chunks: AsyncIterator[bytes],
        declared_type: str | None = None,
    ) -> StoredFile:
        file_id = str(uuid4())
        stored_name = f"{file_id}{extension_of(filename)}"

        try:
            saved = await self._storage.save(
                stored_name, chunks, max_size=self._settings.max_upload_size
            )
        except StorageLimitExceeded as error:
            raise FileTooLarge(error.limit) from error

        if saved.size == 0:
            await self._storage.delete(stored_name)
            raise EmptyFile

        file_item = StoredFile(
            id=file_id,
            title=title,
            original_name=filename or stored_name,
            stored_name=stored_name,
            mime_type=detect_media_type(saved.head, filename=filename, declared=declared_type),
            size=saved.size,
            processing_status=ProcessingStatus.UPLOADED,
        )
        self._files.add(file_item)
        try:
            await self._session.commit()
        except Exception:
            # Компенсация: без записи в базе файл на диске — мусор, который никто
            # никогда не найдёт (A8).
            await self._storage.delete(stored_name)
            raise
        await self._session.refresh(file_item)
        return file_item

    async def rename(self, file_id: str, title: str) -> StoredFile:
        file_item = await self.get(file_id)
        file_item.title = title
        await self._session.commit()
        await self._session.refresh(file_item)
        return file_item

    async def delete(self, file_id: str) -> None:
        file_item = await self.get(file_id)
        stored_name = file_item.stored_name

        # Сначала база, потом диск (A8). В обратном порядке сбой на коммите оставлял
        # запись без файла: карточка открывается, скачивание отдаёт 404.
        await self._files.delete(file_item)
        await self._session.commit()

        try:
            await self._storage.delete(stored_name)
        except OSError:
            # Файл-сирота на диске — плохо, но это уже не рассинхрон, видимый снаружи.
            logger.warning("stored file left on disk", extra={"stored_name": stored_name})

    async def path_for_download(self, file_id: str) -> tuple[StoredFile, str]:
        file_item = await self.get(file_id)
        if not await self._storage.exists(file_item.stored_name):
            raise StoredFileMissing(file_id)
        return file_item, self._storage.path_for(file_item.stored_name)

    async def mark_processing(self, file_id: str) -> StoredFile:
        """Отметить начало обработки отдельной транзакцией.

        Раньше статус ``processing`` коммитился вместе с результатом проверки, поэтому
        снаружи он означал «проверка уже закончилась» (A2).
        """
        file_item = await self.get(file_id)
        file_item.processing_status = ProcessingStatus.PROCESSING
        await self._session.commit()
        return file_item

    async def scan(self, file_id: str) -> StoredFile:
        file_item = await self.get(file_id)
        result = scan(
            filename=file_item.original_name,
            size=file_item.size,
            media_type=file_item.mime_type,
            suspicious_size=self._settings.suspicious_size,
        )
        file_item.scan_status = result.status
        file_item.scan_details = result.details
        file_item.requires_attention = result.requires_attention
        await self._session.commit()
        return file_item

    async def extract_metadata(self, file_id: str) -> StoredFile:
        file_item = await self.get(file_id)

        if not await self._storage.exists(file_item.stored_name):
            file_item.processing_status = ProcessingStatus.FAILED
            file_item.scan_status = file_item.scan_status or ScanStatus.FAILED
            file_item.scan_details = "stored file not found during metadata extraction"
            await self._session.commit()
            return file_item

        metadata = base_metadata(
            extension=extension_of(file_item.original_name),
            size=file_item.size,
            media_type=file_item.mime_type,
        )
        collector = collector_for(file_item.mime_type)
        async for chunk in self._storage.open(file_item.stored_name):
            collector.feed(chunk)
        metadata.update(collector.result())

        file_item.metadata_json = metadata
        file_item.processing_status = ProcessingStatus.PROCESSED
        await self._session.commit()
        return file_item

    async def raise_alert(self, file_id: str) -> Alert | None:
        """Записать итоговый алерт по файлу.

        Повторный запуск задачи (штатное поведение Celery при потере воркера) не должен
        порождать второй такой же алерт (A5).
        """
        file_item = await self.get(file_id)

        if file_item.processing_status == ProcessingStatus.FAILED:
            level, message = AlertLevel.CRITICAL, "File processing failed"
        elif file_item.requires_attention:
            level = AlertLevel.WARNING
            message = f"File requires attention: {file_item.scan_details}"
        else:
            level, message = AlertLevel.INFO, "File processed successfully"

        if await self._alerts.exists_for_file(file_id, level):
            logger.info("alert already exists", extra={"file_id": file_id, "level": level.value})
            return None

        alert = Alert(file_id=file_id, level=level, message=message)
        self._alerts.add(alert)
        await self._session.commit()
        await self._session.refresh(alert)
        return alert

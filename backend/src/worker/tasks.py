"""Задачи конвейера обработки.

Задача — тонкая: разобрать аргументы, открыть сессию, вызвать сценарий. Вся логика живёт
в ``services/file_service.py`` и вызывается в тестах напрямую, без брокера.

Каждая задача умеет повторяться (``autoretry_for``) и подтверждается только после успеха
(``task_acks_late`` в конфигурации): падение воркера посреди работы возвращает сообщение
в очередь, а не теряет его (A4). Повтор безопасен, потому что сценарии идемпотентны (A5).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from src.core.config import get_settings
from src.core.db import get_session_maker
from src.core.exceptions import FileNotFound
from src.services import FileService
from src.storage import get_storage
from src.worker.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()

RETRY_KWARGS = {
    "autoretry_for": (Exception,),
    "retry_backoff": True,
    "retry_backoff_max": 60,
    "retry_jitter": True,
    "max_retries": 5,
}

_worker_loop: asyncio.AbstractEventLoop | None = None


def run_in_worker_loop[T](coroutine: Awaitable[T]) -> T:
    """Выполнить корутину в event loop процесса-воркера.

    Луп создаётся один на процесс и переиспользуется: пул соединений SQLAlchemy привязан
    к лупу, и пересоздание лупа на каждую задачу обесценивало бы пул.
    """
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coroutine)


async def _with_service[T](action: Callable[[FileService], Awaitable[T]]) -> T:
    async with get_session_maker()() as session:
        return await action(FileService(session=session, storage=get_storage(), settings=settings))


@celery_app.task(name="scan_file_for_threats", **RETRY_KWARGS)
def scan_file_for_threats(file_id: str) -> None:
    async def action(service: FileService) -> None:
        # Отдельная транзакция до тяжёлой работы: иначе статус «в обработке» появляется
        # снаружи одновременно с результатом проверки и потому не значит ничего (A2).
        await service.mark_processing(file_id)
        await service.scan(file_id)

    if not _run(file_id, action):
        return
    extract_file_metadata.delay(file_id)


@celery_app.task(name="extract_file_metadata", **RETRY_KWARGS)
def extract_file_metadata(file_id: str) -> None:
    if not _run(file_id, lambda service: service.extract_metadata(file_id)):
        return
    send_file_alert.delay(file_id)


@celery_app.task(name="send_file_alert", **RETRY_KWARGS)
def send_file_alert(file_id: str) -> None:
    _run(file_id, lambda service: service.raise_alert(file_id))


def _run(file_id: str, action: Callable[[FileService], Awaitable[object]]) -> bool:
    """Выполнить шаг конвейера. ``False`` — файла больше нет, цепочку продолжать незачем.

    Раньше исчезнувший файл приводил к молчаливому ``return``: цепочка обрывалась, алерта
    не появлялось, и в логах не оставалось ничего (A4).
    """
    try:
        run_in_worker_loop(_with_service(action))
    except FileNotFound:
        logger.warning("file is gone, pipeline stopped", extra={"file_id": file_id})
        return False
    return True

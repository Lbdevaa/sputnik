"""Конфигурация Celery и инициализация ресурсов в дочерних процессах.

Главная тонкость здесь — форк. Celery с пулом prefork создаёт дочерние процессы копией
родительского, и всё, что родитель успел открыть на импорте, дети наследуют: сокеты,
файловые дескрипторы, пул соединений asyncpg вместе с привязанным к нему event loop.
Пользоваться таким пулом нельзя — в лучшем случае каждое обращение открывает новое
соединение, в худшем прилетает InterfaceError под нагрузкой (В3).

Поэтому движок создаётся лениво (см. core/db.py), а после форка ссылка на него
сбрасывается: каждый дочерний процесс строит свой пул сам.
"""

import logging

from celery import Celery
from celery.signals import setup_logging, worker_process_init, worker_process_shutdown

from src.core.config import get_settings
from src.core.db import reset_engine
from src.core.logging import configure_logging

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery(
    "file_tasks",
    broker=settings.celery_broker_url,
    backend=settings.result_backend,
    include=["src.worker.tasks"],
)

celery_app.conf.update(
    # Celery по умолчанию перехватывает root logger и навязывает свой текстовый формат;
    # нам нужен один формат логов на оба процесса (Б9).
    worker_hijack_root_logger=False,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)


@setup_logging.connect
def setup_worker_logging(**_: object) -> None:
    configure_logging(settings.log_level)


@worker_process_init.connect
def init_worker_process(**_: object) -> None:
    configure_logging(settings.log_level)
    # Наследованный от родителя пул закрывать нельзя — сокеты чужие. Просто забываем
    # про него: следующее обращение к базе создаст свой.
    reset_engine()
    logger.info("worker process initialised")


@worker_process_shutdown.connect
def shutdown_worker_process(**_: object) -> None:
    reset_engine()

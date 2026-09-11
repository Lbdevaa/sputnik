"""Окружение для тестов.

Настройки читаются из переменных окружения при импорте ``src.worker.tasks`` (его тянет
``src.api.v1.files``), поэтому в CI без ``.env.dev`` нужны значения по умолчанию. Реальные
подключения в тестах не открываются: сессия и хранилище приходят из фикстур.
"""

import os

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")

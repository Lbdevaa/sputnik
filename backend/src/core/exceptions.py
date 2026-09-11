"""Доменные ошибки.

Раньше бизнес-логика бросала ``HTTPException`` (Б1): чтобы удалить файл из celery-задачи,
пришлось бы ловить исключение веб-фреймворка в процессе, где никакого HTTP нет.

Здесь ошибки описаны в терминах предметной области, а перевод в коды ответов живёт
в единственном месте — ``api/errors.py``.
"""


class DomainError(Exception):
    """Базовая ошибка сценария."""


class FileNotFound(DomainError):
    def __init__(self, file_id: str) -> None:
        super().__init__(f"file {file_id} not found")
        self.file_id = file_id


class StoredFileMissing(DomainError):
    """Запись в базе есть, а файла на диске нет."""

    def __init__(self, file_id: str) -> None:
        super().__init__(f"stored file for {file_id} not found")
        self.file_id = file_id


class EmptyFile(DomainError):
    def __init__(self) -> None:
        super().__init__("file is empty")


class FileTooLarge(DomainError):
    def __init__(self, limit: int) -> None:
        super().__init__(f"file is larger than {limit} bytes")
        self.limit = limit

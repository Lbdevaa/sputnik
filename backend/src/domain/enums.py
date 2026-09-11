"""Состояния конвейера обработки.

Раньше это были голые строки в семи местах кода (Б5): опечатка в ``"proccessing"``
не ловилась ничем и проявлялась как файл, навсегда застрявший в непонятном статусе.
Значения совпадают со строками, которые уже лежат в базе и уходят на фронт, —
контракт не меняется.
"""

from enum import StrEnum


class ProcessingStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class ScanStatus(StrEnum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    FAILED = "failed"


class AlertLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

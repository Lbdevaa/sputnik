"""Правила проверки файла на угрозы.

Единственная настоящая бизнес-логика проекта. Раньше она жила внутри тела celery-задачи,
между открытием сессии и коммитом (Б8): чтобы проверить, что ``.exe`` помечается
подозрительным, требовались Redis, Postgres и файл на диске.

Здесь это чистая функция: ни базы, ни файловой системы, ни Celery. Таблица «вход → выход»
из docs/behaviour.md ложится на неё построчно.
"""

from dataclasses import dataclass
from pathlib import PurePosixPath

from src.domain.enums import ScanStatus

SUSPICIOUS_EXTENSIONS = frozenset({".exe", ".bat", ".cmd", ".sh", ".js"})
DEFAULT_SUSPICIOUS_SIZE = 10 * 1024 * 1024
PDF_COMPATIBLE_MEDIA_TYPES = frozenset({"application/pdf", "application/octet-stream"})
NO_THREATS = "no threats found"


@dataclass(frozen=True, slots=True)
class ScanResult:
    status: ScanStatus
    details: str
    reasons: tuple[str, ...]

    @property
    def requires_attention(self) -> bool:
        return bool(self.reasons)


def extension_of(filename: str) -> str:
    return PurePosixPath(filename).suffix.lower()


def scan(
    filename: str,
    size: int,
    media_type: str,
    suspicious_size: int = DEFAULT_SUSPICIOUS_SIZE,
) -> ScanResult:
    """Проверить файл по набору правил.

    ``media_type`` — тип, определённый по содержимому (см. ``domain.media_type``), а не
    заголовок клиента: иначе проверка на несоответствие расширения и типа обходится
    подстановкой заголовка (A9).
    """
    reasons: list[str] = []
    extension = extension_of(filename)

    if extension in SUSPICIOUS_EXTENSIONS:
        reasons.append(f"suspicious extension {extension}")

    if size > suspicious_size:
        reasons.append(f"file is larger than {suspicious_size // (1024 * 1024)} MB")

    if extension == ".pdf" and media_type not in PDF_COMPATIBLE_MEDIA_TYPES:
        reasons.append("pdf extension does not match mime type")

    if reasons:
        return ScanResult(
            status=ScanStatus.SUSPICIOUS,
            details=", ".join(reasons),
            reasons=tuple(reasons),
        )
    return ScanResult(status=ScanStatus.CLEAN, details=NO_THREATS, reasons=())

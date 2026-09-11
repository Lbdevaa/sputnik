"""Определение типа файла по содержимому.

Раньше тип брался из заголовка ``Content-Type``, который присылает клиент, и на нём же
строилась проверка «расширение .pdf не совпадает с типом» (A9). Проверку, которая доверяет
проверяемому, обойти нечем: достаточно отправить свой заголовок.

Здесь тип определяется по сигнатуре в первых байтах, а заголовок клиента и расширение —
только подсказки на случай, когда сигнатуры нет (текст, csv, json). Полноценный libmagic
для четырёх форматов не нужен и тянуть системную зависимость ради него не хочется.
"""

from dataclasses import dataclass

DEFAULT_MEDIA_TYPE = "application/octet-stream"
TEXT_MEDIA_TYPE = "text/plain"


@dataclass(frozen=True, slots=True)
class Signature:
    media_type: str
    prefix: bytes
    offset: int = 0


SIGNATURES: tuple[Signature, ...] = (
    Signature("application/pdf", b"%PDF-"),
    Signature("image/png", b"\x89PNG\r\n\x1a\n"),
    Signature("image/jpeg", b"\xff\xd8\xff"),
    Signature("image/gif", b"GIF8"),
    Signature("application/zip", b"PK\x03\x04"),
    Signature("application/gzip", b"\x1f\x8b"),
    Signature("application/x-msdownload", b"MZ"),
    Signature("application/x-executable", b"\x7fELF"),
    Signature("application/x-7z-compressed", b"7z\xbc\xaf\x27\x1c"),
    Signature("application/rtf", b"{\\rtf"),
    Signature("audio/mpeg", b"ID3"),
    Signature("video/mp4", b"ftyp", offset=4),
)

# Признаки двоичного содержимого: нулевой байт и управляющие символы, которых
# не бывает в тексте.
_CONTROL_BYTES = bytes(range(0, 9)) + bytes(range(14, 32))


def looks_like_text(head: bytes) -> bool:
    if not head:
        return False
    if b"\x00" in head:
        return False
    sample = head[:1024]
    control = sum(1 for byte in sample if byte in _CONTROL_BYTES)
    return control / len(sample) < 0.05


def detect_media_type(head: bytes, filename: str = "", declared: str | None = None) -> str:
    """Тип файла по его началу.

    ``declared`` (заголовок клиента) используется только как последняя подсказка и только
    тогда, когда содержимое не противоречит: для файла с двоичным содержимым заявленный
    ``text/plain`` игнорируется.
    """
    for signature in SIGNATURES:
        chunk = head[signature.offset : signature.offset + len(signature.prefix)]
        if chunk == signature.prefix:
            return signature.media_type

    if looks_like_text(head):
        if declared and declared.startswith("text/"):
            return declared
        if declared in {"application/json", "application/xml", "application/javascript"}:
            return declared
        return TEXT_MEDIA_TYPE

    if declared and declared != TEXT_MEDIA_TYPE and not declared.startswith("text/"):
        return declared

    return DEFAULT_MEDIA_TYPE

"""Тип файла по содержимому, заголовок клиента — только подсказка (A9)."""

import pytest

from src.domain.media_type import (
    DEFAULT_MEDIA_TYPE,
    TEXT_MEDIA_TYPE,
    detect_media_type,
    looks_like_text,
)

PDF_HEAD = b"%PDF-1.4\n1 0 obj\n"
EXE_HEAD = b"MZ\x90\x00fake executable payload\n"
PNG_HEAD = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"


@pytest.mark.parametrize(
    ("head", "declared", "expected"),
    [
        # Сигнатура побеждает заголовок: обход через Content-Type больше не работает.
        (PDF_HEAD, "text/plain", "application/pdf"),
        (EXE_HEAD, "text/plain", "application/x-msdownload"),
        (PNG_HEAD, "application/octet-stream", "image/png"),
        (b"\x00\x00\x01\x00ftypisom", None, "video/mp4"),
        # Текст: заголовок уточняет тип, если не противоречит содержимому.
        (b"line one\nline two\n", "text/plain", "text/plain"),
        (b"a,b,c\n1,2,3\n", "text/csv", "text/csv"),
        (b'{"a": 1}', "application/json", "application/json"),
        (b"hello", "application/octet-stream", TEXT_MEDIA_TYPE),
        (b"hello", None, TEXT_MEDIA_TYPE),
        # Двоичное без сигнатуры: заявленный двоичный тип принимается, text/* — нет.
        (b"\x00\x01\x02\x03binary", "application/octet-stream", "application/octet-stream"),
        (b"\x00\x01\x02\x03binary", "application/vnd.custom", "application/vnd.custom"),
        (b"\x00\x01\x02\x03binary", "text/plain", DEFAULT_MEDIA_TYPE),
        (b"\x00\x01\x02\x03binary", None, DEFAULT_MEDIA_TYPE),
        (b"", None, DEFAULT_MEDIA_TYPE),
    ],
)
def test_detect_media_type(head, declared, expected):
    assert detect_media_type(head, filename="x", declared=declared) == expected


def test_looks_like_text_rejects_nul_and_control_bytes():
    assert looks_like_text(b"plain text\r\n\twith tabs")
    assert not looks_like_text(b"text\x00with nul")
    assert not looks_like_text(bytes(range(32)) * 4)
    assert not looks_like_text(b"")


def test_utf8_text_counts_as_text():
    assert looks_like_text("привет, мир\n".encode())

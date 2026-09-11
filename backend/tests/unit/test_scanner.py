"""Правила детекта: таблица «вход → выход» из docs/behaviour.md построчно.

Ни базы, ни файловой системы, ни Celery — ровно то, ради чего правила вынесены в домен (Б8).
"""

import pytest

from src.domain.enums import ScanStatus
from src.domain.scanner import DEFAULT_SUSPICIOUS_SIZE, ScanResult, extension_of, scan

MB = 1024 * 1024


@pytest.mark.parametrize(
    ("filename", "size", "media_type", "status", "details"),
    [
        ("sample.txt", 29, "text/plain", ScanStatus.CLEAN, "no threats found"),
        (
            "sample.exe",
            28,
            "application/x-msdownload",
            ScanStatus.SUSPICIOUS,
            "suspicious extension .exe",
        ),
        ("sample.pdf", 123, "application/pdf", ScanStatus.CLEAN, "no threats found"),
        (
            "big.bin",
            11_000_000,
            "application/octet-stream",
            ScanStatus.SUSPICIOUS,
            "file is larger than 10 MB",
        ),
        ("script.js", 10, "text/plain", ScanStatus.SUSPICIOUS, "suspicious extension .js"),
        ("run.sh", 10, "text/plain", ScanStatus.SUSPICIOUS, "suspicious extension .sh"),
        (
            "ARCHIVE.EXE",
            10,
            "application/x-msdownload",
            ScanStatus.SUSPICIOUS,
            "suspicious extension .exe",
        ),
        (
            "fake.pdf",
            10,
            "text/plain",
            ScanStatus.SUSPICIOUS,
            "pdf extension does not match mime type",
        ),
        ("blob.pdf", 10, "application/octet-stream", ScanStatus.CLEAN, "no threats found"),
    ],
)
def test_behaviour_table(filename, size, media_type, status, details):
    result = scan(filename=filename, size=size, media_type=media_type)

    assert result.status is status
    assert result.details == details
    assert result.requires_attention is (status is ScanStatus.SUSPICIOUS)


def test_reasons_are_joined_in_rule_order():
    result = scan(
        filename="payload.exe",
        size=DEFAULT_SUSPICIOUS_SIZE + 1,
        media_type="application/octet-stream",
    )

    assert result.details == "suspicious extension .exe, file is larger than 10 MB"
    assert result.reasons == ("suspicious extension .exe", "file is larger than 10 MB")


def test_size_threshold_is_strict():
    exactly = scan(
        filename="a.bin", size=DEFAULT_SUSPICIOUS_SIZE, media_type="application/octet-stream"
    )
    over = scan(
        filename="a.bin", size=DEFAULT_SUSPICIOUS_SIZE + 1, media_type="application/octet-stream"
    )

    assert exactly.status is ScanStatus.CLEAN
    assert over.status is ScanStatus.SUSPICIOUS


def test_threshold_comes_from_settings_not_from_constant():
    result = scan(
        filename="a.bin", size=2 * MB, media_type="application/octet-stream", suspicious_size=MB
    )

    assert result.details == "file is larger than 1 MB"


def test_result_is_immutable():
    result = scan(filename="a.txt", size=1, media_type="text/plain")

    assert isinstance(result, ScanResult)
    with pytest.raises(AttributeError):
        result.status = ScanStatus.SUSPICIOUS  # type: ignore[misc]


@pytest.mark.parametrize(
    ("filename", "extension"),
    [("a.txt", ".txt"), ("A.TXT", ".txt"), ("archive.tar.gz", ".gz"), ("noext", ""), ("", "")],
)
def test_extension_of(filename, extension):
    assert extension_of(filename) == extension

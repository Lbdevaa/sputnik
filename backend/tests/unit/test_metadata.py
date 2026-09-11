"""Накопители метаданных: файл приходит кусками, разрезы — в неудобных местах (В2, A11)."""

import pytest

from src.domain.metadata import (
    NullCollector,
    PdfCollector,
    TextCollector,
    base_metadata,
    collector_for,
)


def collect(collector, data: bytes, chunk_size: int) -> dict:
    for start in range(0, len(data), chunk_size):
        collector.feed(data[start : start + chunk_size])
    return collector.result()


SAMPLE_TXT = b"line one\nline two\nline three\n"  # тот же файл, что в docs/behaviour.md


@pytest.mark.parametrize("chunk_size", [1, 2, 7, 1024])
def test_text_matches_baseline_regardless_of_chunking(chunk_size):
    assert collect(TextCollector(), SAMPLE_TXT, chunk_size) == {"line_count": 3, "char_count": 29}


@pytest.mark.parametrize(
    ("data", "lines", "chars"),
    [
        (b"", 0, 0),
        (b"no newline", 1, 10),
        (b"one\ntwo", 2, 7),
        (b"a\r\nb\r\n", 2, 6),
        (b"a\rb\r", 2, 4),
        (b"\n\n\n", 3, 3),
    ],
)
def test_text_line_counting_matches_splitlines(data, lines, chars):
    assert collect(TextCollector(), data, 3) == {"line_count": lines, "char_count": chars}
    assert lines == len(data.decode().splitlines())


@pytest.mark.parametrize("chunk_size", [1, 3, 5])
def test_multibyte_character_split_across_chunks_counts_once(chunk_size):
    data = "привет\nмир".encode()

    assert collect(TextCollector(), data, chunk_size) == {"line_count": 2, "char_count": 10}


TWO_PAGES_PDF = (
    b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>\nendobj\n"
    b"3 0 obj\n<< /Type/Page >>\nendobj\n"
    b"4 0 obj\n<< /Type /Page >>\nendobj\n"
    b"trailer\n%%EOF\n"
)


@pytest.mark.parametrize("chunk_size", [1, 2, 3, 8, 13, 64, 4096])
def test_pdf_counts_both_spellings_and_skips_pages_node(chunk_size):
    assert collect(PdfCollector(), TWO_PAGES_PDF, chunk_size) == {"approx_page_count": 2}


def test_pdf_without_page_objects_reports_at_least_one():
    assert collect(PdfCollector(), b"%PDF-1.4\n%%EOF\n", 4) == {"approx_page_count": 1}


def test_pdf_match_split_on_chunk_boundary_is_not_double_counted():
    data = b"<< /Type /Page >>" * 3
    cut = data.index(b"/Page") + 2  # разрез внутри «/Page»
    collector = PdfCollector()
    collector.feed(data[:cut])
    collector.feed(data[cut:])

    assert collector.result() == {"approx_page_count": 3}


@pytest.mark.parametrize(
    ("media_type", "collector_type"),
    [
        ("text/plain", TextCollector),
        ("text/csv", TextCollector),
        ("application/pdf", PdfCollector),
        ("application/octet-stream", NullCollector),
        ("image/png", NullCollector),
    ],
)
def test_collector_for(media_type, collector_type):
    assert isinstance(collector_for(media_type), collector_type)


def test_base_metadata_keys_match_baseline():
    assert base_metadata(".txt", 29, "text/plain") == {
        "extension": ".txt",
        "size_bytes": 29,
        "mime_type": "text/plain",
    }

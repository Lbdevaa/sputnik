"""Локальное хранилище: потоковая запись, лимит посреди приёма, чистка обрубков (В1, В2, A10)."""

from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from src.storage import LocalFileStorage, StorageLimitExceeded
from src.storage.local import HEAD_SIZE


async def stream(*chunks: bytes) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


@pytest.fixture
async def storage(tmp_path: Path) -> LocalFileStorage:
    instance = LocalFileStorage(tmp_path / "files", chunk_size=4)
    await instance.ensure_ready()
    return instance


async def test_save_counts_size_and_head_in_one_pass(storage: LocalFileStorage, tmp_path: Path):
    payload = b"%PDF-" + b"x" * (HEAD_SIZE * 2)

    saved = await storage.save("a.pdf", stream(payload[:3], payload[3:10], payload[10:]))

    assert saved.size == len(payload)
    assert saved.head == payload[:HEAD_SIZE]
    assert (tmp_path / "files" / "a.pdf").read_bytes() == payload


async def test_limit_is_enforced_mid_stream_and_leaves_no_file(storage: LocalFileStorage):
    with pytest.raises(StorageLimitExceeded) as error:
        await storage.save("big.bin", stream(b"12345", b"67890", b"extra"), max_size=8)

    assert error.value.limit == 8
    assert not await storage.exists("big.bin")


async def test_broken_upload_leaves_no_file(storage: LocalFileStorage):
    async def failing() -> AsyncIterator[bytes]:
        yield b"partial"
        raise ConnectionError("client went away")

    with pytest.raises(ConnectionError):
        await storage.save("broken.bin", failing())

    assert not await storage.exists("broken.bin")


async def test_open_streams_in_chunks(storage: LocalFileStorage):
    await storage.save("t.txt", stream(b"0123456789"))

    chunks = [chunk async for chunk in storage.open("t.txt")]

    assert chunks == [b"0123", b"4567", b"89"]


async def test_delete_is_idempotent(storage: LocalFileStorage):
    await storage.save("t.txt", stream(b"x"))

    await storage.delete("t.txt")
    await storage.delete("t.txt")

    assert not await storage.exists("t.txt")


async def test_empty_stream_saves_empty_file(storage: LocalFileStorage):
    saved = await storage.save("empty.txt", stream())

    assert saved.size == 0
    assert saved.head == b""
    assert await storage.exists("empty.txt")

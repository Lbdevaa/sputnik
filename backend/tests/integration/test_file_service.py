"""Сценарии FileService вызываются напрямую: без HTTP, без Celery, без Postgres.

Это тот самый аргумент из docs/architecture.md: конвейер обработки — обычные методы
сервиса, а задачи Celery лишь передают им ``file_id``.
"""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import EmptyFile, FileNotFound, FileTooLarge, StoredFileMissing
from src.domain.enums import AlertLevel, ProcessingStatus, ScanStatus
from src.models import Alert
from src.services import FileService
from src.storage import LocalFileStorage
from tests.integration.conftest import MAX_UPLOAD, SAMPLE_EXE, SAMPLE_TXT, TWO_PAGES_PDF, stream


async def run_pipeline(service: FileService, file_id: str):
    """Ровно та последовательность, которую выполняют три задачи Celery."""
    await service.mark_processing(file_id)
    await service.scan(file_id)
    await service.extract_metadata(file_id)
    return await service.raise_alert(file_id)


async def alert_count(session: AsyncSession) -> int:
    return (await session.execute(select(func.count()).select_from(Alert))).scalar_one()


# --- загрузка ---------------------------------------------------------------------------


async def test_upload_stores_record_and_file(service: FileService, storage: LocalFileStorage):
    file_item = await service.upload(
        "t", "sample.txt", stream(SAMPLE_TXT), declared_type="text/plain"
    )

    assert file_item.processing_status is ProcessingStatus.UPLOADED
    assert file_item.scan_status is None
    assert file_item.size == len(SAMPLE_TXT)
    assert file_item.mime_type == "text/plain"
    assert file_item.stored_name == f"{file_item.id}.txt"
    assert await storage.exists(file_item.stored_name)


async def test_upload_detects_type_by_content_not_by_header(service: FileService):
    file_item = await service.upload(
        "spoof", "doc.pdf", stream(TWO_PAGES_PDF), declared_type="text/plain"
    )

    assert file_item.mime_type == "application/pdf"


async def test_upload_rejects_empty_file_and_leaves_no_trace(
    service: FileService, storage: LocalFileStorage
):
    with pytest.raises(EmptyFile):
        await service.upload("t", "empty.txt", stream(b""))

    files, total = await service.list(limit=None, offset=0)
    assert (files, total) == ([], 0)
    assert not list((storage._root).iterdir())


async def test_upload_over_limit_is_rejected_mid_stream(
    service: FileService, storage: LocalFileStorage
):
    with pytest.raises(FileTooLarge) as error:
        await service.upload("t", "big.bin", stream(b"x" * (MAX_UPLOAD + 1)))

    assert error.value.limit == MAX_UPLOAD
    assert not list((storage._root).iterdir())


async def test_upload_removes_file_when_commit_fails(
    service: FileService, session: AsyncSession, storage: LocalFileStorage, monkeypatch
):
    """A8: без записи в базе файл на диске — мусор, который никто не найдёт."""

    async def failing_commit():
        raise RuntimeError("database is down")

    monkeypatch.setattr(session, "commit", failing_commit)

    with pytest.raises(RuntimeError):
        await service.upload("t", "sample.txt", stream(SAMPLE_TXT))

    assert not list((storage._root).iterdir())


# --- конвейер ---------------------------------------------------------------------------


async def test_pipeline_for_text_file_matches_baseline(service: FileService):
    file_item = await service.upload(
        "t", "sample.txt", stream(SAMPLE_TXT), declared_type="text/plain"
    )

    alert = await run_pipeline(service, file_item.id)

    assert file_item.processing_status is ProcessingStatus.PROCESSED
    assert file_item.scan_status is ScanStatus.CLEAN
    assert file_item.scan_details == "no threats found"
    assert file_item.requires_attention is False
    assert file_item.metadata_json == {
        "extension": ".txt",
        "size_bytes": 29,
        "mime_type": "text/plain",
        "line_count": 3,
        "char_count": 29,
    }
    assert alert is not None
    assert (alert.level, alert.message) == (AlertLevel.INFO, "File processed successfully")


async def test_pipeline_for_executable_raises_warning(service: FileService):
    file_item = await service.upload("t", "sample.exe", stream(SAMPLE_EXE))

    alert = await run_pipeline(service, file_item.id)

    assert file_item.scan_status is ScanStatus.SUSPICIOUS
    assert file_item.requires_attention is True
    assert alert is not None
    assert alert.level is AlertLevel.WARNING
    assert alert.message == "File requires attention: suspicious extension .exe"


async def test_pipeline_for_pdf_counts_pages(service: FileService):
    file_item = await service.upload(
        "t", "two.pdf", stream(TWO_PAGES_PDF), declared_type="application/pdf"
    )

    await run_pipeline(service, file_item.id)

    assert file_item.scan_status is ScanStatus.CLEAN
    assert file_item.metadata_json["approx_page_count"] == 2


async def test_processing_status_is_visible_before_scan(service: FileService, session_maker):
    """A2: статус «в обработке» коммитится отдельно, так что другой сессии он виден."""
    file_item = await service.upload("t", "sample.txt", stream(SAMPLE_TXT))

    await service.mark_processing(file_item.id)

    async with session_maker() as other_session:
        other = await FileService(other_session, service._storage, service._settings).get(
            file_item.id
        )
        assert other.processing_status is ProcessingStatus.PROCESSING
        assert other.scan_status is None


async def test_missing_stored_file_ends_in_failed_and_critical_alert(
    service: FileService, storage: LocalFileStorage
):
    file_item = await service.upload("t", "sample.txt", stream(SAMPLE_TXT))
    await storage.delete(file_item.stored_name)

    alert = await run_pipeline(service, file_item.id)

    assert file_item.processing_status is ProcessingStatus.FAILED
    assert file_item.scan_details == "stored file not found during metadata extraction"
    assert alert is not None
    assert (alert.level, alert.message) == (AlertLevel.CRITICAL, "File processing failed")


async def test_alert_is_not_duplicated_on_redelivery(service: FileService, session: AsyncSession):
    """A5: повтор задачи (штатное поведение Celery при потере воркера) не плодит алерты."""
    file_item = await service.upload("t", "sample.txt", stream(SAMPLE_TXT))
    await run_pipeline(service, file_item.id)

    second = await service.raise_alert(file_item.id)

    assert second is None
    assert await alert_count(session) == 1


async def test_pipeline_step_on_unknown_file_raises_domain_error(service: FileService):
    with pytest.raises(FileNotFound):
        await service.mark_processing("no-such-id")


# --- переименование, скачивание, удаление -----------------------------------------------


async def test_rename(service: FileService):
    file_item = await service.upload("old", "sample.txt", stream(SAMPLE_TXT))

    renamed = await service.rename(file_item.id, "new")

    assert renamed.title == "new"


async def test_download_path_requires_file_on_disk(service: FileService, storage: LocalFileStorage):
    file_item = await service.upload("t", "sample.txt", stream(SAMPLE_TXT))
    _, path = await service.path_for_download(file_item.id)
    assert path == storage.path_for(file_item.stored_name)

    await storage.delete(file_item.stored_name)

    with pytest.raises(StoredFileMissing):
        await service.path_for_download(file_item.id)


async def test_delete_file_with_alert_removes_everything(
    service: FileService, session: AsyncSession, storage: LocalFileStorage
):
    """A1: раньше удаление любого обработанного файла падало на внешнем ключе."""
    file_item = await service.upload("t", "sample.txt", stream(SAMPLE_TXT))
    await run_pipeline(service, file_item.id)
    stored_name = file_item.stored_name

    await service.delete(file_item.id)

    with pytest.raises(FileNotFound):
        await service.get(file_item.id)
    assert await alert_count(session) == 0
    assert not await storage.exists(stored_name)


async def test_delete_commits_database_before_touching_disk(service: FileService, monkeypatch):
    """A8: сбой на диске не оставляет запись, у которой скачивание отдаёт 404."""
    file_item = await service.upload("t", "sample.txt", stream(SAMPLE_TXT))

    async def failing_delete(_stored_name: str) -> None:
        raise OSError("disk is read-only")

    monkeypatch.setattr(service._storage, "delete", failing_delete)

    await service.delete(file_item.id)

    with pytest.raises(FileNotFound):
        await service.get(file_item.id)


async def test_list_is_newest_first_and_paginated(service: FileService):
    ids = [(await service.upload(str(i), f"{i}.txt", stream(SAMPLE_TXT))).id for i in range(3)]

    page, total = await service.list(limit=2, offset=0)
    rest, _ = await service.list(limit=2, offset=2)

    assert total == 3
    assert [item.id for item in page] + [item.id for item in rest] == list(reversed(ids))

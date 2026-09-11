"""HTTP-контракт из docs/behaviour.md, раздел 2, плюс регрессии на дефекты A1, A7, A10.

Приложение собирается настоящее, подменяются только зависимости: сессия, хранилище,
настройки — и постановка задачи в Celery.
"""

from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import storage_dependency
from src.api.v1 import files as files_api
from src.core.config import Settings, get_settings
from src.core.db import get_session
from src.main import create_app
from src.models import Alert
from src.services import FileService
from src.storage import LocalFileStorage
from tests.integration.conftest import MAX_UPLOAD, SAMPLE_TXT


class FakeTask:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.error: Exception | None = None

    def delay(self, file_id: str) -> None:
        if self.error is not None:
            raise self.error
        self.calls.append(file_id)


@pytest.fixture
def scan_task(monkeypatch) -> FakeTask:
    task = FakeTask()
    monkeypatch.setattr(files_api, "scan_file_for_threats", task)
    return task


@pytest.fixture
async def client(
    session: AsyncSession, storage: LocalFileStorage, settings: Settings, scan_task: FakeTask
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[storage_dependency] = lambda: storage
    app.dependency_overrides[get_settings] = lambda: settings

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def upload(client: httpx.AsyncClient, name: str = "sample.txt", data: bytes = SAMPLE_TXT, **kwargs):
    return await client.post("/files", data={"title": "t"}, files={"file": (name, data, "text/plain")}, **kwargs)


async def test_upload_returns_201_and_enqueues_scan(client: httpx.AsyncClient, scan_task: FakeTask):
    response = await upload(client)

    assert response.status_code == 201
    body = response.json()
    assert body["processing_status"] == "uploaded"
    assert body["scan_status"] is None
    assert body["original_name"] == "sample.txt"
    assert scan_task.calls == [body["id"]]


async def test_upload_succeeds_even_if_broker_is_down(client: httpx.AsyncClient, scan_task: FakeTask):
    """A7: файл уже сохранён, клиент не должен получать 500 из-за Redis."""
    scan_task.error = ConnectionError("redis is down")

    response = await upload(client)

    assert response.status_code == 201
    assert (await client.get(f"/files/{response.json()['id']}")).status_code == 200


async def test_empty_upload_is_400(client: httpx.AsyncClient):
    response = await upload(client, data=b"")

    assert response.status_code == 400
    assert response.json() == {"detail": "File is empty"}


async def test_oversized_upload_is_413(client: httpx.AsyncClient, scan_task: FakeTask):
    """A10: лимит применяется посреди приёма, задача не ставится."""
    response = await upload(client, name="big.bin", data=b"x" * (MAX_UPLOAD + 1))

    assert response.status_code == 413
    assert scan_task.calls == []


async def test_unknown_file_is_404(client: httpx.AsyncClient):
    response = await client.get("/files/no-such-id")

    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}


async def test_rename(client: httpx.AsyncClient):
    file_id = (await upload(client)).json()["id"]

    response = await client.patch(f"/files/{file_id}", json={"title": "renamed"})

    assert response.status_code == 200
    assert response.json()["title"] == "renamed"


async def test_rename_rejects_empty_title(client: httpx.AsyncClient):
    file_id = (await upload(client)).json()["id"]

    assert (await client.patch(f"/files/{file_id}", json={"title": ""})).status_code == 422


async def test_download(client: httpx.AsyncClient):
    file_id = (await upload(client)).json()["id"]

    response = await client.get(f"/files/{file_id}/download")

    assert response.status_code == 200
    assert response.content == SAMPLE_TXT
    assert response.headers["content-type"].startswith("text/plain")
    assert 'filename="sample.txt"' in response.headers["content-disposition"]


async def test_download_without_stored_file_is_404(client: httpx.AsyncClient, storage: LocalFileStorage):
    body = (await upload(client)).json()
    await storage.delete(f"{body['id']}.txt")

    response = await client.get(f"/files/{body['id']}/download")

    assert response.status_code == 404
    assert response.json() == {"detail": "Stored file not found"}


async def test_delete_file_with_alert_is_204(client: httpx.AsyncClient, session: AsyncSession):
    """A1: алерт больше не мешает удалению — он удаляется каскадом."""
    file_id = (await upload(client)).json()["id"]
    session.add(Alert(file_id=file_id, level="info", message="processed"))
    await session.commit()

    assert (await client.delete(f"/files/{file_id}")).status_code == 204
    assert (await client.get(f"/files/{file_id}")).status_code == 404
    assert (await client.get("/alerts")).json()["total"] == 0


async def test_delete_unknown_file_is_404(client: httpx.AsyncClient):
    assert (await client.delete("/files/no-such-id")).status_code == 404


async def test_files_are_paginated_newest_first(client: httpx.AsyncClient):
    ids = [(await upload(client, name=f"{i}.txt")).json()["id"] for i in range(3)]

    first = (await client.get("/files", params={"limit": 2})).json()
    second = (await client.get("/files", params={"limit": 2, "offset": 2})).json()

    assert first["total"] == 3
    assert (first["limit"], first["offset"]) == (2, 0)
    assert [item["id"] for item in first["items"]] + [item["id"] for item in second["items"]] == ids[::-1]


async def test_pagination_bounds_are_validated(client: httpx.AsyncClient):
    assert (await client.get("/files", params={"limit": 0})).status_code == 422
    assert (await client.get("/files", params={"limit": 1000})).status_code == 422
    assert (await client.get("/files", params={"offset": -1})).status_code == 422


async def test_alerts_page_shape(client: httpx.AsyncClient, service: FileService):
    body = (await upload(client)).json()
    await service.mark_processing(body["id"])
    await service.scan(body["id"])
    await service.extract_metadata(body["id"])
    await service.raise_alert(body["id"])

    response = await client.get("/alerts")

    assert response.status_code == 200
    page = response.json()
    assert page["total"] == 1
    assert page["items"][0]["file_id"] == body["id"]
    assert page["items"][0]["level"] == "info"

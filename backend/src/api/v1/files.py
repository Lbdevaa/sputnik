import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import FileResponse

from src.api.deps import FileServiceDep, PageDep
from src.schemas import FileItem, FileUpdate, Page
from src.storage import CHUNK_SIZE
from src.worker.tasks import scan_file_for_threats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["files"])


async def _iter_upload(upload_file: UploadFile) -> AsyncIterator[bytes]:
    while chunk := await upload_file.read(CHUNK_SIZE):
        yield chunk


@router.get("", response_model=Page[FileItem])
async def list_files(service: FileServiceDep, page: PageDep) -> Page[FileItem]:
    items, total = await service.list(limit=page.limit, offset=page.offset)
    return Page(items=items, total=total, limit=page.limit, offset=page.offset)


@router.post("", response_model=FileItem, status_code=status.HTTP_201_CREATED)
async def create_file(
    service: FileServiceDep,
    title: str = Form(...),
    file: UploadFile = File(...),
) -> FileItem:
    file_item = await service.upload(
        title=title,
        filename=file.filename or "",
        chunks=_iter_upload(file),
        declared_type=file.content_type,
    )

    try:
        scan_file_for_threats.delay(file_item.id)
    except Exception:
        # Загрузка уже состоялась и откатывать её из-за недоступного брокера нельзя:
        # раньше это давало клиенту 500 при успешно сохранённом файле (A7).
        # Файл остаётся в статусе uploaded, обработку можно запустить повторно.
        logger.exception("failed to enqueue scan", extra={"file_id": file_item.id})

    return file_item


@router.get("/{file_id}", response_model=FileItem)
async def get_file(file_id: str, service: FileServiceDep) -> FileItem:
    return await service.get(file_id)


@router.patch("/{file_id}", response_model=FileItem)
async def update_file(file_id: str, payload: FileUpdate, service: FileServiceDep) -> FileItem:
    return await service.rename(file_id=file_id, title=payload.title)


@router.get("/{file_id}/download")
async def download_file(file_id: str, service: FileServiceDep) -> FileResponse:
    file_item, path = await service.path_for_download(file_id)
    return FileResponse(
        path=path,
        media_type=file_item.mime_type,
        filename=file_item.original_name,
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: str, service: FileServiceDep) -> None:
    await service.delete(file_id)

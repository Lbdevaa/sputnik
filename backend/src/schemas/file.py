from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.domain.enums import ProcessingStatus, ScanStatus


class FileItem(BaseModel):
    """Представление файла для клиента.

    Отдельная схема, а не ORM-модель напрямую (Б6): статусы здесь — перечисления, так что
    их набор виден в OpenAPI, а изменение схемы базы не меняет контракт молча.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_name: str
    mime_type: str
    size: int
    processing_status: ProcessingStatus
    scan_status: ScanStatus | None
    scan_details: str | None
    metadata_json: dict | None
    requires_attention: bool
    created_at: datetime
    updated_at: datetime


class FileUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)

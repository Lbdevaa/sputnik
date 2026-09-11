from fastapi import APIRouter

from src.api.deps import AlertServiceDep, PageDep
from src.schemas import AlertItem, Page

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=Page[AlertItem])
async def list_alerts(service: AlertServiceDep, page: PageDep) -> Page[AlertItem]:
    items, total = await service.list(limit=page.limit, offset=page.offset)
    return Page(items=items, total=total, limit=page.limit, offset=page.offset)

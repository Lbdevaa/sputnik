from fastapi import APIRouter

from src.api.v1 import alerts, files

router = APIRouter()
router.include_router(files.router)
router.include_router(alerts.router)

__all__ = ["router"]

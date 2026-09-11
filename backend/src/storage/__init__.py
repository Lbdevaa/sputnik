from functools import lru_cache

from src.core.config import get_settings
from src.storage.base import FileStorage, SavedFile, StorageLimitExceeded
from src.storage.local import CHUNK_SIZE, HEAD_SIZE, LocalFileStorage


@lru_cache
def get_storage() -> FileStorage:
    return LocalFileStorage(get_settings().storage_dir)


__all__ = [
    "CHUNK_SIZE",
    "HEAD_SIZE",
    "FileStorage",
    "LocalFileStorage",
    "SavedFile",
    "StorageLimitExceeded",
    "get_storage",
]

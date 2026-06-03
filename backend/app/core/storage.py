from __future__ import annotations

from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class StorageService:
    """MinIO client wrapper. Injected as a FastAPI dependency so tests can override it."""

    def __init__(self) -> None:
        self._client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self._bucket = settings.MINIO_BUCKET

    def generate_upload_url(self, storage_key: str, expires_in: int) -> str:
        return self._client.presigned_put_object(
            bucket_name=self._bucket,
            object_name=storage_key,
            expires=timedelta(seconds=expires_in),
        )

    def generate_download_url(self, storage_key: str, expires_in: int) -> str:
        return self._client.presigned_get_object(
            bucket_name=self._bucket,
            object_name=storage_key,
            expires=timedelta(seconds=expires_in),
        )

    def delete_object(self, storage_key: str) -> None:
        try:
            self._client.remove_object(self._bucket, storage_key)
        except S3Error:
            pass  # Best-effort; object may already be absent


_instance: StorageService | None = None


def get_storage() -> StorageService:
    """FastAPI dependency. Returns a lazily-initialised singleton. Override in tests."""
    global _instance
    if _instance is None:
        _instance = StorageService()
    return _instance

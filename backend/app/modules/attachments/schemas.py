from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AttachmentUploadRequest(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int


class AttachmentUploadUrlResponse(BaseModel):
    upload_url: str
    storage_key: str
    expires_in: int


class AttachmentConfirmRequest(BaseModel):
    storage_key: str
    filename: str
    mime_type: str
    size_bytes: int


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    ticket_id: UUID
    uploaded_by: UUID
    filename: str
    storage_key: str
    mime_type: str
    size_bytes: int
    created_at: datetime


class AttachmentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AttachmentResponse]


class AttachmentDownloadUrlResponse(BaseModel):
    download_url: str
    expires_in: int

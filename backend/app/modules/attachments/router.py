from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_role_codes, get_current_user, get_db, require_permission
from app.core.permissions import TICKET_READ
from app.core.storage import StorageService, get_storage
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.schemas import (
    AttachmentConfirmRequest,
    AttachmentDownloadUrlResponse,
    AttachmentListResponse,
    AttachmentResponse,
    AttachmentUploadRequest,
    AttachmentUploadUrlResponse,
)
from app.modules.attachments.service import AttachmentService
from app.modules.tickets.repository import TicketObserverRepository, TicketRepository
from app.modules.timeline.repository import TicketEventRepository
from app.modules.timeline.service import TimelineService
from app.modules.users.repository import UserRepository

ticket_attachments_router = APIRouter(prefix="/tickets", tags=["attachments"])
attachments_router = APIRouter(prefix="/attachments", tags=["attachments"])


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
) -> AttachmentService:
    tid = current_user.tenant_id
    return AttachmentService(
        attachment_repo=AttachmentRepository(db, tid),
        ticket_repo=TicketRepository(db, tid),
        observer_repo=TicketObserverRepository(db, tid),
        timeline_svc=TimelineService(
            event_repo=TicketEventRepository(db, tid),
            ticket_repo=TicketRepository(db, tid),
            observer_repo=TicketObserverRepository(db, tid),
            user_repo=UserRepository(db, tid),
        ),
        storage_svc=storage,
    )


@ticket_attachments_router.post(
    "/{ticket_id}/attachments/upload-url",
    response_model=AttachmentUploadUrlResponse,
)
async def request_upload_url(
    ticket_id: UUID,
    body: AttachmentUploadRequest,
    service: AttachmentService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
) -> AttachmentUploadUrlResponse:
    return await service.request_upload_url(ticket_id, body, current_user_id=current_user.id)


@ticket_attachments_router.post(
    "/{ticket_id}/attachments/confirm",
    response_model=AttachmentResponse,
    status_code=201,
)
async def confirm_upload(
    ticket_id: UUID,
    body: AttachmentConfirmRequest,
    service: AttachmentService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
) -> AttachmentResponse:
    return await service.confirm_upload(ticket_id, body, current_user_id=current_user.id)


@ticket_attachments_router.get(
    "/{ticket_id}/attachments",
    response_model=AttachmentListResponse,
)
async def list_attachments(
    ticket_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    service: AttachmentService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
) -> AttachmentListResponse:
    return await service.list_attachments(
        ticket_id, current_user_id=current_user.id, page=page, page_size=page_size
    )


@attachments_router.get(
    "/{attachment_id}/download-url",
    response_model=AttachmentDownloadUrlResponse,
)
async def get_download_url(
    attachment_id: UUID,
    service: AttachmentService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
) -> AttachmentDownloadUrlResponse:
    return await service.get_download_url(attachment_id, current_user_id=current_user.id)


@attachments_router.delete("/{attachment_id}", status_code=204)
async def delete_attachment(
    attachment_id: UUID,
    service: AttachmentService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
    role_codes: list[str] = Depends(get_current_role_codes),
) -> None:
    await service.delete(attachment_id, current_user_id=current_user.id, role_codes=set(role_codes))

from __future__ import annotations

import os
import uuid as uuid_module
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError, UnprocessableError
from app.core.storage import StorageService
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.schemas import (
    AttachmentConfirmRequest,
    AttachmentDownloadUrlResponse,
    AttachmentListResponse,
    AttachmentResponse,
    AttachmentUploadRequest,
    AttachmentUploadUrlResponse,
)
from app.modules.tickets.repository import TicketObserverRepository, TicketRepository
from app.modules.timeline.service import TimelineService

_IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
_VIDEO_MIME_TYPES = frozenset({"video/mp4", "video/quicktime"})
_ADMIN_ROLES = frozenset({"admin", "supervisor"})


class AttachmentService:
    def __init__(
        self,
        attachment_repo: AttachmentRepository,
        ticket_repo: TicketRepository,
        observer_repo: TicketObserverRepository,
        timeline_svc: TimelineService,
        storage_svc: StorageService,
    ) -> None:
        self._attachments = attachment_repo
        self._tickets = ticket_repo
        self._observers = observer_repo
        self._timeline = timeline_svc
        self._storage = storage_svc

    # ── Upload URL ─────────────────────────────────────────────────────────────

    async def request_upload_url(
        self,
        ticket_id: UUID,
        data: AttachmentUploadRequest,
        current_user_id: UUID,
    ) -> AttachmentUploadUrlResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")
        await self._require_participant(ticket, current_user_id)
        self._validate_mime_and_size(data.mime_type, data.size_bytes)

        storage_key = _build_storage_key(self._attachments.tenant_id, ticket_id, data.filename)
        upload_url = self._storage.generate_upload_url(
            storage_key, settings.ATTACHMENT_UPLOAD_EXPIRE_SECONDS
        )
        return AttachmentUploadUrlResponse(
            upload_url=upload_url,
            storage_key=storage_key,
            expires_in=settings.ATTACHMENT_UPLOAD_EXPIRE_SECONDS,
        )

    # ── Confirm ────────────────────────────────────────────────────────────────

    async def confirm_upload(
        self,
        ticket_id: UUID,
        data: AttachmentConfirmRequest,
        current_user_id: UUID,
    ) -> AttachmentResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")
        await self._require_participant(ticket, current_user_id)
        self._validate_mime_and_size(data.mime_type, data.size_bytes)

        # Verify the key belongs to this tenant/ticket to prevent cross-context confirmation
        expected_prefix = f"{self._attachments.tenant_id}/{ticket_id}/"
        if not data.storage_key.startswith(expected_prefix):
            raise UnprocessableError("Chave de armazenamento inválida para este chamado.")

        attachment = await self._attachments.create(
            {
                "ticket_id": ticket_id,
                "uploaded_by": current_user_id,
                "filename": data.filename,
                "storage_key": data.storage_key,
                "mime_type": data.mime_type,
                "size_bytes": data.size_bytes,
            }
        )
        await self._timeline.record_event(
            event_type="attachment_added",
            ticket_id=ticket_id,
            actor_id=current_user_id,
            payload={"filename": data.filename, "attachment_id": str(attachment.id)},
        )
        return AttachmentResponse.model_validate(attachment)

    # ── List ───────────────────────────────────────────────────────────────────

    async def list_attachments(
        self,
        ticket_id: UUID,
        current_user_id: UUID,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> AttachmentListResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")
        await self._require_participant(ticket, current_user_id)

        offset = (page - 1) * page_size
        items = await self._attachments.list_for_ticket(ticket_id, offset=offset, limit=page_size)
        total = await self._attachments.count_for_ticket(ticket_id)
        return AttachmentListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AttachmentResponse.model_validate(a) for a in items],
        )

    # ── Download URL ───────────────────────────────────────────────────────────

    async def get_download_url(
        self,
        attachment_id: UUID,
        current_user_id: UUID,
    ) -> AttachmentDownloadUrlResponse:
        attachment = await self._attachments.get(attachment_id)
        if attachment is None:
            raise NotFoundError("Anexo não encontrado.")

        ticket = await self._tickets.get(attachment.ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")
        await self._require_participant(ticket, current_user_id)

        download_url = self._storage.generate_download_url(
            attachment.storage_key, settings.ATTACHMENT_DOWNLOAD_EXPIRE_SECONDS
        )
        return AttachmentDownloadUrlResponse(
            download_url=download_url,
            expires_in=settings.ATTACHMENT_DOWNLOAD_EXPIRE_SECONDS,
        )

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete(
        self,
        attachment_id: UUID,
        current_user_id: UUID,
        role_codes: set[str],
    ) -> None:
        attachment = await self._attachments.get(attachment_id)
        if attachment is None:
            raise NotFoundError("Anexo não encontrado.")

        ticket = await self._tickets.get(attachment.ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")

        is_admin = bool(role_codes & _ADMIN_ROLES)
        is_uploader = attachment.uploaded_by == current_user_id
        is_assignee = ticket.assignee_id == current_user_id

        if not (is_admin or is_uploader or is_assignee):
            raise ForbiddenError(
                "Exclusão permitida apenas para o autor do upload, responsável ou admin."
            )

        self._storage.delete_object(attachment.storage_key)
        await self._attachments.delete(attachment_id)

    # ── Helpers ────────────────────────────────────────────────────────────────

    async def _require_participant(self, ticket, user_id: UUID) -> None:
        """Raises ForbiddenError if the user is not a participant of the ticket."""
        if ticket.requester_id == user_id or ticket.assignee_id == user_id:
            return
        observer = await self._observers.find(ticket.id, user_id)
        if observer is not None:
            return
        raise ForbiddenError("Apenas participantes do chamado podem acessar os anexos.")

    @staticmethod
    def _validate_mime_and_size(mime_type: str, size_bytes: int) -> None:
        allowed = set(settings.ATTACHMENT_ALLOWED_MIME_TYPES)
        if mime_type not in allowed:
            raise UnprocessableError(
                f"Tipo MIME '{mime_type}' não é permitido. "
                f"Tipos aceitos: {', '.join(sorted(allowed))}."
            )
        if mime_type in _IMAGE_MIME_TYPES:
            max_bytes = settings.ATTACHMENT_MAX_IMAGE_BYTES
            if size_bytes > max_bytes:
                raise UnprocessableError(
                    f"Imagem excede o tamanho máximo de {max_bytes // 1024 // 1024} MB."
                )
        elif mime_type in _VIDEO_MIME_TYPES:
            max_bytes = settings.ATTACHMENT_MAX_VIDEO_BYTES
            if size_bytes > max_bytes:
                raise UnprocessableError(
                    f"Vídeo excede o tamanho máximo de {max_bytes // 1024 // 1024} MB."
                )


def _build_storage_key(tenant_id: UUID, ticket_id: UUID, filename: str) -> str:
    """Generates {tenant_id}/{ticket_id}/{uuid}.ext — ensures tenant isolation (INV-01)."""
    ext = os.path.splitext(filename)[1].lower()
    return f"{tenant_id}/{ticket_id}/{uuid_module.uuid4()}{ext}"

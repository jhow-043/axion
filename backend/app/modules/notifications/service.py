from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from app.modules.notifications.repository import (
    NotificationPreferenceRepository,
    NotificationRepository,
    RecipientQueryRepository,
)
from app.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferencesPatch,
    NotificationPreferencesResponse,
    NotificationResponse,
)

if TYPE_CHECKING:
    from app.modules.tickets.repository import TicketRepository

logger = logging.getLogger(__name__)

# Recipient resolution strategy per event type
_RECIPIENT_STRATEGY: dict[str, str] = {
    "ticket_created": "team_supervisors_and_admins",
    "ticket_assigned": "requester_and_observers",
    "ticket_status_changed": "requester_assignee_observers",
    "ticket_comment_added": "requester_assignee_observers",
    "ticket_resolved": "requester_and_observers",
    "ticket_validation_requested": "requester",
    "ticket_validation_approved": "assignee_and_observers",
    "ticket_validation_rejected": "assignee_and_observers",
    "ticket_closed": "requester_assignee_observers",
    "ticket_auto_closed": "all_participants_and_team_supervisors",
    "sla_attendance_at_risk": "assignee_and_team_supervisors",
    "sla_attendance_breached": "assignee_and_team_supervisors",
    "sla_resolution_at_risk": "assignee_and_team_supervisors",
    "sla_resolution_breached": "assignee_and_team_supervisors",
}

_SUPERVISOR_ROLES = ["supervisor", "admin"]

_TITLE_MAP: dict[str, str] = {
    "ticket_created": "Novo chamado aberto",
    "ticket_assigned": "Chamado atribuído",
    "ticket_status_changed": "Status do chamado alterado",
    "ticket_comment_added": "Novo comentário no chamado",
    "ticket_resolved": "Chamado solucionado",
    "ticket_validation_requested": "Validação de solução solicitada",
    "ticket_validation_approved": "Solução aprovada",
    "ticket_validation_rejected": "Solução rejeitada",
    "ticket_closed": "Chamado encerrado",
    "ticket_auto_closed": "Chamado encerrado automaticamente",
    "sla_attendance_at_risk": "SLA de atendimento em risco",
    "sla_attendance_breached": "SLA de atendimento vencido",
    "sla_resolution_at_risk": "SLA de resolução em risco",
    "sla_resolution_breached": "SLA de resolução vencido",
}


class NotificationService:
    """Real notification service (P14). Replaces stub used in P09, P12, P13.

    When instantiated with no repos (NotificationService()), behaves as a no-op stub
    so existing tests that don't set up notification infrastructure continue passing.
    """

    def __init__(
        self,
        notification_repo: NotificationRepository | None = None,
        preference_repo: NotificationPreferenceRepository | None = None,
        ticket_repo: TicketRepository | None = None,
        recipient_repo: RecipientQueryRepository | None = None,
        redis_url: str | None = None,
    ) -> None:
        self._notifications = notification_repo
        self._preferences = preference_repo
        self._tickets = ticket_repo
        self._recipients = recipient_repo
        self._redis_url = redis_url

    # ── Public API ────────────────────────────────────────────────────────────

    async def notify(
        self,
        *,
        event_type: str,
        ticket_id: UUID,
        actor_id: UUID | None,
        extra_recipients: list[UUID] | None = None,
        payload: dict | None = None,
    ) -> None:
        """Persist in-app notification, push via WebSocket, and enqueue email task.

        No-op when repos are not configured (stub mode for pre-P14 tests).
        """
        if self._notifications is None:
            return

        ticket = await self._tickets.get(ticket_id) if self._tickets else None

        recipients = await self._resolve_recipients(event_type, ticket_id, ticket)
        if extra_recipients:
            recipients.update(extra_recipients)
        # RN-07: do not notify the actor of their own action
        if actor_id:
            recipients.discard(actor_id)

        if not recipients:
            return

        title = _TITLE_MAP.get(event_type, "Notificação")
        body = _build_body(event_type, ticket)

        for recipient_id in recipients:
            await self._dispatch(
                recipient_id=recipient_id,
                ticket_id=ticket_id,
                event_type=event_type,
                title=title,
                body=body,
            )

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        is_read: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> NotificationListResponse:
        offset = (page - 1) * page_size
        items = await self._notifications.list_for_recipient(
            user_id, is_read=is_read, offset=offset, limit=page_size
        )
        total = await self._notifications.count_for_recipient(user_id, is_read=is_read)
        unread = await self._notifications.count_for_recipient(user_id, is_read=False)
        return NotificationListResponse(
            total=total,
            page=page,
            page_size=page_size,
            unread_count=unread,
            items=[NotificationResponse.model_validate(n) for n in items],
        )

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> NotificationResponse:
        from datetime import datetime

        from app.core.exceptions import ForbiddenError, NotFoundError

        notif = await self._notifications.get(notification_id)
        if notif is None:
            raise NotFoundError("Notificação não encontrada.")
        # 403 here is intentional — it's the user's own resource, not cross-tenant (ADR-0002)
        if notif.recipient_id != user_id:
            raise ForbiddenError("Você não pode marcar a notificação de outro usuário como lida.")
        if not notif.is_read:
            notif = await self._notifications.update(
                notification_id, {"is_read": True, "read_at": datetime.utcnow()}
            )
        return NotificationResponse.model_validate(notif)

    async def mark_all_read(self, user_id: UUID) -> int:
        return await self._notifications.mark_all_read(user_id)

    async def get_preferences(self, user_id: UUID) -> NotificationPreferencesResponse:
        prefs = await self._preferences.list_for_user(user_id)
        return NotificationPreferencesResponse(
            preferences=[NotificationPreferenceResponse.model_validate(p) for p in prefs]
        )

    async def update_preferences(
        self, user_id: UUID, body: NotificationPreferencesPatch
    ) -> NotificationPreferencesResponse:
        for item in body.preferences:
            await self._preferences.upsert(
                user_id=user_id,
                event_type=item.event_type,
                in_app_enabled=item.in_app_enabled,
                email_enabled=item.email_enabled,
            )
        return await self.get_preferences(user_id)

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _dispatch(
        self,
        *,
        recipient_id: UUID,
        ticket_id: UUID,
        event_type: str,
        title: str,
        body: str,
    ) -> None:
        pref = await self._preferences.find(recipient_id, event_type)
        # Default: all channels enabled when no preference row exists
        in_app_enabled = pref.in_app_enabled if pref else True
        email_enabled = pref.email_enabled if pref else True

        # RN-01: in-app always persisted regardless of email preference
        if in_app_enabled:
            notif = await self._notifications.create(
                {
                    "recipient_id": recipient_id,
                    "ticket_id": ticket_id,
                    "event_type": event_type,
                    "title": title,
                    "body": body,
                }
            )
            await self._push_ws(recipient_id, notif)

        if email_enabled:
            await self._enqueue_email(recipient_id, title, body)

    async def _push_ws(self, user_id: UUID, notif: object) -> None:
        try:
            from app.modules.notifications.websocket import publish_to_user

            data = {
                "type": "notification",
                "data": {
                    "id": str(notif.id),  # type: ignore[attr-defined]
                    "event_type": notif.event_type,  # type: ignore[attr-defined]
                    "title": notif.title,  # type: ignore[attr-defined]
                    "body": notif.body,  # type: ignore[attr-defined]
                    "ticket_id": str(notif.ticket_id) if notif.ticket_id else None,  # type: ignore[attr-defined]
                    "created_at": notif.created_at.isoformat(),  # type: ignore[attr-defined]
                },
            }
            await publish_to_user(user_id, data, self._redis_url)
        except Exception:
            logger.warning("WebSocket push failed for user %s", user_id, exc_info=True)

    async def _enqueue_email(self, user_id: UUID, title: str, body: str) -> None:
        if self._recipients is None:
            return
        email = await self._recipients.get_user_email(user_id)
        if not email:
            return
        try:
            from celery import current_app as celery

            celery.send_task(
                "app.modules.notifications.tasks.send_notification_email",
                args=[email, title, body],
            )
        except Exception:
            logger.warning("Failed to enqueue email for user %s", user_id, exc_info=True)

    async def _resolve_recipients(
        self, event_type: str, ticket_id: UUID, ticket: object | None
    ) -> set[UUID]:
        if self._recipients is None or ticket is None:
            return set()

        strategy = _RECIPIENT_STRATEGY.get(event_type, "")
        requester_id: UUID | None = getattr(ticket, "requester_id", None)
        assignee_id: UUID | None = getattr(ticket, "assignee_id", None)
        team_id: UUID | None = getattr(ticket, "team_id", None)

        recipients: set[UUID] = set()

        if strategy == "team_supervisors_and_admins":
            recipients.update(await self._get_supervisors(team_id))

        elif strategy == "requester_and_observers":
            if requester_id:
                recipients.add(requester_id)
            observers = await self._recipients.get_observer_user_ids(ticket_id)
            recipients.update(observers)

        elif strategy == "requester_assignee_observers":
            if requester_id:
                recipients.add(requester_id)
            if assignee_id:
                recipients.add(assignee_id)
            observers = await self._recipients.get_observer_user_ids(ticket_id)
            recipients.update(observers)

        elif strategy == "requester":
            if requester_id:
                recipients.add(requester_id)

        elif strategy == "assignee_and_observers":
            if assignee_id:
                recipients.add(assignee_id)
            observers = await self._recipients.get_observer_user_ids(ticket_id)
            recipients.update(observers)

        elif strategy == "all_participants_and_team_supervisors":
            if requester_id:
                recipients.add(requester_id)
            if assignee_id:
                recipients.add(assignee_id)
            observers = await self._recipients.get_observer_user_ids(ticket_id)
            recipients.update(observers)
            recipients.update(await self._get_supervisors(team_id))

        elif strategy == "assignee_and_team_supervisors":
            if assignee_id:
                recipients.add(assignee_id)
            recipients.update(await self._get_supervisors(team_id))

        return recipients

    async def _get_supervisors(self, team_id: UUID | None) -> list[UUID]:
        if self._recipients is None:
            return []
        if team_id:
            return await self._recipients.get_team_users_by_role_codes(team_id, _SUPERVISOR_ROLES)
        return await self._recipients.get_users_by_role_codes(_SUPERVISOR_ROLES)


def _build_body(event_type: str, ticket: object | None) -> str:
    ticket_title = getattr(ticket, "title", "chamado") if ticket else "chamado"
    messages = {
        "ticket_created": f"O {ticket_title!r} foi aberto.",
        "ticket_assigned": f"O {ticket_title!r} foi assumido.",
        "ticket_status_changed": f"O status de {ticket_title!r} foi alterado.",
        "ticket_comment_added": f"Novo comentário em {ticket_title!r}.",
        "ticket_resolved": f"{ticket_title!r} foi solucionado e aguarda validação.",
        "ticket_validation_requested": f"Sua validação é necessária em {ticket_title!r}.",
        "ticket_validation_approved": f"A solução de {ticket_title!r} foi aprovada.",
        "ticket_validation_rejected": f"A solução de {ticket_title!r} foi rejeitada.",
        "ticket_closed": f"{ticket_title!r} foi encerrado.",
        "ticket_auto_closed": f"{ticket_title!r} foi encerrado automaticamente por inatividade.",
        "sla_attendance_at_risk": (
            f"O SLA de atendimento de {ticket_title!r} está próximo do vencimento."
        ),
        "sla_attendance_breached": f"O SLA de atendimento de {ticket_title!r} foi violado.",
        "sla_resolution_at_risk": (
            f"O SLA de resolução de {ticket_title!r} está próximo do vencimento."
        ),
        "sla_resolution_breached": f"O SLA de resolução de {ticket_title!r} foi violado.",
    }
    return messages.get(event_type, f"Evento {event_type!r} em {ticket_title!r}.")


def build_notification_service(
    db: object, tenant_id: UUID, redis_url: str | None = None
) -> NotificationService:
    """Factory used by routers and Celery tasks to create a fully-wired NotificationService."""
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.modules.tickets.repository import TicketRepository

    session: AsyncSession = db  # type: ignore[assignment]

    return NotificationService(
        notification_repo=NotificationRepository(session, tenant_id),
        preference_repo=NotificationPreferenceRepository(session, tenant_id),
        ticket_repo=TicketRepository(session, tenant_id),
        recipient_repo=RecipientQueryRepository(session, tenant_id),
        redis_url=redis_url,
    )

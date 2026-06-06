from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.modules.catalog.repository import StatusRepository
from app.modules.closures.repository import TenantSettingsRepository, ValidationRepository
from app.modules.closures.schemas import (
    SolutionSummary,
    TenantSettingsPatch,
    TenantSettingsResponse,
    UserSummary,
    ValidationReject,
    ValidationResponse,
)
from app.modules.notifications.service import NotificationService
from app.modules.tickets.repository import SolutionRepository, TicketRepository
from app.modules.timeline.service import TimelineService
from app.modules.users.repository import UserRepository


class ClosureService:
    def __init__(
        self,
        validation_repo: ValidationRepository,
        settings_repo: TenantSettingsRepository,
        ticket_repo: TicketRepository,
        solution_repo: SolutionRepository,
        status_repo: StatusRepository,
        user_repo: UserRepository,
        timeline_svc: TimelineService,
        notification_svc: NotificationService,
    ) -> None:
        self._validations = validation_repo
        self._settings = settings_repo
        self._tickets = ticket_repo
        self._solutions = solution_repo
        self._statuses = status_repo
        self._users = user_repo
        self._timeline = timeline_svc
        self._notifications = notification_svc

    # ── Called by TicketService on resolve ────────────────────────────────────

    async def create_validation(self, ticket_id: UUID, requester_id: UUID) -> None:
        settings = await self._settings.get_or_create_defaults()
        expires_at = datetime.utcnow() + timedelta(days=settings.auto_close_days)
        await self._validations.create(
            {
                "ticket_id": ticket_id,
                "requester_id": requester_id,
                "status": "pending",
                "expires_at": expires_at,
            }
        )

    # ── Validation status ─────────────────────────────────────────────────────

    async def get_validation(self, ticket_id: UUID) -> ValidationResponse:
        validation = await self._validations.find_by_ticket(ticket_id)
        if validation is None:
            raise NotFoundError("Validação não encontrada para este chamado.")
        solution = await self._solutions.find_by_ticket(ticket_id)
        solution_summary = await self._build_solution_summary(solution) if solution else None
        return self._build_response(validation, solution_summary)

    async def approve(self, ticket_id: UUID, actor_id: UUID) -> ValidationResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")

        validation = await self._validations.find_by_ticket(ticket_id)
        if validation is None:
            raise NotFoundError("Validação não encontrada para este chamado.")

        self._check_requester(validation, actor_id)
        self._check_pending(validation)

        # SELECT FOR UPDATE to prevent double-close race condition
        locked = await self._validations.get_with_lock(validation.id)
        if locked is None or locked.status != "pending":
            raise BusinessRuleError("Esta validação já foi respondida.")

        await self._close_ticket(ticket_id, validation.id, actor_id, method="manual")
        return await self.get_validation(ticket_id)

    async def reject(
        self, ticket_id: UUID, data: ValidationReject, actor_id: UUID
    ) -> ValidationResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")

        validation = await self._validations.find_by_ticket(ticket_id)
        if validation is None:
            raise NotFoundError("Validação não encontrada para este chamado.")

        self._check_requester(validation, actor_id)
        self._check_pending(validation)

        locked = await self._validations.get_with_lock(validation.id)
        if locked is None or locked.status != "pending":
            raise BusinessRuleError("Esta validação já foi respondida.")

        await self._reopen_ticket(ticket_id, validation.id, actor_id, data.rejection_reason)
        return await self.get_validation(ticket_id)

    # ── Settings ──────────────────────────────────────────────────────────────

    async def get_settings(self) -> TenantSettingsResponse:
        obj = await self._settings.get_or_create_defaults()
        return TenantSettingsResponse.model_validate(obj)

    async def update_settings(
        self, data: TenantSettingsPatch, actor_id: UUID
    ) -> TenantSettingsResponse:
        obj = await self._settings.update(
            {"auto_close_days": data.auto_close_days, "updated_by": actor_id}
        )
        return TenantSettingsResponse.model_validate(obj)

    # ── Auto-close sweep (called by Celery per tenant) ────────────────────────

    async def sweep_auto_close(self) -> None:
        now = datetime.utcnow()
        expired = await self._validations.list_expired_pending(now)
        for validation in expired:
            # idempotent: re-check status after lock
            locked = await self._validations.get_with_lock(validation.id)
            if locked is None or locked.status != "pending":
                continue
            await self._close_ticket(locked.ticket_id, locked.id, actor_id=None, method="auto")

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _check_requester(validation, actor_id: UUID) -> None:
        # Rule 2 of spec: only the requester can approve or reject
        if validation.requester_id != actor_id:
            raise ForbiddenError("Apenas o solicitante pode validar a solução.")

    @staticmethod
    def _check_pending(validation) -> None:
        if validation.status != "pending":
            raise BusinessRuleError("Esta validação já foi respondida.")

    async def _close_ticket(
        self, ticket_id: UUID, validation_id: UUID, actor_id: UUID | None, method: str
    ) -> None:
        now = datetime.utcnow()
        closed_status = await self._statuses.find_by_code("closed")
        if closed_status is None:
            raise BusinessRuleError("Status 'closed' não configurado para este tenant.")

        await self._validations.update(
            validation_id,
            {"status": "approved", "responded_at": now, "responded_by": actor_id},
        )
        await self._tickets.update(ticket_id, {"status_id": closed_status.id, "closed_at": now})
        await self._timeline.record_event(
            event_type="ticket_closed",
            ticket_id=ticket_id,
            actor_id=actor_id,
            payload={"method": method},
        )
        await self._notifications.notify(
            event_type="ticket_closed",
            ticket_id=ticket_id,
            actor_id=actor_id,
        )

    async def _reopen_ticket(
        self, ticket_id: UUID, validation_id: UUID, actor_id: UUID, rejection_reason: str
    ) -> None:
        now = datetime.utcnow()
        in_progress_status = await self._statuses.find_by_code("in_progress")
        if in_progress_status is None:
            raise BusinessRuleError("Status 'in_progress' não configurado para este tenant.")

        await self._validations.update(
            validation_id,
            {
                "status": "rejected",
                "responded_at": now,
                "responded_by": actor_id,
                "rejection_reason": rejection_reason,
            },
        )
        await self._tickets.update(
            ticket_id,
            {"status_id": in_progress_status.id, "resolved_at": None},
        )
        await self._timeline.record_event(
            event_type="ticket_reopened",
            ticket_id=ticket_id,
            actor_id=actor_id,
            payload={"rejection_reason": rejection_reason},
        )
        await self._notifications.notify(
            event_type="ticket_reopened",
            ticket_id=ticket_id,
            actor_id=actor_id,
        )

    async def _build_solution_summary(self, solution) -> SolutionSummary | None:
        if solution is None:
            return None
        resolver = await self._users.get(solution.resolved_by)
        resolver_summary = (
            UserSummary(id=resolver.id, name=resolver.name)
            if resolver
            else UserSummary(id=solution.resolved_by, name="—")
        )
        return SolutionSummary(
            description=solution.description,
            resolved_by=resolver_summary,
            resolved_at=solution.resolved_at,
        )

    @staticmethod
    def _build_response(validation, solution_summary: SolutionSummary | None) -> ValidationResponse:
        now = datetime.utcnow()
        delta = validation.expires_at - now
        days_remaining = max(0, delta.days)
        return ValidationResponse(
            id=validation.id,
            ticket_id=validation.ticket_id,
            status=validation.status,
            expires_at=validation.expires_at,
            days_remaining=days_remaining,
            responded_at=validation.responded_at,
            rejection_reason=validation.rejection_reason,
            solution=solution_summary,
        )

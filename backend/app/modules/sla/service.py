from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.modules.audit.service import AuditService

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.modules.notifications.service import NotificationService
from app.modules.sla.repository import SlaPauseRepository, SlaPolicyRepository, SlaTrackerRepository
from app.modules.sla.schemas import (
    SlaAttendanceDetail,
    SlaPolicyCreate,
    SlaPolicyListResponse,
    SlaPolicyPatch,
    SlaPolicyResponse,
    SlaResolutionDetail,
    SlaTicketResponse,
)
from app.modules.tickets.repository import TicketRepository
from app.modules.timeline.service import TimelineService

logger = logging.getLogger(__name__)


class SlaService:
    def __init__(
        self,
        policy_repo: SlaPolicyRepository,
        tracker_repo: SlaTrackerRepository,
        pause_repo: SlaPauseRepository,
        ticket_repo: TicketRepository,
        timeline_svc: TimelineService | None = None,
        notification_svc: NotificationService | None = None,
        audit_svc: AuditService | None = None,
        actor_id: UUID | None = None,
    ) -> None:
        self._policies = policy_repo
        self._trackers = tracker_repo
        self._pauses = pause_repo
        self._tickets = ticket_repo
        self._timeline = timeline_svc
        self._notifications = notification_svc
        self._audit = audit_svc
        self._actor_id = actor_id

    # ── Policy CRUD ───────────────────────────────────────────────────────────────

    async def create_policy(self, data: SlaPolicyCreate) -> SlaPolicyResponse:
        existing = await self._policies.find_duplicate(
            ticket_type=data.ticket_type,
            priority_id=data.priority_id,
            team_id=data.team_id,
        )
        if existing is not None:
            raise BusinessRuleError(
                "Já existe uma política ativa com este tipo de chamado, prioridade e equipe."
            )
        policy = await self._policies.create(data.model_dump())
        if self._audit:
            await self._audit.log(
                action="sla_policy.created",
                entity_type="SlaPolicy",
                entity_id=policy.id,
                actor_id=self._actor_id,
                after=data.model_dump(mode="json"),
            )
        return SlaPolicyResponse.model_validate(policy)

    async def list_policies(self, *, page: int, page_size: int) -> SlaPolicyListResponse:
        offset = (page - 1) * page_size
        items = await self._policies.list(offset=offset, limit=page_size)
        total = await self._policies.count()
        return SlaPolicyListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[SlaPolicyResponse.model_validate(p) for p in items],
        )

    async def get_policy(self, policy_id: UUID) -> SlaPolicyResponse:
        policy = await self._policies.get(policy_id)
        if policy is None:
            raise NotFoundError("Política de SLA não encontrada.")
        return SlaPolicyResponse.model_validate(policy)

    async def update_policy(self, policy_id: UUID, data: SlaPolicyPatch) -> SlaPolicyResponse:
        policy = await self._policies.get(policy_id)
        if policy is None:
            raise NotFoundError("Política de SLA não encontrada.")
        before_snapshot = SlaPolicyResponse.model_validate(policy).model_dump(mode="json")
        updates = data.model_dump(exclude_unset=True)
        updated = await self._policies.update(policy_id, updates)
        if self._audit:
            after_snapshot = SlaPolicyResponse.model_validate(updated).model_dump(mode="json")
            await self._audit.log(
                action="sla_policy.updated",
                entity_type="SlaPolicy",
                entity_id=policy_id,
                actor_id=self._actor_id,
                before=before_snapshot,
                after=after_snapshot,
            )
        return SlaPolicyResponse.model_validate(updated)

    async def deactivate_policy(self, policy_id: UUID) -> SlaPolicyResponse:
        policy = await self._policies.get(policy_id)
        if policy is None:
            raise NotFoundError("Política de SLA não encontrada.")
        before_snapshot = SlaPolicyResponse.model_validate(policy).model_dump(mode="json")
        updated = await self._policies.update(policy_id, {"is_active": False})
        if self._audit:
            after_snapshot = SlaPolicyResponse.model_validate(updated).model_dump(mode="json")
            await self._audit.log(
                action="sla_policy.deactivated",
                entity_type="SlaPolicy",
                entity_id=policy_id,
                actor_id=self._actor_id,
                before=before_snapshot,
                after=after_snapshot,
            )
        return SlaPolicyResponse.model_validate(updated)

    # ── SLA Lifecycle ─────────────────────────────────────────────────────────────

    async def initialize_tracker(
        self,
        *,
        ticket_id: UUID,
        ticket_type: str,
        priority_id: UUID,
        team_id: UUID | None,
        created_at: datetime,
    ) -> None:
        """Called on ticket creation. No tracker created if no policy applies (spec P12 RN)."""
        policy = await self._policies.find_applicable(
            ticket_type=ticket_type,
            priority_id=priority_id,
            team_id=team_id,
        )
        if policy is None:
            logger.warning("No SLA policy for ticket %s — tracker skipped", ticket_id)
            return

        created_naive = _naive(created_at)
        attendance_due_at = created_naive + timedelta(minutes=policy.attendance_minutes)
        await self._trackers.create(
            {
                "ticket_id": ticket_id,
                "policy_id": policy.id,
                "attendance_due_at": attendance_due_at,
                "attendance_status": "running",
                "resolution_status": "running",
                "total_paused_minutes": 0,
            }
        )

    async def on_ticket_assigned(self, *, ticket_id: UUID, assigned_at: datetime) -> None:
        """Close attendance SLA; calculate and start resolution SLA."""
        tracker = await self._trackers.find_by_ticket(ticket_id)
        if tracker is None or tracker.attendance_status != "running":
            return

        policy = await self._policies.get(tracker.policy_id)
        if policy is None:
            return

        assigned_naive = _naive(assigned_at)
        att_status = (
            "met"
            if tracker.attendance_due_at and assigned_naive <= tracker.attendance_due_at
            else "breached"
        )
        resolution_due_at = assigned_naive + timedelta(minutes=policy.resolution_minutes)
        await self._trackers.update(
            tracker.id,
            {
                "attendance_status": att_status,
                "attendance_met_at": assigned_naive,
                "resolution_due_at": resolution_due_at,
            },
        )

    async def on_ticket_pending(self, *, ticket_id: UUID, paused_at: datetime) -> None:
        """Pause resolution SLA; create sla_pause record."""
        tracker = await self._trackers.find_by_ticket(ticket_id)
        if tracker is None or tracker.resolution_status != "running":
            return

        await self._pauses.create({"tracker_id": tracker.id, "paused_at": _naive(paused_at)})
        await self._trackers.update(tracker.id, {"resolution_status": "paused"})

    async def on_ticket_resumed(self, *, ticket_id: UUID, resumed_at: datetime) -> None:
        """Close open pause, accumulate paused minutes, extend resolution deadline."""
        tracker = await self._trackers.find_by_ticket(ticket_id)
        if tracker is None or tracker.resolution_status != "paused":
            return

        pause = await self._pauses.find_open_pause(tracker.id)
        if pause is None:
            return

        resumed_naive = _naive(resumed_at)
        elapsed_minutes = max(0, int((resumed_naive - pause.paused_at).total_seconds() / 60))
        await self._pauses.update(
            pause.id, {"resumed_at": resumed_naive, "minutes": elapsed_minutes}
        )

        new_total = tracker.total_paused_minutes + elapsed_minutes
        new_due_at = (
            tracker.resolution_due_at + timedelta(minutes=elapsed_minutes)
            if tracker.resolution_due_at
            else None
        )
        await self._trackers.update(
            tracker.id,
            {
                "total_paused_minutes": new_total,
                "resolution_due_at": new_due_at,
                "resolution_status": "running",
            },
        )

    async def on_ticket_resolved(self, *, ticket_id: UUID, resolved_at: datetime) -> None:
        """Close resolution SLA as met or breached."""
        tracker = await self._trackers.find_by_ticket(ticket_id)
        if tracker is None or tracker.resolution_status not in ("running", "paused"):
            return

        resolved_naive = _naive(resolved_at)
        res_status = (
            "met"
            if tracker.resolution_due_at and resolved_naive <= tracker.resolution_due_at
            else "breached"
        )
        await self._trackers.update(
            tracker.id,
            {"resolution_status": res_status, "resolution_met_at": resolved_naive},
        )

    async def get_ticket_sla(self, ticket_id: UUID) -> SlaTicketResponse:
        tracker = await self._trackers.find_by_ticket(ticket_id)
        if tracker is None:
            raise NotFoundError("SLA não configurado para este chamado.")

        now = _naive_utcnow()
        elapsed_min: int | None = None
        remaining_min: int | None = None

        if tracker.resolution_due_at and tracker.resolution_status == "running":
            remaining_seconds = (tracker.resolution_due_at - now).total_seconds()
            remaining_min = max(0, int(remaining_seconds / 60))

            policy = await self._policies.get(tracker.policy_id)
            if policy:
                net_minutes = policy.resolution_minutes - tracker.total_paused_minutes
                origin = tracker.resolution_due_at - timedelta(minutes=net_minutes)
                elapsed_min = max(0, int((now - origin).total_seconds() / 60))

        return SlaTicketResponse(
            policy_id=tracker.policy_id,
            attendance=SlaAttendanceDetail(
                due_at=tracker.attendance_due_at,
                status=tracker.attendance_status,
                met_at=tracker.attendance_met_at,
            ),
            resolution=SlaResolutionDetail(
                due_at=tracker.resolution_due_at,
                status=tracker.resolution_status,
                met_at=tracker.resolution_met_at,
                elapsed_minutes=elapsed_min,
                remaining_minutes=remaining_min,
                paused_minutes=tracker.total_paused_minutes,
            ),
        )

    # ── Sweep jobs ────────────────────────────────────────────────────────────────

    async def sweep_breaches(self) -> None:
        """Mark overdue SLAs as breached and record timeline events. Idempotent."""
        now = _naive_utcnow()
        trackers = await self._trackers.list_overdue()

        for tracker in trackers:
            updates: dict = {}
            events: list[str] = []

            if (
                tracker.attendance_status == "running"
                and tracker.attendance_due_at
                and now > tracker.attendance_due_at
            ):
                updates["attendance_status"] = "breached"
                events.append("sla_attendance_breached")

            if (
                tracker.resolution_status == "running"
                and tracker.resolution_due_at
                and now > tracker.resolution_due_at
            ):
                updates["resolution_status"] = "breached"
                events.append("sla_resolution_breached")

            if not updates:
                continue

            await self._trackers.update(tracker.id, updates)

            for event_type in events:
                if self._timeline:
                    await self._timeline.record_event(
                        event_type=event_type,
                        ticket_id=tracker.ticket_id,
                        actor_id=None,
                    )
                if self._notifications:
                    await self._notifications.notify(
                        event_type=event_type,
                        ticket_id=tracker.ticket_id,
                        actor_id=None,
                    )

    async def sweep_alerts(self) -> None:
        """Send threshold alerts when SLA nears expiration. Idempotent via alert_sent flags."""
        now = _naive_utcnow()
        trackers = await self._trackers.list_running()

        for tracker in trackers:
            policy = await self._policies.get(tracker.policy_id)
            if policy is None:
                continue

            updates: dict = {}

            if (
                tracker.attendance_status == "running"
                and not tracker.attendance_alert_sent
                and tracker.attendance_due_at
            ):
                pct = _elapsed_pct(
                    due_at=tracker.attendance_due_at,
                    total_minutes=policy.attendance_minutes,
                    now=now,
                )
                if pct >= policy.alert_threshold_pct:
                    updates["attendance_alert_sent"] = True
                    if self._notifications:
                        await self._notifications.notify(
                            event_type="sla_attendance_alert",
                            ticket_id=tracker.ticket_id,
                            actor_id=None,
                        )

            if (
                tracker.resolution_status == "running"
                and not tracker.resolution_alert_sent
                and tracker.resolution_due_at
            ):
                net_minutes = policy.resolution_minutes - tracker.total_paused_minutes
                pct = _elapsed_pct(
                    due_at=tracker.resolution_due_at,
                    total_minutes=max(1, net_minutes),
                    now=now,
                )
                if pct >= policy.alert_threshold_pct:
                    updates["resolution_alert_sent"] = True
                    if self._notifications:
                        await self._notifications.notify(
                            event_type="sla_resolution_alert",
                            ticket_id=tracker.ticket_id,
                            actor_id=None,
                        )

            if updates:
                await self._trackers.update(tracker.id, updates)


def _naive_utcnow() -> datetime:
    """Naive UTC now — compatible with SQLite (aiosqlite returns naive datetimes)."""
    return datetime.utcnow()


def _naive(dt: datetime) -> datetime:
    """Strip timezone info for SQLite-compatible storage and comparison."""
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


def _elapsed_pct(*, due_at: datetime, total_minutes: int, now: datetime) -> float:
    origin = due_at - timedelta(minutes=total_minutes)
    elapsed = (now - origin).total_seconds() / 60
    return (elapsed / total_minutes) * 100

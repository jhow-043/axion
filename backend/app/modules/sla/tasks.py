from __future__ import annotations

import asyncio
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


def _get_celery_app():
    from app.core.celery_app import celery_app

    return celery_app


def breach_sweep() -> None:
    """Celery task: mark SLA trackers as breached when their deadlines have passed.
    Registered via celery_app.task decorator after import to avoid circular deps."""
    asyncio.run(_breach_sweep_async())


def alert_sweep() -> None:
    """Celery task: send threshold alerts when SLA nears expiration.
    Idempotent: alert_sent flags prevent duplicate notifications."""
    asyncio.run(_alert_sweep_async())


async def _get_active_tenant_ids() -> list[UUID]:
    """Returns all active tenant IDs. Not tenant-scoped — ADR-0004 sweep pattern."""
    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.modules.tenants.models import Tenant

    async with get_session_factory()() as session:
        result = await session.execute(select(Tenant.id).where(Tenant.is_active.is_(True)))
        return list(result.scalars().all())


async def _breach_sweep_async() -> None:
    from app.db.session import get_session_factory
    from app.modules.notifications.service import build_notification_service
    from app.modules.sla.repository import (
        SlaPauseRepository,
        SlaPolicyRepository,
        SlaTrackerRepository,
    )
    from app.modules.sla.service import SlaService
    from app.modules.tickets.repository import TicketObserverRepository, TicketRepository
    from app.modules.timeline.repository import TicketEventRepository
    from app.modules.timeline.service import TimelineService
    from app.modules.users.repository import UserRepository
    from app.shared.tenant_context import tenant_context

    tenant_ids = await _get_active_tenant_ids()
    for tenant_id in tenant_ids:
        # INV-04: configure ContextVar explicitly per tenant before any repository access
        with tenant_context(tenant_id):
            async with get_session_factory()() as session:
                svc = SlaService(
                    policy_repo=SlaPolicyRepository(session, tenant_id),
                    tracker_repo=SlaTrackerRepository(session, tenant_id),
                    pause_repo=SlaPauseRepository(session, tenant_id),
                    ticket_repo=TicketRepository(session, tenant_id),
                    timeline_svc=TimelineService(
                        event_repo=TicketEventRepository(session, tenant_id),
                        ticket_repo=TicketRepository(session, tenant_id),
                        observer_repo=TicketObserverRepository(session, tenant_id),
                        user_repo=UserRepository(session, tenant_id),
                    ),
                    notification_svc=build_notification_service(session, tenant_id),
                )
                try:
                    await svc.sweep_breaches()
                    await session.commit()
                except Exception:
                    logger.exception("Breach sweep failed for tenant %s", tenant_id)
                    await session.rollback()


async def _alert_sweep_async() -> None:
    from app.db.session import get_session_factory
    from app.modules.notifications.service import build_notification_service
    from app.modules.sla.repository import (
        SlaPauseRepository,
        SlaPolicyRepository,
        SlaTrackerRepository,
    )
    from app.modules.sla.service import SlaService
    from app.modules.tickets.repository import TicketRepository
    from app.shared.tenant_context import tenant_context

    tenant_ids = await _get_active_tenant_ids()
    for tenant_id in tenant_ids:
        with tenant_context(tenant_id):
            async with get_session_factory()() as session:
                svc = SlaService(
                    policy_repo=SlaPolicyRepository(session, tenant_id),
                    tracker_repo=SlaTrackerRepository(session, tenant_id),
                    pause_repo=SlaPauseRepository(session, tenant_id),
                    ticket_repo=TicketRepository(session, tenant_id),
                    notification_svc=build_notification_service(session, tenant_id),
                )
                try:
                    await svc.sweep_alerts()
                    await session.commit()
                except Exception:
                    logger.exception("Alert sweep failed for tenant %s", tenant_id)
                    await session.rollback()


# Register with Celery after defining functions to avoid circular import at module load
def _register_tasks() -> None:
    app = _get_celery_app()
    app.task(name="app.modules.sla.tasks.breach_sweep")(breach_sweep)
    app.task(name="app.modules.sla.tasks.alert_sweep")(alert_sweep)


_register_tasks()

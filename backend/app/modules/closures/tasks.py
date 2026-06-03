from __future__ import annotations

import asyncio
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


def auto_close_sweep() -> None:
    """Celery task: close tickets whose validation deadline has expired.
    Idempotent — re-checks status under lock before closing."""
    asyncio.run(_auto_close_sweep_async())


async def _get_active_tenant_ids() -> list[UUID]:
    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.modules.tenants.models import Tenant

    async with get_session_factory()() as session:
        result = await session.execute(select(Tenant.id).where(Tenant.is_active.is_(True)))
        return list(result.scalars().all())


async def _auto_close_sweep_async() -> None:
    from app.db.session import get_session_factory
    from app.modules.catalog.repository import StatusRepository
    from app.modules.closures.repository import TenantSettingsRepository, ValidationRepository
    from app.modules.closures.service import ClosureService
    from app.modules.notifications.service import NotificationService
    from app.modules.tickets.repository import (
        SolutionRepository,
        TicketObserverRepository,
        TicketRepository,
    )
    from app.modules.timeline.repository import TicketEventRepository
    from app.modules.timeline.service import TimelineService
    from app.modules.users.repository import UserRepository
    from app.shared.tenant_context import tenant_context

    tenant_ids = await _get_active_tenant_ids()
    for tenant_id in tenant_ids:
        # INV-04: configure ContextVar explicitly per tenant before any repository access
        with tenant_context(tenant_id):
            async with get_session_factory()() as session:
                svc = ClosureService(
                    validation_repo=ValidationRepository(session, tenant_id),
                    settings_repo=TenantSettingsRepository(session, tenant_id),
                    ticket_repo=TicketRepository(session, tenant_id),
                    solution_repo=SolutionRepository(session, tenant_id),
                    status_repo=StatusRepository(session, tenant_id),
                    user_repo=UserRepository(session, tenant_id),
                    timeline_svc=TimelineService(
                        event_repo=TicketEventRepository(session, tenant_id),
                        ticket_repo=TicketRepository(session, tenant_id),
                        observer_repo=TicketObserverRepository(session, tenant_id),
                        user_repo=UserRepository(session, tenant_id),
                    ),
                    notification_svc=NotificationService(),
                )
                try:
                    await svc.sweep_auto_close()
                    await session.commit()
                except Exception:
                    logger.exception("Auto-close sweep failed for tenant %s", tenant_id)
                    await session.rollback()


def _register_tasks() -> None:
    from app.core.celery_app import celery_app

    celery_app.task(name="app.modules.closures.tasks.auto_close_sweep")(auto_close_sweep)


_register_tasks()

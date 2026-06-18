from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.users.models import User


@dataclass
class GlobalStats:
    total_companies: int
    active_companies: int
    suspended_companies: int
    total_users: int
    total_tickets: int


@dataclass
class CompanyRow:
    id: UUID
    name: str
    slug: str
    is_active: bool
    is_system: bool
    created_at: datetime
    user_count: int
    ticket_count: int


class DashboardRepository:
    """Cross-tenant aggregation queries for the SaaS Admin dashboard.
    Operates on the global tenants table — not scoped by tenant_id (ADR-0001 exception)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_global_stats(self) -> GlobalStats:
        tenant_q = await self.session.execute(
            select(
                func.count().label("total"),
                func.sum(Tenant.is_active.cast(Integer)).label("active"),
            ).where(Tenant.deleted_at.is_(None), Tenant.is_system.is_(False))
        )
        row = tenant_q.one()
        total = row.total or 0
        active = int(row.active or 0)

        users_q = await self.session.execute(
            select(func.count())
            .select_from(User)
            .join(Tenant, User.tenant_id == Tenant.id)
            .where(
                Tenant.deleted_at.is_(None),
                Tenant.is_system.is_(False),
            )
        )
        total_users = users_q.scalar_one() or 0

        tickets_q = await self.session.execute(
            select(func.count())
            .select_from(Ticket)
            .join(Tenant, Ticket.tenant_id == Tenant.id)
            .where(
                Tenant.deleted_at.is_(None),
                Tenant.is_system.is_(False),
            )
        )
        total_tickets = tickets_q.scalar_one() or 0

        return GlobalStats(
            total_companies=total,
            active_companies=active,
            suspended_companies=total - active,
            total_users=total_users,
            total_tickets=total_tickets,
        )

    async def list_company_rows(self, *, offset: int = 0, limit: int = 20) -> list[CompanyRow]:
        users_sub = (
            select(User.tenant_id, func.count().label("user_count"))
            .group_by(User.tenant_id)
            .subquery()
        )
        tickets_sub = (
            select(Ticket.tenant_id, func.count().label("ticket_count"))
            .group_by(Ticket.tenant_id)
            .subquery()
        )
        stmt = (
            select(
                Tenant.id,
                Tenant.name,
                Tenant.slug,
                Tenant.is_active,
                Tenant.is_system,
                Tenant.created_at,
                func.coalesce(users_sub.c.user_count, 0).label("user_count"),
                func.coalesce(tickets_sub.c.ticket_count, 0).label("ticket_count"),
            )
            .outerjoin(users_sub, Tenant.id == users_sub.c.tenant_id)
            .outerjoin(tickets_sub, Tenant.id == tickets_sub.c.tenant_id)
            .where(Tenant.deleted_at.is_(None), Tenant.is_system.is_(False))
            .order_by(Tenant.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            CompanyRow(
                id=r.id,
                name=r.name,
                slug=r.slug,
                is_active=r.is_active,
                is_system=r.is_system,
                created_at=r.created_at,
                user_count=r.user_count,
                ticket_count=r.ticket_count,
            )
            for r in rows
        ]

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Priority, Status

_DEFAULT_PRIORITIES: list[dict] = [
    {"name": "Baixa", "code": "low", "color": "#22C55E", "order": 1},
    {"name": "Média", "code": "medium", "color": "#EAB308", "order": 2},
    {"name": "Alta", "code": "high", "color": "#F97316", "order": 3},
    {"name": "Crítica", "code": "critical", "color": "#EF4444", "order": 4},
]

_DEFAULT_STATUSES: list[dict] = [
    {
        "name": "Novo",
        "code": "new",
        "order": 1,
        "requires_reason": False,
        "requires_solution": False,
        "is_terminal": False,
    },
    {
        "name": "Em Atendimento",
        "code": "in_progress",
        "order": 2,
        "requires_reason": False,
        "requires_solution": False,
        "is_terminal": False,
    },
    {
        "name": "Pendente",
        "code": "pending",
        "order": 3,
        "requires_reason": True,
        "requires_solution": False,
        "is_terminal": False,
    },
    {
        "name": "Solucionado",
        "code": "resolved",
        "order": 4,
        "requires_reason": False,
        "requires_solution": True,
        "is_terminal": False,
    },
    {
        "name": "Fechado",
        "code": "closed",
        "order": 5,
        "requires_reason": False,
        "requires_solution": False,
        "is_terminal": True,
    },
]


async def seed_catalog_defaults(db: AsyncSession, tenant_id: UUID) -> None:
    """Seeds default priorities and statuses for a new tenant. Idempotent."""
    await _ensure_priorities(db, tenant_id)
    await _ensure_statuses(db, tenant_id)
    await db.flush()


async def _ensure_priorities(db: AsyncSession, tenant_id: UUID) -> None:
    existing_stmt = select(Priority).where(Priority.tenant_id == tenant_id)
    result = await db.execute(existing_stmt)
    existing_codes = {p.code for p in result.scalars().all()}

    for data in _DEFAULT_PRIORITIES:
        if data["code"] not in existing_codes:
            db.add(
                Priority(
                    tenant_id=tenant_id,
                    name=data["name"],
                    code=data["code"],
                    color=data["color"],
                    order=data["order"],
                    is_default=True,
                    is_active=True,
                )
            )


async def _ensure_statuses(db: AsyncSession, tenant_id: UUID) -> None:
    existing_stmt = select(Status).where(Status.tenant_id == tenant_id)
    result = await db.execute(existing_stmt)
    existing_codes = {s.code for s in result.scalars().all()}

    for data in _DEFAULT_STATUSES:
        if data["code"] not in existing_codes:
            db.add(
                Status(
                    tenant_id=tenant_id,
                    name=data["name"],
                    code=data["code"],
                    order=data["order"],
                    requires_reason=data["requires_reason"],
                    requires_solution=data["requires_solution"],
                    is_terminal=data["is_terminal"],
                    is_default=True,
                    is_active=True,
                )
            )

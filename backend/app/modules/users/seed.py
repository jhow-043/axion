from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import ALL_PERMISSIONS
from app.modules.users.models import Permission, Role, RolePermission

# Default roles seeded on every new tenant (RN-04).
# code → (name, is_default, permission_codes)
_DEFAULT_ROLES: list[tuple[str, str, list[str]]] = [
    (
        "admin",
        "Admin",
        [
            "user:read",
            "user:manage",
            "team:manage",
            "ticket:create",
            "ticket:read",
            "ticket:assign",
            "ticket:transition",
            "ticket:validate",
            "dashboard:operational",
            "dashboard:management",
            "admin:config",
            "equipment:read",
            "equipment:manage",
        ],
    ),
    (
        "supervisor",
        "Supervisor",
        [
            "user:read",
            "team:manage",
            "ticket:create",
            "ticket:read",
            "ticket:assign",
            "ticket:transition",
            "ticket:validate",
            "dashboard:operational",
            "dashboard:management",
            "equipment:read",
            "equipment:manage",
        ],
    ),
    (
        "technician",
        "Técnico",
        [
            "ticket:create",
            "ticket:read",
            "ticket:assign",
            "ticket:transition",
            "dashboard:operational",
            "equipment:read",
        ],
    ),
    (
        "requester",
        "Solicitante",
        [
            "ticket:create",
            "ticket:read",
            "ticket:validate",
            "equipment:read",
        ],
    ),
]


async def seed_default_roles_and_permissions(db: AsyncSession, tenant_id: UUID) -> None:
    """Creates the default roles and permissions for a new tenant.
    Idempotent — safe to call multiple times; uses INSERT-or-skip logic."""
    permission_map = await _ensure_permissions(db)
    await _ensure_roles(db, tenant_id, permission_map)
    await db.flush()


async def _ensure_permissions(db: AsyncSession) -> dict[str, Permission]:
    """Upserts all global permissions and returns a code→Permission map."""
    existing_stmt = select(Permission)
    result = await db.execute(existing_stmt)
    existing = {p.code: p for p in result.scalars().all()}

    for code, name in ALL_PERMISSIONS:
        if code not in existing:
            perm = Permission(code=code, name=name)
            db.add(perm)
            await db.flush()
            existing[code] = perm

    return existing


async def _ensure_roles(
    db: AsyncSession, tenant_id: UUID, permission_map: dict[str, Permission]
) -> None:
    """Upserts the 4 default roles and their permission assignments for the given tenant."""
    existing_stmt = select(Role).where(Role.tenant_id == tenant_id)
    result = await db.execute(existing_stmt)
    existing_roles = {r.code: r for r in result.scalars().all()}

    for role_code, role_name, perm_codes in _DEFAULT_ROLES:
        if role_code not in existing_roles:
            role = Role(
                tenant_id=tenant_id,
                name=role_name,
                code=role_code,
                is_default=True,
            )
            db.add(role)
            await db.flush()
            existing_roles[role_code] = role

        role = existing_roles[role_code]
        await _ensure_role_permissions(db, role, perm_codes, permission_map)


async def _ensure_role_permissions(
    db: AsyncSession,
    role: Role,
    perm_codes: list[str],
    permission_map: dict[str, Permission],
) -> None:
    existing_stmt = select(RolePermission).where(RolePermission.role_id == role.id)
    result = await db.execute(existing_stmt)
    existing_perm_ids = {rp.permission_id for rp in result.scalars().all()}

    for code in perm_codes:
        perm = permission_map.get(code)
        if perm and perm.id not in existing_perm_ids:
            rp = RolePermission(role_id=role.id, permission_id=perm.id)
            db.add(rp)

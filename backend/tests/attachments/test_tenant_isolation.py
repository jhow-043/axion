"""Testes de isolamento de tenant — P11 Anexos e Evidências.

Garante que anexos de um tenant não são acessíveis a outro (INV-01, INV-02).
"""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.core.storage import get_storage
from app.modules.attachments.models import Attachment
from app.modules.catalog.models import Priority, Status
from app.modules.catalog.seed import seed_catalog_defaults
from app.modules.locations.models import Location
from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.users.models import Role, User, UserRole
from app.modules.users.seed import seed_default_roles_and_permissions


async def _bootstrap_tenant(db_session: AsyncSession, name: str):
    tenant = Tenant(name=name, slug=f"iso-{uuid.uuid4().hex[:8]}")
    db_session.add(tenant)
    await db_session.flush()
    await seed_default_roles_and_permissions(db_session, tenant.id)
    await seed_catalog_defaults(db_session, tenant.id)
    await db_session.flush()

    role_stmt = select(Role).where(Role.tenant_id == tenant.id, Role.code == "requester")
    role = (await db_session.execute(role_stmt)).scalar_one()

    user = User(
        tenant_id=tenant.id,
        name=f"User {name}",
        email=f"user-{uuid.uuid4().hex[:6]}@{name}.test",
        password_hash=hash_password("test1234"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=tenant.id, user_id=user.id, role_id=role.id))

    priority_stmt = select(Priority).where(Priority.tenant_id == tenant.id, Priority.code == "low")
    priority = (await db_session.execute(priority_stmt)).scalar_one()
    status_stmt = select(Status).where(Status.tenant_id == tenant.id, Status.code == "new")
    status = (await db_session.execute(status_stmt)).scalar_one()
    loc = Location(tenant_id=tenant.id, name=f"Sala-{uuid.uuid4().hex[:4]}", is_active=True)
    db_session.add(loc)
    await db_session.flush()

    ticket = Ticket(
        tenant_id=tenant.id,
        type="predial",
        title="Ticket isolation",
        description="desc",
        priority_id=priority.id,
        status_id=status.id,
        location_id=loc.id,
        requester_id=user.id,
    )
    db_session.add(ticket)
    await db_session.flush()

    attachment = Attachment(
        tenant_id=tenant.id,
        ticket_id=ticket.id,
        uploaded_by=user.id,
        filename="foto.jpg",
        storage_key=f"{tenant.id}/{ticket.id}/{uuid.uuid4()}.jpg",
        mime_type="image/jpeg",
        size_bytes=512,
    )
    db_session.add(attachment)
    await db_session.flush()

    role_codes_stmt = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    role_codes = list((await db_session.execute(role_codes_stmt)).scalars().all())
    token = create_access_token(str(user.id), tenant.id, role_codes)
    return tenant, user, ticket, attachment, f"Bearer {token}"


@pytest.mark.asyncio
async def test_attachment_not_visible_cross_tenant(db_session: AsyncSession, mock_storage):
    from app.main import app

    _, _, _, attachment_a, _ = await _bootstrap_tenant(db_session, "TenantA")
    _, _, _, _, token_b = await _bootstrap_tenant(db_session, "TenantB")

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_storage] = lambda: mock_storage

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": token_b},
    ) as client:
        # Tenant B user tries to get download URL for Tenant A's attachment
        resp = await client.get(f"/api/v1/attachments/{attachment_a.id}/download-url")
        # INV-02: returns 404, never 403
        assert resp.status_code == 404

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_storage, None)


@pytest.mark.asyncio
async def test_list_attachments_scoped_to_tenant(db_session: AsyncSession, mock_storage):
    from app.main import app

    _, _, ticket_a, attachment_a, token_a = await _bootstrap_tenant(db_session, "TenantC")
    _, _, ticket_b, attachment_b, token_b = await _bootstrap_tenant(db_session, "TenantD")

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_storage] = lambda: mock_storage

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": token_a},
    ) as client:
        resp = await client.get(f"/api/v1/tickets/{ticket_a.id}/attachments")
        assert resp.status_code == 200
        ids = [a["id"] for a in resp.json()["items"]]
        assert str(attachment_a.id) in ids
        assert str(attachment_b.id) not in ids

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_storage, None)

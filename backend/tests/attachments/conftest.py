from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.core.storage import StorageService, get_storage
from app.modules.attachments.models import Attachment
from app.modules.catalog.models import Priority, Status
from app.modules.catalog.seed import seed_catalog_defaults
from app.modules.locations.models import Location
from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.users.models import Role, User, UserRole
from app.modules.users.seed import seed_default_roles_and_permissions


@pytest.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="Attachments Test Corp", slug=f"att-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def seeded_tenant(db_session: AsyncSession, tenant: Tenant) -> Tenant:
    await seed_default_roles_and_permissions(db_session, tenant.id)
    await seed_catalog_defaults(db_session, tenant.id)
    await db_session.flush()
    return tenant


@pytest.fixture
async def admin_role(db_session: AsyncSession, seeded_tenant: Tenant) -> Role:
    stmt = select(Role).where(Role.tenant_id == seeded_tenant.id, Role.code == "admin")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def requester_role(db_session: AsyncSession, seeded_tenant: Tenant) -> Role:
    stmt = select(Role).where(Role.tenant_id == seeded_tenant.id, Role.code == "requester")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def technician_role(db_session: AsyncSession, seeded_tenant: Tenant) -> Role:
    stmt = select(Role).where(Role.tenant_id == seeded_tenant.id, Role.code == "technician")
    result = await db_session.execute(stmt)
    return result.scalar_one()


def _make_user(tenant_id, name, email):
    return User(
        tenant_id=tenant_id,
        name=name,
        email=email,
        password_hash=hash_password("test1234"),
        is_active=True,
    )


@pytest.fixture
async def admin_user(db_session: AsyncSession, seeded_tenant: Tenant, admin_role: Role) -> User:
    user = _make_user(seeded_tenant.id, "Admin", f"admin-{uuid.uuid4().hex[:6]}@att.test")
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=admin_role.id))
    await db_session.flush()
    return user


@pytest.fixture
async def requester_user(
    db_session: AsyncSession, seeded_tenant: Tenant, requester_role: Role
) -> User:
    user = _make_user(seeded_tenant.id, "Requester", f"req-{uuid.uuid4().hex[:6]}@att.test")
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=requester_role.id))
    await db_session.flush()
    return user


@pytest.fixture
async def technician_user(
    db_session: AsyncSession, seeded_tenant: Tenant, technician_role: Role
) -> User:
    user = _make_user(seeded_tenant.id, "Tech", f"tech-{uuid.uuid4().hex[:6]}@att.test")
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=technician_role.id)
    )
    await db_session.flush()
    return user


@pytest.fixture
async def outsider_user(
    db_session: AsyncSession, seeded_tenant: Tenant, requester_role: Role
) -> User:
    """A requester that is NOT a participant on the sample ticket."""
    user = _make_user(seeded_tenant.id, "Outsider", f"out-{uuid.uuid4().hex[:6]}@att.test")
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=requester_role.id))
    await db_session.flush()
    return user


@pytest.fixture
async def active_location(db_session: AsyncSession, seeded_tenant: Tenant) -> Location:
    loc = Location(tenant_id=seeded_tenant.id, name=f"Sala-{uuid.uuid4().hex[:4]}", is_active=True)
    db_session.add(loc)
    await db_session.flush()
    return loc


@pytest.fixture
async def default_priority(db_session: AsyncSession, seeded_tenant: Tenant) -> Priority:
    stmt = select(Priority).where(Priority.tenant_id == seeded_tenant.id, Priority.code == "low")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def default_status_new(db_session: AsyncSession, seeded_tenant: Tenant) -> Status:
    stmt = select(Status).where(Status.tenant_id == seeded_tenant.id, Status.code == "new")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def sample_ticket(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    requester_user: User,
    default_priority: Priority,
    default_status_new: Status,
    active_location: Location,
) -> Ticket:
    ticket = Ticket(
        tenant_id=seeded_tenant.id,
        type="predial",
        title="Ticket para attachments",
        description="Desc",
        priority_id=default_priority.id,
        status_id=default_status_new.id,
        location_id=active_location.id,
        requester_id=requester_user.id,
    )
    db_session.add(ticket)
    await db_session.flush()
    return ticket


@pytest.fixture
async def sample_attachment(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sample_ticket: Ticket,
    requester_user: User,
) -> Attachment:
    att = Attachment(
        tenant_id=seeded_tenant.id,
        ticket_id=sample_ticket.id,
        uploaded_by=requester_user.id,
        filename="foto.jpg",
        storage_key=f"{seeded_tenant.id}/{sample_ticket.id}/{uuid.uuid4()}.jpg",
        mime_type="image/jpeg",
        size_bytes=1024,
    )
    db_session.add(att)
    await db_session.flush()
    return att


@pytest.fixture
def mock_storage() -> MagicMock:
    svc = MagicMock(spec=StorageService)
    svc.generate_upload_url.return_value = "https://minio.test/bucket/key?presigned=1"
    svc.generate_download_url.return_value = "https://minio.test/bucket/key?get=1"
    svc.delete_object.return_value = None
    return svc


async def _make_bearer(user: User, db_session: AsyncSession) -> str:
    stmt = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    result = await db_session.execute(stmt)
    role_codes = list(result.scalars().all())
    token = create_access_token(str(user.id), user.tenant_id, role_codes)
    return f"Bearer {token}"


def _make_client(
    db_session: AsyncSession,
    auth_header: str | None = None,
    storage_mock: MagicMock | None = None,
) -> AsyncClient:
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    if storage_mock is not None:
        app.dependency_overrides[get_storage] = lambda: storage_mock
    headers = {"Authorization": auth_header} if auth_header else {}
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers)


def _cleanup(storage_mock: MagicMock | None = None) -> None:
    from app.main import app

    app.dependency_overrides.pop(get_db, None)
    if storage_mock is not None:
        app.dependency_overrides.pop(get_storage, None)


@pytest.fixture
async def admin_client(db_session: AsyncSession, admin_user: User, mock_storage: MagicMock):
    bearer = await _make_bearer(admin_user, db_session)
    async with _make_client(db_session, auth_header=bearer, storage_mock=mock_storage) as client:
        yield client
    _cleanup(mock_storage)


@pytest.fixture
async def requester_client(db_session: AsyncSession, requester_user: User, mock_storage: MagicMock):
    bearer = await _make_bearer(requester_user, db_session)
    async with _make_client(db_session, auth_header=bearer, storage_mock=mock_storage) as client:
        yield client
    _cleanup(mock_storage)


@pytest.fixture
async def outsider_client(db_session: AsyncSession, outsider_user: User, mock_storage: MagicMock):
    bearer = await _make_bearer(outsider_user, db_session)
    async with _make_client(db_session, auth_header=bearer, storage_mock=mock_storage) as client:
        yield client
    _cleanup(mock_storage)


@pytest.fixture
async def anon_client(db_session: AsyncSession, mock_storage: MagicMock):
    async with _make_client(db_session, storage_mock=mock_storage) as client:
        yield client
    _cleanup(mock_storage)

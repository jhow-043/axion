from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant

# Import test models at module level so they register in Base.metadata
# before test_engine fixture calls create_all (session-scoped in parent conftest).
from tests.tenants._models import SampleItem  # noqa: F401


@pytest.fixture
async def tenant_a(db_session: AsyncSession) -> Tenant:
    tenant = Tenant(name="Empresa Alpha", slug="empresa-alpha")
    db_session.add(tenant)
    await db_session.flush()
    return tenant


@pytest.fixture
async def tenant_b(db_session: AsyncSession) -> Tenant:
    tenant = Tenant(name="Empresa Beta", slug="empresa-beta")
    db_session.add(tenant)
    await db_session.flush()
    return tenant

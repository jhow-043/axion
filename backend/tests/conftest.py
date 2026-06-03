from __future__ import annotations

import os
from collections.abc import AsyncGenerator

# Must be set before any app imports so Settings() finds the required fields.
_TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("DATABASE_URL", _TEST_DB_URL)
os.environ.setdefault("SECRET_KEY", "test-secret-key-placeholder-not-for-production")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.deps import get_db  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.modules.equipments.models import Equipment  # noqa: E402, F401
from app.modules.locations.models import Location, Sector  # noqa: E402, F401
from app.modules.teams.models import Team, TeamMember  # noqa: E402, F401
from app.modules.tickets.models import (  # noqa: E402, F401
    Solution,
    Ticket,
    TicketComment,
    TicketObserver,
)
from app.modules.attachments.models import Attachment  # noqa: E402, F401
from app.modules.timeline.models import TicketEvent  # noqa: E402, F401
from app.shared.tenant_context import tenant_context  # noqa: E402


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def with_tenant():
    """Factory fixture returning tenant_context() — use as: `with with_tenant(tenant_id): ...`"""
    return tenant_context

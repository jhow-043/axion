from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncEngine


class TestEngine:
    async def test_get_engine_initializes_lazily(self) -> None:
        import app.db.engine as engine_module

        saved = engine_module._engine
        engine_module._engine = None

        engine = engine_module.get_engine()
        assert isinstance(engine, AsyncEngine)

        await engine_module.dispose_engine()
        assert engine_module._engine is None

        engine_module._engine = saved  # restore for other tests

    async def test_get_engine_returns_same_instance(self) -> None:
        import app.db.engine as engine_module

        engine_a = engine_module.get_engine()
        engine_b = engine_module.get_engine()
        assert engine_a is engine_b

    async def test_dispose_engine_when_none_is_noop(self) -> None:
        import app.db.engine as engine_module

        saved = engine_module._engine
        engine_module._engine = None

        await engine_module.dispose_engine()  # should not raise
        assert engine_module._engine is None

        engine_module._engine = saved


class TestSession:
    def test_get_session_factory_returns_factory(self) -> None:
        import app.db.session as session_module

        saved = session_module._factory
        session_module._factory = None

        factory = session_module.get_session_factory()
        assert factory is not None

        session_module._factory = saved

    def test_get_session_factory_returns_same_instance(self) -> None:
        import app.db.session as session_module

        f1 = session_module.get_session_factory()
        f2 = session_module.get_session_factory()
        assert f1 is f2


class TestGetDb:
    async def test_get_db_yields_async_session(self, test_engine) -> None:
        from sqlalchemy.ext.asyncio import AsyncSession

        import app.db.engine as engine_module
        import app.db.session as session_module
        from app.core.deps import get_db

        saved_engine = engine_module._engine
        saved_factory = session_module._factory
        engine_module._engine = test_engine
        session_module._factory = None

        gen = get_db()
        session = await gen.__anext__()
        assert isinstance(session, AsyncSession)

        try:
            await gen.aclose()
        except StopAsyncIteration:
            pass
        finally:
            engine_module._engine = saved_engine
            session_module._factory = saved_factory


class TestGetPagination:
    def test_get_pagination_with_explicit_values(self) -> None:
        from app.core.deps import get_pagination

        # Must pass explicit ints — FastAPI Query defaults don't resolve outside DI
        params = get_pagination(page=1, page_size=20)
        assert params.page == 1
        assert params.page_size == 20

    def test_get_pagination_custom_values(self) -> None:
        from app.core.deps import get_pagination

        params = get_pagination(page=5, page_size=50)
        assert params.page == 5
        assert params.page_size == 50


class TestTenantContext:
    def test_set_and_get_tenant(self) -> None:
        from app.shared.tenant_context import current_tenant_id, get_tenant, set_tenant

        tenant_id = uuid4()
        token = current_tenant_id.set(None)  # isolate from other tests
        try:
            set_tenant(tenant_id)
            assert get_tenant() == tenant_id
        finally:
            current_tenant_id.reset(token)

    def test_get_tenant_default_is_none(self) -> None:
        from app.shared.tenant_context import current_tenant_id, get_tenant

        token = current_tenant_id.set(None)
        try:
            assert get_tenant() is None
        finally:
            current_tenant_id.reset(token)


class TestBaseRepository:
    def test_init_stores_session_and_tenant_id(self) -> None:
        from app.shared.base_repository import BaseRepository

        class ConcreteRepo(BaseRepository):
            pass

        session = MagicMock()
        tenant_id = uuid4()
        repo = ConcreteRepo(session, tenant_id)

        assert repo.session is session
        assert repo.tenant_id == tenant_id

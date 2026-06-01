from __future__ import annotations

import uuid

import pytest

from app.shared.tenant_context import current_tenant_id, get_tenant, set_tenant, tenant_context


class TestTenantContextVar:
    def test_set_and_get_tenant(self):
        tenant_id = uuid.uuid4()
        token = current_tenant_id.set(None)
        try:
            set_tenant(tenant_id)
            assert get_tenant() == tenant_id
        finally:
            current_tenant_id.reset(token)

    def test_get_tenant_returns_none_by_default(self):
        token = current_tenant_id.set(None)
        try:
            assert get_tenant() is None
        finally:
            current_tenant_id.reset(token)


class TestTenantContext:
    def test_sets_tenant_inside_block(self):
        tenant_id = uuid.uuid4()
        token = current_tenant_id.set(None)
        try:
            with tenant_context(tenant_id):
                assert get_tenant() == tenant_id
        finally:
            current_tenant_id.reset(token)

    def test_resets_tenant_after_block(self):
        outer_id = uuid.uuid4()
        inner_id = uuid.uuid4()
        token = current_tenant_id.set(outer_id)
        try:
            with tenant_context(inner_id):
                pass
            assert get_tenant() == outer_id
        finally:
            current_tenant_id.reset(token)

    def test_resets_tenant_on_exception(self):
        outer_id = uuid.uuid4()
        inner_id = uuid.uuid4()
        token = current_tenant_id.set(outer_id)
        try:
            with pytest.raises(ValueError):
                with tenant_context(inner_id):
                    assert get_tenant() == inner_id
                    raise ValueError("simulated failure")
            assert get_tenant() == outer_id
        finally:
            current_tenant_id.reset(token)

    def test_nested_contexts_restore_correctly(self):
        outer_id = uuid.uuid4()
        mid_id = uuid.uuid4()
        inner_id = uuid.uuid4()
        token = current_tenant_id.set(outer_id)
        try:
            with tenant_context(mid_id):
                assert get_tenant() == mid_id
                with tenant_context(inner_id):
                    assert get_tenant() == inner_id
                assert get_tenant() == mid_id
            assert get_tenant() == outer_id
        finally:
            current_tenant_id.reset(token)


class TestWithTenantFixture:
    def test_with_tenant_fixture_sets_context(self, with_tenant):
        tenant_id = uuid.uuid4()
        token = current_tenant_id.set(None)
        try:
            with with_tenant(tenant_id):
                assert get_tenant() == tenant_id
            assert get_tenant() is None
        finally:
            current_tenant_id.reset(token)


class TestTenantMixin:
    def test_tenant_mixin_has_tenant_id_attribute(self):
        from app.shared.tenant_mixin import TenantMixin

        assert "tenant_id" in TenantMixin.__annotations__

    def test_sample_item_has_tenant_id_column(self):
        from sqlalchemy import inspect as sa_inspect

        from tests.tenants._models import SampleItem

        mapper = sa_inspect(SampleItem)
        column_names = [c.key for c in mapper.mapper.columns]
        assert "tenant_id" in column_names

    def test_sample_item_tenant_id_has_index(self):
        from sqlalchemy import inspect as sa_inspect

        from tests.tenants._models import SampleItem

        mapper = sa_inspect(SampleItem)
        indexed_columns = {
            col.name for idx in mapper.mapper.local_table.indexes for col in idx.columns
        }
        assert "tenant_id" in indexed_columns

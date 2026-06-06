"""Unit tests for AuditService — no database required."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.audit.service import AuditService


@pytest.fixture
def audit_repo():
    repo = MagicMock()
    repo.create_log = AsyncMock(return_value=None)
    repo.list_filtered = AsyncMock(return_value=[])
    repo.count_filtered = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def user_repo():
    repo = MagicMock()
    repo.get = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def service(audit_repo, user_repo) -> AuditService:
    return AuditService(audit_repo=audit_repo, user_repo=user_repo)


@pytest.mark.asyncio
async def test_log_persists_all_fields(service, audit_repo):
    entity_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    await service.log(
        action="user.created",
        entity_type="User",
        entity_id=entity_id,
        actor_id=actor_id,
        before=None,
        after={"name": "Alice", "email": "alice@test.com", "is_active": True},
    )

    audit_repo.create_log.assert_awaited_once()
    call_data = audit_repo.create_log.call_args[0][0]
    assert call_data["action"] == "user.created"
    assert call_data["entity_type"] == "User"
    assert call_data["entity_id"] == entity_id
    assert call_data["actor_id"] == actor_id
    assert call_data["before"] is None
    assert call_data["after"]["name"] == "Alice"


@pytest.mark.asyncio
async def test_log_with_null_actor(service, audit_repo):
    """System actions (jobs, seed) have actor_id = None."""
    await service.log(
        action="sla_policy.created",
        entity_type="SlaPolicy",
        entity_id=uuid.uuid4(),
        actor_id=None,
    )

    call_data = audit_repo.create_log.call_args[0][0]
    assert call_data["actor_id"] is None


@pytest.mark.asyncio
async def test_log_before_after_for_update(service, audit_repo):
    before = {"resolution_minutes": 480}
    after = {"resolution_minutes": 360}
    entity_id = uuid.uuid4()

    await service.log(
        action="sla_policy.updated",
        entity_type="SlaPolicy",
        entity_id=entity_id,
        actor_id=None,
        before=before,
        after=after,
    )

    call_data = audit_repo.create_log.call_args[0][0]
    assert call_data["before"] == before
    assert call_data["after"] == after


@pytest.mark.asyncio
async def test_list_logs_returns_paginated(service, audit_repo, user_repo):
    audit_repo.list_filtered = AsyncMock(return_value=[])
    audit_repo.count_filtered = AsyncMock(return_value=0)

    result = await service.list_logs(page=1, page_size=20)

    assert result.total == 0
    assert result.page == 1
    assert result.page_size == 20
    assert result.items == []

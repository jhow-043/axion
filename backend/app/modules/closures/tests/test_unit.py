"""Unit tests for P13 — Encerramento, Validação e Auto-Fechamento.
Each test covers a specific Critério de Aceite or business rule from the spec."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.modules.closures.schemas import ValidationReject
from app.modules.closures.service import ClosureService


def _make_service(**overrides):
    defaults = dict(
        validation_repo=AsyncMock(),
        settings_repo=AsyncMock(),
        ticket_repo=AsyncMock(),
        solution_repo=AsyncMock(),
        status_repo=AsyncMock(),
        user_repo=AsyncMock(),
        timeline_svc=AsyncMock(),
        notification_svc=AsyncMock(),
    )
    defaults.update(overrides)
    return ClosureService(**defaults)


def _make_validation(*, status="pending", requester_id=None, expires_at=None):
    v = MagicMock()
    v.id = uuid4()
    v.ticket_id = uuid4()
    v.status = status
    v.requester_id = requester_id or uuid4()
    v.expires_at = expires_at or (datetime.utcnow() + timedelta(days=3))
    v.responded_at = None
    v.rejection_reason = None
    return v


class TestCreateValidation:
    async def test_expires_at_uses_auto_close_days(self):
        svc = _make_service()
        settings = MagicMock(auto_close_days=7)
        svc._settings.get_or_create_defaults = AsyncMock(return_value=settings)
        svc._validations.create = AsyncMock()

        before = datetime.utcnow()
        await svc.create_validation(ticket_id=uuid4(), requester_id=uuid4())
        after = datetime.utcnow()

        call_kwargs = svc._validations.create.call_args[0][0]
        expires = call_kwargs["expires_at"]
        assert (before + timedelta(days=7)) <= expires <= (after + timedelta(days=7))

    async def test_status_is_pending_on_creation(self):
        svc = _make_service()
        svc._settings.get_or_create_defaults = AsyncMock(return_value=MagicMock(auto_close_days=5))
        svc._validations.create = AsyncMock()

        await svc.create_validation(ticket_id=uuid4(), requester_id=uuid4())

        call_data = svc._validations.create.call_args[0][0]
        assert call_data["status"] == "pending"


class TestApprove:
    async def test_non_requester_raises_forbidden(self):
        requester_id = uuid4()
        other_id = uuid4()
        svc = _make_service()
        ticket = MagicMock()
        ticket.requester_id = requester_id
        validation = _make_validation(requester_id=requester_id)
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._validations.find_by_ticket = AsyncMock(return_value=validation)

        with pytest.raises(ForbiddenError):
            await svc.approve(validation.ticket_id, actor_id=other_id)

    async def test_already_approved_raises_business_rule(self):
        requester_id = uuid4()
        svc = _make_service()
        ticket = MagicMock()
        validation = _make_validation(status="approved", requester_id=requester_id)
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._validations.find_by_ticket = AsyncMock(return_value=validation)

        with pytest.raises(BusinessRuleError):
            await svc.approve(validation.ticket_id, actor_id=requester_id)

    async def test_ticket_not_found_raises_not_found(self):
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await svc.approve(uuid4(), actor_id=uuid4())

    async def test_race_condition_lock_prevents_double_close(self):
        """If validation is already approved when we get the lock, do not close again."""
        requester_id = uuid4()
        svc = _make_service()
        ticket = MagicMock()
        validation = _make_validation(requester_id=requester_id)
        # After lock, status is already approved — another process beat us
        locked_validation = _make_validation(status="approved", requester_id=requester_id)
        locked_validation.id = validation.id
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._validations.find_by_ticket = AsyncMock(return_value=validation)
        svc._validations.get_with_lock = AsyncMock(return_value=locked_validation)

        with pytest.raises(BusinessRuleError):
            await svc.approve(validation.ticket_id, actor_id=requester_id)


class TestReject:
    async def test_rejection_reason_required(self):
        """Pydantic enforces min_length=1 on rejection_reason."""
        with pytest.raises(Exception):
            ValidationReject(rejection_reason="")

    async def test_non_requester_cannot_reject(self):
        requester_id = uuid4()
        svc = _make_service()
        ticket = MagicMock()
        validation = _make_validation(requester_id=requester_id)
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._validations.find_by_ticket = AsyncMock(return_value=validation)

        with pytest.raises(ForbiddenError):
            await svc.reject(
                validation.ticket_id,
                ValidationReject(rejection_reason="motivo"),
                actor_id=uuid4(),
            )

    async def test_already_rejected_raises_business_rule(self):
        requester_id = uuid4()
        svc = _make_service()
        ticket = MagicMock()
        validation = _make_validation(status="rejected", requester_id=requester_id)
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._validations.find_by_ticket = AsyncMock(return_value=validation)

        with pytest.raises(BusinessRuleError):
            await svc.reject(
                validation.ticket_id,
                ValidationReject(rejection_reason="motivo"),
                actor_id=requester_id,
            )


class TestAutoCloseSweep:
    async def test_idempotent_already_closed_not_closed_twice(self):
        """Job must not close a ticket whose validation is already approved."""
        svc = _make_service()
        # Validation appears expired but when locked its status is already approved
        expired = _make_validation(
            status="pending",
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        locked = _make_validation(status="approved")
        locked.id = expired.id

        svc._validations.list_expired_pending = AsyncMock(return_value=[expired])
        svc._validations.get_with_lock = AsyncMock(return_value=locked)
        svc._tickets.update = AsyncMock()

        await svc.sweep_auto_close()

        svc._tickets.update.assert_not_called()

    async def test_sweep_closes_expired_pending(self):
        requester_id = uuid4()
        ticket_id = uuid4()
        svc = _make_service()

        expired = _make_validation(
            status="pending",
            requester_id=requester_id,
            expires_at=datetime.utcnow() - timedelta(days=2),
        )
        expired.ticket_id = ticket_id
        locked = MagicMock()
        locked.id = expired.id
        locked.ticket_id = ticket_id
        locked.status = "pending"

        svc._validations.list_expired_pending = AsyncMock(return_value=[expired])
        svc._validations.get_with_lock = AsyncMock(return_value=locked)
        svc._validations.update = AsyncMock()
        closed_status = MagicMock(id=uuid4())
        svc._statuses.find_by_code = AsyncMock(return_value=closed_status)
        svc._tickets.update = AsyncMock()
        svc._timeline.record_event = AsyncMock()
        svc._notifications.notify = AsyncMock()

        await svc.sweep_auto_close()

        svc._tickets.update.assert_called_once()
        payload_kwarg = svc._timeline.record_event.call_args.kwargs.get("payload", {})
        assert payload_kwarg.get("method") == "auto"


class TestDaysRemaining:
    def test_days_remaining_positive(self):
        validation = _make_validation(expires_at=datetime.utcnow() + timedelta(days=3))
        result = ClosureService._build_response(validation, None)
        assert result.days_remaining >= 2  # at least 2 full days

    def test_days_remaining_zero_when_expired(self):
        validation = _make_validation(expires_at=datetime.utcnow() - timedelta(days=1))
        result = ClosureService._build_response(validation, None)
        assert result.days_remaining == 0

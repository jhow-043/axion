"""Unit tests for the ticket state machine and business rules (no DB)."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.modules.tickets.schemas import TicketCommentCreate, TicketCreate, TicketTransition
from app.modules.tickets.service import _VALID_TRANSITIONS, TicketService

# ── State Machine ─────────────────────────────────────────────────────────────


class TestStateMachine:
    def test_new_to_in_progress_is_valid(self):
        TicketService._validate_transition("new", "in_progress")  # must not raise

    def test_in_progress_to_pending_is_valid(self):
        TicketService._validate_transition("in_progress", "pending")

    def test_in_progress_to_resolved_is_valid(self):
        TicketService._validate_transition("in_progress", "resolved")

    def test_pending_to_in_progress_is_valid(self):
        TicketService._validate_transition("pending", "in_progress")

    def test_resolved_to_in_progress_is_valid(self):
        TicketService._validate_transition("resolved", "in_progress")

    def test_resolved_to_closed_is_valid(self):
        TicketService._validate_transition("resolved", "closed")

    def test_new_to_closed_is_invalid(self):
        with pytest.raises(BusinessRuleError):
            TicketService._validate_transition("new", "closed")

    def test_new_to_pending_is_invalid(self):
        with pytest.raises(BusinessRuleError):
            TicketService._validate_transition("new", "pending")

    def test_new_to_resolved_is_invalid(self):
        with pytest.raises(BusinessRuleError):
            TicketService._validate_transition("new", "resolved")

    def test_closed_to_in_progress_is_invalid(self):
        with pytest.raises(BusinessRuleError):
            TicketService._validate_transition("closed", "in_progress")

    def test_closed_to_pending_is_invalid(self):
        with pytest.raises(BusinessRuleError):
            TicketService._validate_transition("closed", "pending")

    def test_pending_to_resolved_is_invalid(self):
        with pytest.raises(BusinessRuleError):
            TicketService._validate_transition("pending", "resolved")

    def test_pending_to_closed_is_invalid(self):
        with pytest.raises(BusinessRuleError):
            TicketService._validate_transition("pending", "closed")

    def test_all_valid_transitions_match_spec(self):
        assert _VALID_TRANSITIONS["new"] == frozenset({"in_progress"})
        assert _VALID_TRANSITIONS["in_progress"] == frozenset({"pending", "resolved"})
        assert _VALID_TRANSITIONS["pending"] == frozenset({"in_progress"})
        assert _VALID_TRANSITIONS["resolved"] == frozenset({"in_progress", "closed"})
        assert _VALID_TRANSITIONS["closed"] == frozenset()


# ── Type constraints ──────────────────────────────────────────────────────────


def _make_service(**overrides) -> TicketService:
    defaults = dict(
        ticket_repo=AsyncMock(),
        observer_repo=AsyncMock(),
        comment_repo=AsyncMock(),
        solution_repo=AsyncMock(),
        status_repo=AsyncMock(),
        priority_repo=AsyncMock(),
        category_repo=AsyncMock(),
        pending_reason_repo=AsyncMock(),
        equipment_repo=AsyncMock(),
        location_repo=AsyncMock(),
        user_repo=AsyncMock(),
        timeline_svc=AsyncMock(),
        notification_svc=AsyncMock(),
    )
    defaults.update(overrides)
    return TicketService(**defaults)


class TestCreateTypeConstraints:
    async def test_industrial_without_equipment_raises(self):
        svc = _make_service()
        with pytest.raises(BusinessRuleError, match="equipamento"):
            await svc._validate_create_type_constraints(
                TicketCreate(
                    type="industrial",
                    title="T",
                    description="D",
                    priority_id=uuid4(),
                )
            )

    async def test_predial_without_location_raises(self):
        svc = _make_service()
        with pytest.raises(BusinessRuleError, match="local"):
            await svc._validate_create_type_constraints(
                TicketCreate(
                    type="predial",
                    title="T",
                    description="D",
                    priority_id=uuid4(),
                )
            )

    async def test_industrial_with_inactive_equipment_raises(self):
        inactive_eq = AsyncMock(is_active=False)
        svc = _make_service()
        svc._equipments.get = AsyncMock(return_value=inactive_eq)
        with pytest.raises(BusinessRuleError, match="inativo"):
            await svc._validate_create_type_constraints(
                TicketCreate(
                    type="industrial",
                    title="T",
                    description="D",
                    priority_id=uuid4(),
                    equipment_id=uuid4(),
                )
            )

    async def test_predial_with_inactive_location_raises(self):
        inactive_loc = AsyncMock(is_active=False)
        svc = _make_service()
        svc._locations.get = AsyncMock(return_value=inactive_loc)
        with pytest.raises(BusinessRuleError, match="inativo"):
            await svc._validate_create_type_constraints(
                TicketCreate(
                    type="predial",
                    title="T",
                    description="D",
                    priority_id=uuid4(),
                    location_id=uuid4(),
                )
            )

    async def test_industrial_with_unknown_equipment_raises_not_found(self):
        svc = _make_service()
        svc._equipments.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await svc._validate_create_type_constraints(
                TicketCreate(
                    type="industrial",
                    title="T",
                    description="D",
                    priority_id=uuid4(),
                    equipment_id=uuid4(),
                )
            )


# ── Transition validation ─────────────────────────────────────────────────────


class TestTransitionValidation:
    async def test_pending_without_reason_id_raises(self):
        current_status = AsyncMock(code="in_progress")
        ticket = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._statuses.get = AsyncMock(return_value=current_status)
        with pytest.raises(BusinessRuleError, match="Motivo"):
            await svc.transition(
                ticket.id,
                TicketTransition(to_status="pending", pending_reason_id=None),
                current_user_id=uuid4(),
            )

    async def test_resolved_without_solution_raises(self):
        current_status = AsyncMock(code="in_progress")
        ticket = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._statuses.get = AsyncMock(return_value=current_status)
        with pytest.raises(BusinessRuleError, match="solução"):
            await svc.transition(
                ticket.id,
                TicketTransition(to_status="resolved", solution_description=None),
                current_user_id=uuid4(),
            )

    async def test_closed_transition_raises_business_rule(self):
        current_status = AsyncMock(code="closed")
        ticket = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._statuses.get = AsyncMock(return_value=current_status)
        with pytest.raises(BusinessRuleError):
            await svc.transition(
                ticket.id,
                TicketTransition(to_status="in_progress"),
                current_user_id=uuid4(),
            )


# ── Comment participation ─────────────────────────────────────────────────────


class TestCommentParticipation:
    async def test_non_participant_cannot_comment(self):
        ticket = AsyncMock(id=uuid4(), requester_id=uuid4(), assignee_id=None)
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._observers.find = AsyncMock(return_value=None)
        with pytest.raises(ForbiddenError):
            await svc.add_comment(
                ticket.id,
                TicketCommentCreate(content="Oi"),
                author_id=uuid4(),  # unrelated user
            )

    async def test_requester_can_comment(self):
        from datetime import UTC, datetime

        requester_id = uuid4()
        ticket_id = uuid4()
        ticket = AsyncMock(id=ticket_id, requester_id=requester_id, assignee_id=None)
        now = datetime.now(UTC)
        comment = AsyncMock(
            id=uuid4(),
            ticket_id=ticket_id,
            author_id=requester_id,
            content="ok",
            created_at=now,
            updated_at=now,
        )
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._comments.create = AsyncMock(return_value=comment)
        # Should not raise
        await svc.add_comment(ticket_id, TicketCommentCreate(content="ok"), author_id=requester_id)

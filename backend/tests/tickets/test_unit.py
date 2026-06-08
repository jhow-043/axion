"""Unit tests for the ticket state machine and business rules (no DB)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.modules.tickets.schemas import (
    TicketCommentCreate,
    TicketCommentUpdate,
    TicketCreate,
    TicketObserverAdd,
    TicketTransition,
)
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


# ── Create error paths ────────────────────────────────────────────────────────


class TestCreateErrorPaths:
    async def test_priority_not_found_raises(self):
        svc = _make_service()
        svc._priorities.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError, match="Prioridade"):
            await svc.create(
                TicketCreate(
                    type="predial",
                    title="T",
                    description="D",
                    priority_id=uuid4(),
                    location_id=uuid4(),
                ),
                requester_id=uuid4(),
            )

    async def test_priority_inactive_raises(self):
        svc = _make_service()
        svc._priorities.get = AsyncMock(return_value=AsyncMock(is_active=False))
        with pytest.raises(NotFoundError, match="Prioridade"):
            await svc.create(
                TicketCreate(
                    type="predial",
                    title="T",
                    description="D",
                    priority_id=uuid4(),
                    location_id=uuid4(),
                ),
                requester_id=uuid4(),
            )

    async def test_category_not_found_raises(self):
        svc = _make_service()
        svc._priorities.get = AsyncMock(return_value=AsyncMock(is_active=True))
        svc._categories.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError, match="Categoria"):
            await svc.create(
                TicketCreate(
                    type="predial",
                    title="T",
                    description="D",
                    priority_id=uuid4(),
                    category_id=uuid4(),
                    location_id=uuid4(),
                ),
                requester_id=uuid4(),
            )

    async def test_team_not_found_raises(self):
        svc = _make_service()
        svc._priorities.get = AsyncMock(return_value=AsyncMock(is_active=True))
        svc._categories.get = AsyncMock(return_value=AsyncMock(is_active=True))
        team_repo_mock = AsyncMock()
        team_repo_mock.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError, match="Equipe"):
            with patch(
                "app.modules.teams.repository.TeamRepository",
                return_value=team_repo_mock,
            ):
                await svc.create(
                    TicketCreate(
                        type="predial",
                        title="T",
                        description="D",
                        priority_id=uuid4(),
                        category_id=uuid4(),
                        team_id=uuid4(),
                        location_id=uuid4(),
                    ),
                    requester_id=uuid4(),
                )

    async def test_initial_status_not_configured_raises(self):
        svc = _make_service()
        svc._priorities.get = AsyncMock(return_value=AsyncMock(is_active=True))
        svc._statuses.find_by_code = AsyncMock(return_value=None)
        with pytest.raises(BusinessRuleError, match="Status inicial"):
            await svc.create(
                TicketCreate(
                    type="predial",
                    title="T",
                    description="D",
                    priority_id=uuid4(),
                    location_id=uuid4(),
                ),
                requester_id=uuid4(),
            )


# ── Get error paths ───────────────────────────────────────────────────────────


class TestGetErrorPaths:
    async def test_get_not_found_raises(self):
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await svc.get(uuid4(), uuid4(), {"admin"})


# ── Assign error paths ────────────────────────────────────────────────────────


class TestAssignErrorPaths:
    async def test_assign_ticket_not_found_raises(self):
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await svc.assign(uuid4(), uuid4(), uuid4())

    async def test_assign_non_new_status_raises(self):
        ticket = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._statuses.get = AsyncMock(return_value=AsyncMock(code="in_progress"))
        with pytest.raises(BusinessRuleError, match="Novo"):
            await svc.assign(ticket.id, uuid4(), uuid4())

    async def test_assign_in_progress_status_not_configured_raises(self):
        ticket = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._statuses.get = AsyncMock(return_value=AsyncMock(code="new"))
        svc._statuses.find_by_code = AsyncMock(return_value=None)
        with pytest.raises(BusinessRuleError, match="in_progress"):
            await svc.assign(ticket.id, uuid4(), uuid4())


# ── Transition error paths ────────────────────────────────────────────────────


class TestTransitionErrorPaths:
    async def test_transition_ticket_not_found_raises(self):
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await svc.transition(uuid4(), TicketTransition(to_status="in_progress"), uuid4())

    async def test_transition_current_status_none_raises(self):
        ticket = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._statuses.get = AsyncMock(return_value=None)
        with pytest.raises(BusinessRuleError, match="Status atual"):
            await svc.transition(ticket.id, TicketTransition(to_status="in_progress"), uuid4())

    async def test_transition_pending_reason_not_found_raises(self):
        ticket = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._statuses.get = AsyncMock(return_value=AsyncMock(code="in_progress"))
        svc._pending_reasons.get = AsyncMock(return_value=None)
        with pytest.raises((BusinessRuleError, NotFoundError)):
            await svc.transition(
                ticket.id,
                TicketTransition(to_status="pending", pending_reason_id=uuid4()),
                uuid4(),
            )

    async def test_transition_target_status_not_configured_raises(self):
        ticket = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._statuses.get = AsyncMock(return_value=AsyncMock(code="in_progress"))
        svc._statuses.find_by_code = AsyncMock(return_value=None)
        with pytest.raises(BusinessRuleError, match="não configurado"):
            await svc.transition(
                ticket.id,
                TicketTransition(to_status="resolved", solution_description="Fixed."),
                uuid4(),
            )


# ── Observer error paths ──────────────────────────────────────────────────────


class TestObserverErrorPaths:
    async def test_add_observer_user_not_found_raises(self):
        ticket = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._users.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError, match="Usuário"):
            await svc.add_observer(ticket.id, TicketObserverAdd(user_id=uuid4()), uuid4())

    async def test_add_observer_duplicate_raises(self):
        ticket = AsyncMock(id=uuid4())
        user = AsyncMock(is_active=True)
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._users.get = AsyncMock(return_value=user)
        svc._observers.find = AsyncMock(return_value=AsyncMock())
        with pytest.raises(BusinessRuleError, match="observador"):
            await svc.add_observer(ticket.id, TicketObserverAdd(user_id=uuid4()), uuid4())

    async def test_remove_observer_ticket_not_found_raises(self):
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await svc.remove_observer(uuid4(), uuid4(), uuid4())

    async def test_remove_observer_not_found_raises(self):
        ticket = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._observers.find = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError, match="Observador"):
            await svc.remove_observer(ticket.id, uuid4(), uuid4())

    async def test_remove_observer_success(self):
        ticket = AsyncMock(id=uuid4())
        observer = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._observers.find = AsyncMock(return_value=observer)
        svc._observers.delete = AsyncMock()
        svc._timeline.record_event = AsyncMock()
        await svc.remove_observer(ticket.id, uuid4(), uuid4())
        svc._observers.delete.assert_called_once_with(observer.id)


# ── Comment error paths ───────────────────────────────────────────────────────


class TestCommentErrorPaths:
    async def test_add_comment_ticket_not_found_raises(self):
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await svc.add_comment(uuid4(), TicketCommentCreate(content="x"), uuid4())

    async def test_edit_comment_ticket_not_found_raises(self):
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await svc.edit_comment(uuid4(), uuid4(), TicketCommentUpdate(content="x"), uuid4())

    async def test_edit_comment_not_editable_raises(self):
        ticket = AsyncMock(id=uuid4())
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._comments.find_editable = AsyncMock(return_value=None)
        with pytest.raises(BusinessRuleError):
            await svc.edit_comment(
                ticket.id, uuid4(), TicketCommentUpdate(content="x"), uuid4()
            )

    async def test_edit_comment_wrong_ticket_raises(self):
        ticket_id = uuid4()
        ticket = AsyncMock(id=ticket_id)
        comment = AsyncMock(ticket_id=uuid4())  # different ticket
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=ticket)
        svc._comments.find_editable = AsyncMock(return_value=comment)
        with pytest.raises(NotFoundError):
            await svc.edit_comment(
                ticket_id, comment.id, TicketCommentUpdate(content="x"), uuid4()
            )

    async def test_list_comments_ticket_not_found_raises(self):
        svc = _make_service()
        svc._tickets.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await svc.list_comments(uuid4(), uuid4(), {"admin"}, page=1, page_size=10)


# ── Access control paths ──────────────────────────────────────────────────────


class TestAccessControlPaths:
    async def test_check_read_access_admin_passes(self):
        ticket = AsyncMock(assignee_id=None, team_id=None, requester_id=uuid4())
        svc = _make_service()
        await svc._check_read_access(ticket, uuid4(), {"admin"})

    async def test_check_read_access_tech_assignee_passes(self):
        user_id = uuid4()
        ticket = AsyncMock(assignee_id=user_id, team_id=None, requester_id=uuid4())
        svc = _make_service()
        await svc._check_read_access(ticket, user_id, {"technician"})

    async def test_check_read_access_tech_same_team_passes(self):
        user_id = uuid4()
        team_id = uuid4()
        ticket = AsyncMock(assignee_id=uuid4(), team_id=team_id, requester_id=uuid4())
        svc = _make_service()
        svc._tickets.get_team_ids_for_user = AsyncMock(return_value=[team_id])
        await svc._check_read_access(ticket, user_id, {"technician"})

    async def test_check_read_access_tech_no_team_raises(self):
        user_id = uuid4()
        ticket = AsyncMock(assignee_id=uuid4(), team_id=uuid4(), requester_id=uuid4())
        svc = _make_service()
        svc._tickets.get_team_ids_for_user = AsyncMock(return_value=[])
        svc._observers.find = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await svc._check_read_access(ticket, user_id, {"technician"})

    async def test_resolve_visibility_tech_role(self):
        user_id = uuid4()
        team_ids = [uuid4()]
        svc = _make_service()
        svc._tickets.get_team_ids_for_user = AsyncMock(return_value=team_ids)
        vis, ids = await svc._resolve_visibility(user_id, {"technician"})
        assert vis == "team"
        assert ids == team_ids

    async def test_resolve_visibility_requester_role(self):
        svc = _make_service()
        vis, ids = await svc._resolve_visibility(uuid4(), {"requester"})
        assert vis == "own"
        assert ids == []

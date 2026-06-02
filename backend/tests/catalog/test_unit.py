from __future__ import annotations

import pytest

from app.modules.catalog.seed import _DEFAULT_PRIORITIES, _DEFAULT_STATUSES


class TestSeedDefaultValues:
    def test_default_priorities_have_required_codes(self):
        codes = {p["code"] for p in _DEFAULT_PRIORITIES}
        assert codes == {"low", "medium", "high", "critical"}

    def test_default_priorities_have_unique_orders(self):
        orders = [p["order"] for p in _DEFAULT_PRIORITIES]
        assert len(orders) == len(set(orders))

    def test_default_statuses_have_required_codes(self):
        codes = {s["code"] for s in _DEFAULT_STATUSES}
        assert codes == {"new", "in_progress", "pending", "resolved", "closed"}

    def test_pending_status_requires_reason(self):
        pending = next(s for s in _DEFAULT_STATUSES if s["code"] == "pending")
        assert pending["requires_reason"] is True
        assert pending["requires_solution"] is False
        assert pending["is_terminal"] is False

    def test_resolved_status_requires_solution(self):
        resolved = next(s for s in _DEFAULT_STATUSES if s["code"] == "resolved")
        assert resolved["requires_solution"] is True
        assert resolved["requires_reason"] is False
        assert resolved["is_terminal"] is False

    def test_closed_status_is_terminal(self):
        closed = next(s for s in _DEFAULT_STATUSES if s["code"] == "closed")
        assert closed["is_terminal"] is True

    def test_default_statuses_have_unique_orders(self):
        orders = [s["order"] for s in _DEFAULT_STATUSES]
        assert len(orders) == len(set(orders))

    def test_new_status_has_no_special_flags(self):
        new = next(s for s in _DEFAULT_STATUSES if s["code"] == "new")
        assert new["requires_reason"] is False
        assert new["requires_solution"] is False
        assert new["is_terminal"] is False


class TestStatusSchemaRejectsImmutableFlags:
    """INV-03: status behavioral flags cannot be changed via the PATCH schema."""

    def test_status_update_rejects_requires_reason(self):
        from pydantic import ValidationError

        from app.modules.catalog.schemas import StatusUpdate

        with pytest.raises(ValidationError):
            StatusUpdate.model_validate({"requires_reason": True})

    def test_status_update_rejects_requires_solution(self):
        from pydantic import ValidationError

        from app.modules.catalog.schemas import StatusUpdate

        with pytest.raises(ValidationError):
            StatusUpdate.model_validate({"requires_solution": True})

    def test_status_update_rejects_is_terminal(self):
        from pydantic import ValidationError

        from app.modules.catalog.schemas import StatusUpdate

        with pytest.raises(ValidationError):
            StatusUpdate.model_validate({"is_terminal": True})

    def test_status_update_rejects_code(self):
        from pydantic import ValidationError

        from app.modules.catalog.schemas import StatusUpdate

        with pytest.raises(ValidationError):
            StatusUpdate.model_validate({"code": "hacked"})

    def test_status_update_allows_name_and_order(self):
        from app.modules.catalog.schemas import StatusUpdate

        data = StatusUpdate.model_validate({"name": "Novo Nome", "order": 2})
        assert data.name == "Novo Nome"
        assert data.order == 2

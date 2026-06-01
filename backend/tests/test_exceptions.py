from __future__ import annotations

from app.core.exceptions import (
    AppException,
    BusinessRuleError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnprocessableError,
    _envelope,
)


class TestExceptionHierarchy:
    def test_not_found_error_status_and_code(self) -> None:
        exc = NotFoundError()
        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"

    def test_not_found_default_message(self) -> None:
        exc = NotFoundError()
        assert "encontrado" in exc.message.lower()

    def test_conflict_error_status_and_code(self) -> None:
        exc = ConflictError()
        assert exc.status_code == 409
        assert exc.error_code == "CONFLICT"

    def test_unprocessable_error_status_and_code(self) -> None:
        exc = UnprocessableError()
        assert exc.status_code == 422
        assert exc.error_code == "UNPROCESSABLE"

    def test_forbidden_error_status_and_code(self) -> None:
        exc = ForbiddenError()
        assert exc.status_code == 403
        assert exc.error_code == "FORBIDDEN"

    def test_business_rule_error_status_and_code(self) -> None:
        exc = BusinessRuleError("Transição inválida.")
        assert exc.status_code == 422
        assert exc.error_code == "BUSINESS_RULE_ERROR"
        assert exc.message == "Transição inválida."

    def test_exception_with_detail(self) -> None:
        exc = NotFoundError("Chamado não encontrado.", detail={"id": "abc-123"})
        assert exc.detail == {"id": "abc-123"}

    def test_all_exceptions_inherit_from_app_exception(self) -> None:
        subclasses = (
            NotFoundError,
            ConflictError,
            UnprocessableError,
            ForbiddenError,
            BusinessRuleError,
        )
        for cls in subclasses:
            assert issubclass(cls, AppException)


class TestErrorEnvelope:
    def test_envelope_has_required_fields(self) -> None:
        env = _envelope("NOT_FOUND", "Recurso não encontrado.")
        assert set(env.keys()) == {"error", "message", "detail", "timestamp"}

    def test_envelope_error_code(self) -> None:
        env = _envelope("CONFLICT", "Conflito.")
        assert env["error"] == "CONFLICT"

    def test_envelope_message(self) -> None:
        env = _envelope("NOT_FOUND", "Item ausente.")
        assert env["message"] == "Item ausente."

    def test_envelope_detail_defaults_to_none(self) -> None:
        env = _envelope("NOT_FOUND", "Test")
        assert env["detail"] is None

    def test_envelope_detail_with_value(self) -> None:
        env = _envelope("NOT_FOUND", "Test", detail={"field": "id"})
        assert env["detail"] == {"field": "id"}

    def test_envelope_timestamp_is_iso_string(self) -> None:
        env = _envelope("NOT_FOUND", "Test")
        assert isinstance(env["timestamp"], str)
        assert "T" in env["timestamp"]

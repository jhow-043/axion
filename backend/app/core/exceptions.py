from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):  # noqa: N818
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, detail: Any = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(AppException):
    status_code = 404
    error_code = "NOT_FOUND"

    def __init__(self, message: str = "Recurso não encontrado.", detail: Any = None) -> None:
        super().__init__(message, detail)


class ConflictError(AppException):
    status_code = 409
    error_code = "CONFLICT"

    def __init__(self, message: str = "Conflito com o estado atual.", detail: Any = None) -> None:
        super().__init__(message, detail)


class UnprocessableError(AppException):
    status_code = 422
    error_code = "UNPROCESSABLE"

    def __init__(self, message: str = "Dados inválidos.", detail: Any = None) -> None:
        super().__init__(message, detail)


class ForbiddenError(AppException):
    status_code = 403
    error_code = "FORBIDDEN"

    def __init__(self, message: str = "Acesso negado.", detail: Any = None) -> None:
        super().__init__(message, detail)


class BusinessRuleError(AppException):
    status_code = 422
    error_code = "BUSINESS_RULE_ERROR"

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(message, detail)


_HTTP_ERROR_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "UNPROCESSABLE",
    429: "TOO_MANY_REQUESTS",
}


def _envelope(error_code: str, message: str, detail: Any = None) -> dict[str, Any]:
    return {
        "error": error_code,
        "message": message,
        "detail": detail,
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(exc.error_code, exc.message, exc.detail),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    error_code = _HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(error_code, str(exc.detail)),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_envelope("VALIDATION_ERROR", "Dados de entrada inválidos.", exc.errors()),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_envelope("INTERNAL_SERVER_ERROR", "Um erro interno ocorreu."),
    )

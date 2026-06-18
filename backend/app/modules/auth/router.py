from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.modules.auth.repository import RefreshTokenRepository, UserAuthRepository
from app.modules.auth.schemas import LoginRequest, TokenResponse, UserMeResponse
from app.modules.auth.service import AuthService, InvalidCredentialsError, TokenRevokedError
from app.modules.hub.repository import ModuleRepository
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"
_COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


def _get_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(
        user_repo=UserAuthRepository(db),
        token_repo=RefreshTokenRepository(db),
        module_repo=ModuleRepository(db),
    )


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        samesite="strict",
        max_age=_COOKIE_MAX_AGE,
        path="/api/v1/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, path="/api/v1/auth/refresh")


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    service: AuthService = Depends(_get_service),
) -> TokenResponse:
    try:
        token_response, raw_refresh = await service.login(body.email, body.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    _set_refresh_cookie(response, raw_refresh)
    return token_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    response: Response,
    service: AuthService = Depends(_get_service),
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
) -> TokenResponse:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token ausente.")
    try:
        token_response, new_raw_refresh = await service.refresh(refresh_token)
    except (InvalidCredentialsError, TokenRevokedError) as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    _set_refresh_cookie(response, new_raw_refresh)
    return token_response


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    service: AuthService = Depends(_get_service),
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
) -> None:
    if refresh_token:
        await service.logout(refresh_token)
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserMeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(_get_service),
) -> UserMeResponse:
    return await service.get_me(current_user)

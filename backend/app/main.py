from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.db.engine import dispose_engine, get_engine
from app.modules.attachments.router import attachments_router, ticket_attachments_router
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import catalog_router
from app.modules.equipments.router import router as equipments_router
from app.modules.locations.router import locations_router, sectors_router
from app.modules.teams.router import router as teams_router
from app.modules.tickets.router import router as tickets_router
from app.modules.timeline.router import router as timeline_router
from app.modules.users.router import permissions_router, roles_router, users_router
from app.routers.health import api_router as health_api_router
from app.routers.health import root_router as health_root_router

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.APP_NAME)
    get_engine()
    yield
    logger.info("Shutting down %s", settings.APP_NAME)
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        logger.info(
            "%s %s %d %.3fs", request.method, request.url.path, response.status_code, elapsed
        )
        return response

    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(health_root_router)
    app.include_router(health_api_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(roles_router, prefix="/api/v1")
    app.include_router(permissions_router, prefix="/api/v1")
    app.include_router(teams_router, prefix="/api/v1")
    app.include_router(sectors_router, prefix="/api/v1")
    app.include_router(locations_router, prefix="/api/v1")
    app.include_router(catalog_router, prefix="/api/v1")
    app.include_router(equipments_router, prefix="/api/v1")
    app.include_router(tickets_router, prefix="/api/v1")
    app.include_router(timeline_router, prefix="/api/v1")
    app.include_router(ticket_attachments_router, prefix="/api/v1")
    app.include_router(attachments_router, prefix="/api/v1")

    return app


app = create_app()

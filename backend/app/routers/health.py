from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db

root_router = APIRouter(tags=["system"])
api_router = APIRouter(tags=["system"])


@root_router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    overall = "ok" if db_status == "ok" else "degraded"
    status_code = 200 if db_status == "ok" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "database": db_status,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


@api_router.get("/ping")
async def ping() -> dict[str, bool]:
    return {"pong": True}

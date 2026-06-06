from __future__ import annotations

import csv
import io
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import (
    get_current_user,
    get_db,
    require_permission,
)
from app.core.permissions import DASHBOARD_MANAGEMENT
from app.modules.dashboards.repository import DashboardRepository

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_repo(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> DashboardRepository:
    return DashboardRepository(db, current_user.tenant_id)


def _validate_period(date_from: datetime, date_to: datetime) -> None:
    if (date_to - date_from).days > settings.REPORT_MAX_PERIOD_DAYS:
        raise HTTPException(
            status_code=422,
            detail=f"Período máximo de {settings.REPORT_MAX_PERIOD_DAYS} dias excedido.",
        )


def _csv_response(headers: list[str], rows: list[dict], filename: str) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/tickets")
async def report_tickets(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    team_id: UUID | None = Query(default=None),
    priority_id: UUID | None = Query(default=None),
    ticket_type: str | None = Query(default=None),
    fmt: str = Query(default="json", alias="format"),
    repo: DashboardRepository = Depends(_get_repo),
    _: None = Depends(require_permission(DASHBOARD_MANAGEMENT)),
):
    _validate_period(date_from, date_to)
    rows = await repo.get_tickets_for_report(date_from, date_to, team_id, priority_id, ticket_type)
    data = [
        {
            "id": str(row.id),
            "type": row.type,
            "title": row.title,
            "priority": row.priority,
            "status": row.status,
            "closed": row.is_terminal,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "closed_at": row.closed_at.isoformat() if row.closed_at else None,
            "team": row.team_name or "",
        }
        for row in rows
    ]
    if fmt == "csv":
        headers = ["id", "type", "title", "priority", "status", "closed", "created_at", "closed_at", "team"]
        return _csv_response(headers, data, "relatorio_chamados.csv")
    return data


@router.get("/sla")
async def report_sla(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    team_id: UUID | None = Query(default=None),
    fmt: str = Query(default="json", alias="format"),
    repo: DashboardRepository = Depends(_get_repo),
    _: None = Depends(require_permission(DASHBOARD_MANAGEMENT)),
):
    _validate_period(date_from, date_to)
    rows = await repo.get_sla_for_report(date_from, date_to, team_id)
    data = [
        {
            "ticket_id": str(row.id),
            "title": row.title,
            "team": row.team_name or "",
            "attendance_due_at": row.attendance_due_at.isoformat() if row.attendance_due_at else None,
            "attendance_status": row.attendance_status,
            "resolution_due_at": row.resolution_due_at.isoformat() if row.resolution_due_at else None,
            "resolution_status": row.resolution_status,
            "total_paused_minutes": row.total_paused_minutes,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]
    if fmt == "csv":
        headers = [
            "ticket_id", "title", "team",
            "attendance_due_at", "attendance_status",
            "resolution_due_at", "resolution_status",
            "total_paused_minutes", "created_at",
        ]
        return _csv_response(headers, data, "relatorio_sla.csv")
    return data


@router.get("/equipments")
async def report_equipments(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    fmt: str = Query(default="json", alias="format"),
    repo: DashboardRepository = Depends(_get_repo),
    _: None = Depends(require_permission(DASHBOARD_MANAGEMENT)),
):
    _validate_period(date_from, date_to)
    rows = await repo.get_equipments_for_report(date_from, date_to)
    data = [
        {
            "equipment_id": str(row.id),
            "code": row.code,
            "name": row.name,
            "ticket_count": row.ticket_count,
            "critical_count": int(row.critical_count or 0),
        }
        for row in rows
    ]
    if fmt == "csv":
        headers = ["equipment_id", "code", "name", "ticket_count", "critical_count"]
        return _csv_response(headers, data, "relatorio_equipamentos.csv")
    return data


@router.get("/teams")
async def report_teams(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    team_id: UUID | None = Query(default=None),
    fmt: str = Query(default="json", alias="format"),
    repo: DashboardRepository = Depends(_get_repo),
    _: None = Depends(require_permission(DASHBOARD_MANAGEMENT)),
):
    _validate_period(date_from, date_to)
    rows = await repo.get_teams_for_report(date_from, date_to, team_id)
    data = [
        {
            "team_id": str(row.id),
            "name": row.name,
            "total_closed": row.total_closed,
        }
        for row in rows
    ]
    if fmt == "csv":
        headers = ["team_id", "name", "total_closed"]
        return _csv_response(headers, data, "relatorio_equipes.csv")
    return data

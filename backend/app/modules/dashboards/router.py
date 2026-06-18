from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import (
    get_current_role_codes,
    get_current_user,
    get_db,
    require_module,
    require_permission,
)
from app.core.permissions import DASHBOARD_MANAGEMENT, DASHBOARD_OPERATIONAL
from app.modules.dashboards.repository import DashboardRepository
from app.modules.dashboards.schemas import (
    BoardResponse,
    ManagementDashboardResponse,
    SupervisorDashboardResponse,
    TechnicianDashboardResponse,
)
from app.modules.dashboards.service import DashboardService

router = APIRouter(prefix="/dashboards", tags=["dashboards"], dependencies=[Depends(require_module("manutencao"))])

_DEFAULT_PERIOD_DAYS = settings.REPORT_MAX_PERIOD_DAYS


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> DashboardService:
    return DashboardService(dashboard_repo=DashboardRepository(db, current_user.tenant_id))


@router.get("/technician", response_model=TechnicianDashboardResponse)
async def get_technician_dashboard(
    service: DashboardService = Depends(_get_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission(DASHBOARD_OPERATIONAL)),
) -> TechnicianDashboardResponse:
    return await service.get_technician_dashboard(current_user.id)


@router.get("/supervisor", response_model=SupervisorDashboardResponse)
async def get_supervisor_dashboard(
    team_id: UUID | None = Query(default=None),
    priority_id: UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    service: DashboardService = Depends(_get_service),
    current_user=Depends(get_current_user),
    role_codes: list[str] = Depends(get_current_role_codes),
    _: None = Depends(require_permission(DASHBOARD_OPERATIONAL)),
) -> SupervisorDashboardResponse:
    return await service.get_supervisor_dashboard(
        user_id=current_user.id,
        role_codes=role_codes,
        team_id=team_id,
        priority_id=priority_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/board", response_model=BoardResponse)
async def get_board(
    team_id: UUID | None = Query(default=None),
    assignee_id: UUID | None = Query(default=None),
    priority_id: UUID | None = Query(default=None),
    service: DashboardService = Depends(_get_service),
    current_user=Depends(get_current_user),
    role_codes: list[str] = Depends(get_current_role_codes),
    _: None = Depends(require_permission(DASHBOARD_OPERATIONAL)),
) -> BoardResponse:
    return await service.get_board(
        user_id=current_user.id,
        role_codes=role_codes,
        team_id=team_id,
        assignee_id=assignee_id,
        priority_id=priority_id,
    )


@router.get("/management", response_model=ManagementDashboardResponse)
async def get_management_dashboard(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    team_id: UUID | None = Query(default=None),
    priority_id: UUID | None = Query(default=None),
    ticket_type: str | None = Query(default=None),
    service: DashboardService = Depends(_get_service),
    role_codes: list[str] = Depends(get_current_role_codes),
    _: None = Depends(require_permission(DASHBOARD_MANAGEMENT)),
) -> ManagementDashboardResponse:
    now = datetime.utcnow()
    resolved_from = date_from or datetime(now.year, now.month, 1)
    resolved_to = date_to or now
    return await service.get_management_dashboard(
        role_codes=role_codes,
        date_from=resolved_from,
        date_to=resolved_to,
        team_id=team_id,
        priority_id=priority_id,
        ticket_type=ticket_type,
    )

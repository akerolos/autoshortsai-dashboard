"""Dashboard API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.common import ResponseEnvelope
from app.schemas.dashboard import DashboardOverviewSchema
from app.services.dashboard_service import DashboardService
from app.api.v1.dependencies import get_dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=ResponseEnvelope[DashboardOverviewSchema])
async def get_dashboard_overview(
    channel_id: str = "default",
    service: DashboardService = Depends(get_dashboard_service),
) -> ResponseEnvelope[DashboardOverviewSchema]:
    """يجلب كل بيانات الـ Dashboard Home في طلب واحد."""
    overview = await service.get_overview(channel_id)
    return ResponseEnvelope(data=overview)

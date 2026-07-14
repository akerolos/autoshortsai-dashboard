"""Analytics API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.analytics import AnalyticsOverviewSchema
from app.schemas.common import ResponseEnvelope
from app.services.analytics_service import AnalyticsService
from app.api.v1.dependencies import get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=ResponseEnvelope[AnalyticsOverviewSchema])
async def get_analytics_overview(
    channel_id: str = "default",
    service: AnalyticsService = Depends(get_analytics_service),
) -> ResponseEnvelope[AnalyticsOverviewSchema]:
    """نظرة عامة على التحليلات."""
    overview = await service.get_overview(channel_id)
    return ResponseEnvelope(data=overview)

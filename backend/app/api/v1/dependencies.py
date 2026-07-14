"""Common FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.analytics_service import AnalyticsService
from app.services.dashboard_service import DashboardService
from app.services.log_service import LogService
from app.services.pipeline_service import PipelineService
from app.services.settings_service import SettingsService
from app.services.video_service import VideoService


async def get_dashboard_service(
    session: AsyncSession = Depends(get_db),
) -> DashboardService:
    return DashboardService(session)


async def get_pipeline_service(
    session: AsyncSession = Depends(get_db),
) -> PipelineService:
    return PipelineService(session)


async def get_video_service(
    session: AsyncSession = Depends(get_db),
) -> VideoService:
    return VideoService(session)


async def get_analytics_service(
    session: AsyncSession = Depends(get_db),
) -> AnalyticsService:
    return AnalyticsService(session)


async def get_log_service(
    session: AsyncSession = Depends(get_db),
) -> LogService:
    return LogService(session)


async def get_settings_service(
    session: AsyncSession = Depends(get_db),
) -> SettingsService:
    return SettingsService(session)

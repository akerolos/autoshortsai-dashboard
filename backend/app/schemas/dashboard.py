"""Dashboard overview schema — aggregates everything needed for the home page."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.analytics import ChartSchema, StatCardSchema
from app.schemas.pipeline import PipelineOverviewSchema
from app.schemas.video import DashboardVideoSchema


class TodayRunSummarySchema(BaseModel):
    """ملخص run اليوم."""

    run_uid: str | None = None
    status: str = "waiting"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    execution_time_seconds: float | None = None
    current_stage: str | None = None
    current_progress: float = 0.0
    target_videos: int = 5
    completed_videos: int = 0
    failed_videos: int = 0
    color: str | None = None


class DashboardOverviewSchema(BaseModel):
    """كل ما تحتاجه صفحة Dashboard Home في طلب واحد."""

    today_run: TodayRunSummarySchema
    pipeline_overview: PipelineOverviewSchema
    today_videos: list[DashboardVideoSchema]
    stats: list[StatCardSchema]
    charts: list[ChartSchema]
    pipeline_stages: list[dict] = []

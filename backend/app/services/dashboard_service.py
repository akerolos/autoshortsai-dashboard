"""Dashboard service — aggregates everything for the home page."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stage import STAGE_DEFINITIONS
from app.repositories.pipeline_repo import PipelineRunRepository
from app.repositories.video_repo import VideoRepository
from app.schemas.analytics import ChartSchema, ChartSeriesSchema, StatCardSchema
from app.schemas.dashboard import DashboardOverviewSchema, TodayRunSummarySchema
from app.schemas.pipeline import PipelineOverviewSchema
from app.services.analytics_service import AnalyticsService
from app.services.pipeline_service import PipelineService
from app.services.video_service import VideoService
from app.utils.enums import STATUS_COLORS


class DashboardService:
    """يجمع كل البيانات اللازمة لصفحة Dashboard Home."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline_service = PipelineService(session)
        self.video_service = VideoService(session)
        self.analytics_service = AnalyticsService(session)
        self.run_repo = PipelineRunRepository(session)
        self.video_repo = VideoRepository(session)

    async def get_overview(self, channel_id: str = "default") -> DashboardOverviewSchema:
        """كل ما تحتاجه الصفحة الرئيسية في طلب واحد."""
        today_run = await self.run_repo.get_today_run(channel_id)
        pipeline_overview = await self.pipeline_service.get_overview(channel_id)
        today_videos = await self.video_service.get_today_videos(channel_id)
        stats = await self._compute_quick_stats(channel_id)
        charts = await self._compute_quick_charts(channel_id)

        # تعريف مراحل الـ pipeline (للـ UI حتى لو لم يوجد run)
        pipeline_stages = [
            {
                "key": s["key"],
                "name": s["name"],
                "icon": s["icon"],
                "status": "waiting",
                "color": STATUS_COLORS.get("waiting"),
            }
            for s in STAGE_DEFINITIONS
        ]

        # إذا وُجد run اليوم نحدّث المراحل بحالتها الحقيقية
        if today_run and today_run.stages:
            stage_map = {s.stage_key: s for s in today_run.stages}
            for stage in pipeline_stages:
                real = stage_map.get(stage["key"])
                if real:
                    stage["status"] = real.status
                    stage["color"] = STATUS_COLORS.get(real.status)
                    stage["progress"] = real.progress

        today_run_schema = TodayRunSummarySchema(
            run_uid=today_run.run_uid if today_run else None,
            status=today_run.status if today_run else "waiting",
            started_at=today_run.started_at if today_run else None,
            finished_at=today_run.finished_at if today_run else None,
            execution_time_seconds=today_run.execution_time_seconds if today_run else None,
            current_stage=today_run.current_stage if today_run else None,
            current_progress=today_run.current_progress if today_run else 0.0,
            target_videos=today_run.target_videos if today_run else 5,
            completed_videos=today_run.completed_videos if today_run else 0,
            failed_videos=today_run.failed_videos if today_run else 0,
            color=STATUS_COLORS.get(today_run.status if today_run else "waiting"),
        )

        return DashboardOverviewSchema(
            today_run=today_run_schema,
            pipeline_overview=pipeline_overview,
            today_videos=today_videos,
            stats=stats,
            charts=charts,
            pipeline_stages=pipeline_stages,
        )

    async def _compute_quick_stats(self, channel_id: str) -> list[StatCardSchema]:
        """إحصائيات سريعة للـ Dashboard."""
        totals = await self.video_repo.get_total_stats(channel_id)
        today_count = await self.video_repo.get_today_count(channel_id)
        success_rate = await self.video_repo.get_upload_success_rate(channel_id)

        return [
            StatCardSchema(
                label="Total Videos",
                value=totals["total_videos"],
                raw_value=totals["total_videos"],
                icon="film",
                color="#8B5CF6",
            ),
            StatCardSchema(
                label="Today's Videos",
                value=today_count,
                raw_value=today_count,
                icon="calendar",
                color="#3B82F6",
            ),
            StatCardSchema(
                label="Total Views",
                value=totals["total_views"],
                raw_value=totals["total_views"],
                icon="eye",
                color="#10B981",
            ),
            StatCardSchema(
                label="Avg CTR",
                value=f"{totals['avg_ctr']:.1f}%",
                raw_value=totals["avg_ctr"],
                unit="%",
                icon="mouse-pointer",
                color="#F59E0B",
            ),
            StatCardSchema(
                label="Avg Retention",
                value=f"{totals['avg_retention']:.1f}%",
                raw_value=totals["avg_retention"],
                unit="%",
                icon="clock",
                color="#06B6D4",
            ),
            StatCardSchema(
                label="Upload Success",
                value=f"{success_rate:.1f}%",
                raw_value=success_rate,
                unit="%",
                icon="check-circle",
                color="#10B981",
            ),
        ]

    async def _compute_quick_charts(self, channel_id: str) -> list[ChartSchema]:
        """Charts مختصرة للـ Dashboard."""
        from app.repositories.metric_repo import MetricRepository
        metric_repo = MetricRepository(self.session)

        views_series = await metric_repo.get_series("views", 14, channel_id)
        ctr_series = await metric_repo.get_series("ctr", 14, channel_id)

        return [
            ChartSchema(
                id="dashboard_views",
                title="Views (Last 14 Days)",
                type="line",
                series=[ChartSeriesSchema(
                    name="Views",
                    color="#3B82F6",
                    points=views_series,
                )],
                x_labels=[p["date"] for p in views_series],
            ),
            ChartSchema(
                id="dashboard_ctr",
                title="CTR (Last 14 Days)",
                type="bar",
                series=[ChartSeriesSchema(
                    name="CTR %",
                    color="#10B981",
                    points=ctr_series,
                )],
                x_labels=[p["date"] for p in ctr_series],
                unit="%",
            ),
        ]

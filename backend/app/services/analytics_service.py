"""Analytics service — computes statistics and chart data."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.metric_repo import MetricRepository
from app.repositories.pipeline_repo import PipelineRunRepository
from app.repositories.video_repo import VideoRepository
from app.schemas.analytics import (
    AnalyticsOverviewSchema,
    ChartSchema,
    ChartSeriesSchema,
    StatCardSchema,
)
from app.utils.enums import STATUS_COLORS


# ألوان الـ charts
CHART_COLORS = {
    "views": "#3B82F6",
    "subscribers": "#8B5CF6",
    "ctr": "#10B981",
    "retention": "#F59E0B",
    "render_time": "#EC4899",
    "execution_time": "#06B6D4",
    "videos_produced": "#A855F7",
}


class AnalyticsService:
    """منطق أعمال التحليلات."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.video_repo = VideoRepository(session)
        self.metric_repo = MetricRepository(session)
        self.pipeline_repo = PipelineRunRepository(session)

    async def get_overview(self, channel_id: str = "default") -> AnalyticsOverviewSchema:
        """نظرة عامة على التحليلات."""
        stats = await self._compute_stats(channel_id)
        charts = await self._build_charts(channel_id)

        top_videos = self._serialize_videos(
            await self.video_repo.get_top_videos(5, channel_id)
        )
        worst_videos = self._serialize_videos(
            await self.video_repo.get_worst_videos(5, channel_id)
        )

        # Best hooks (نستخدم أعلى CTR كـ proxy)
        all_top = await self.video_repo.get_top_videos(10, channel_id)
        best_hooks = [
            {
                "id": v.id,
                "title": v.title,
                "ctr": v.ctr,
                "retention": v.retention,
                "thumbnail_url": v.thumbnail_url,
            }
            for v in sorted(all_top, key=lambda x: x.ctr, reverse=True)[:5]
        ]
        avg_hook = sum(h["ctr"] for h in best_hooks) / len(best_hooks) if best_hooks else 0.0

        # Upload frequency (آخر 7 أيام)
        upload_freq = await self._compute_upload_frequency(channel_id)

        return AnalyticsOverviewSchema(
            stats=stats,
            charts=charts,
            top_videos=top_videos,
            worst_videos=worst_videos,
            best_hooks=best_hooks,
            avg_hook_performance=avg_hook,
            upload_frequency=upload_freq,
        )

    async def _compute_stats(self, channel_id: str) -> list[StatCardSchema]:
        """يحسب بطاقات الإحصائيات."""
        totals = await self.video_repo.get_total_stats(channel_id)
        today_count = await self.video_repo.get_today_count(channel_id)
        success_rate = await self.video_repo.get_upload_success_rate(channel_id)
        exec_time_avg = await self.pipeline_repo.get_execution_time_avg(channel_id)

        return [
            StatCardSchema(
                label="Total Videos Generated",
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
                label="Total Likes",
                value=totals["total_likes"],
                raw_value=totals["total_likes"],
                icon="heart",
                color="#EC4899",
            ),
            StatCardSchema(
                label="Average CTR",
                value=f"{totals['avg_ctr']:.1f}%",
                raw_value=totals["avg_ctr"],
                unit="%",
                icon="mouse-pointer",
                color="#F59E0B",
            ),
            StatCardSchema(
                label="Average Retention",
                value=f"{totals['avg_retention']:.1f}%",
                raw_value=totals["avg_retention"],
                unit="%",
                icon="clock",
                color="#06B6D4",
            ),
            StatCardSchema(
                label="Average Watch Time",
                value=f"{totals['avg_watch_time']:.0f}s",
                raw_value=totals["avg_watch_time"],
                unit="s",
                icon="play",
                color="#A855F7",
            ),
            StatCardSchema(
                label="Upload Success Rate",
                value=f"{success_rate:.1f}%",
                raw_value=success_rate,
                unit="%",
                icon="check-circle",
                color="#10B981",
            ),
            StatCardSchema(
                label="Average Render Time",
                value=f"{totals['avg_render_time']:.0f}s",
                raw_value=totals["avg_render_time"],
                unit="s",
                icon="cpu",
                color="#EF4444",
            ),
            StatCardSchema(
                label="Average Generation Time",
                value=f"{totals['avg_generation_time']:.0f}s",
                raw_value=totals["avg_generation_time"],
                unit="s",
                icon="zap",
                color="#7C3AED",
            ),
        ]

    async def _build_charts(self, channel_id: str) -> list[ChartSchema]:
        """يبني الـ charts."""
        charts: list[ChartSchema] = []

        # 1. Views (آخر 30 يوم)
        views_series = await self.metric_repo.get_series("views", 30, channel_id)
        charts.append(ChartSchema(
            id="views_chart",
            title="Views (Last 30 Days)",
            type="line",
            series=[ChartSeriesSchema(
                name="Views",
                color=CHART_COLORS["views"],
                points=views_series,
            )],
            x_labels=[p["date"] for p in views_series],
        ))

        # 2. Subscribers
        subs_series = await self.metric_repo.get_series("subscribers", 30, channel_id)
        charts.append(ChartSchema(
            id="subscribers_chart",
            title="Subscribers Growth",
            type="line",
            series=[ChartSeriesSchema(
                name="Subscribers",
                color=CHART_COLORS["subscribers"],
                points=subs_series,
            )],
            x_labels=[p["date"] for p in subs_series],
        ))

        # 3. CTR
        ctr_series = await self.metric_repo.get_series("ctr", 30, channel_id)
        charts.append(ChartSchema(
            id="ctr_chart",
            title="CTR (Last 30 Days)",
            type="bar",
            series=[ChartSeriesSchema(
                name="CTR %",
                color=CHART_COLORS["ctr"],
                points=ctr_series,
            )],
            x_labels=[p["date"] for p in ctr_series],
            unit="%",
        ))

        # 4. Retention
        ret_series = await self.metric_repo.get_series("retention", 30, channel_id)
        charts.append(ChartSchema(
            id="retention_chart",
            title="Retention Rate",
            type="line",
            series=[ChartSeriesSchema(
                name="Retention %",
                color=CHART_COLORS["retention"],
                points=ret_series,
            )],
            x_labels=[p["date"] for p in ret_series],
            unit="%",
        ))

        # 5. Render Time
        rt_series = await self.metric_repo.get_series("render_time", 30, channel_id)
        charts.append(ChartSchema(
            id="render_time_chart",
            title="Render Time (Avg)",
            type="bar",
            series=[ChartSeriesSchema(
                name="Render Time (s)",
                color=CHART_COLORS["render_time"],
                points=rt_series,
            )],
            x_labels=[p["date"] for p in rt_series],
            unit="s",
        ))

        # 6. Execution Time
        et_series = await self.metric_repo.get_series("execution_time", 30, channel_id)
        charts.append(ChartSchema(
            id="execution_time_chart",
            title="Pipeline Execution Time",
            type="line",
            series=[ChartSeriesSchema(
                name="Execution Time (s)",
                color=CHART_COLORS["execution_time"],
                points=et_series,
            )],
            x_labels=[p["date"] for p in et_series],
            unit="s",
        ))

        # 7. Video Production
        vp_series = await self.metric_repo.get_series("videos_produced", 30, channel_id)
        charts.append(ChartSchema(
            id="video_production_chart",
            title="Video Production Volume",
            type="bar",
            series=[ChartSeriesSchema(
                name="Videos",
                color=CHART_COLORS["videos_produced"],
                points=vp_series,
            )],
            x_labels=[p["date"] for p in vp_series],
        ))

        return charts

    async def _compute_upload_frequency(self, channel_id: str) -> dict:
        """توزيع الرفع خلال الأسبوع."""
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        today = date.today()
        week_ago = today - timedelta(days=7)

        # نستخدم بيانات وهمية منظمة من الـ metrics إن وُجدت
        series = await self.metric_repo.get_series("videos_produced", 7, channel_id)
        counts = [int(p["value"]) for p in series]
        # محاذاة مع أيام الأسبوع
        weekday = today.weekday()
        rotated = counts[-weekday:] + counts[:-weekday] if len(counts) == 7 else counts

        return {
            "labels": days,
            "values": rotated[:7] if len(rotated) >= 7 else rotated + [0] * (7 - len(rotated)),
        }

    @staticmethod
    def _serialize_videos(videos) -> list[dict]:
        """تحويل بسيط لـ dict."""
        return [
            {
                "id": v.id,
                "title": v.title,
                "thumbnail_url": v.thumbnail_url,
                "views": v.views,
                "ctr": v.ctr,
                "retention": v.retention,
                "avg_view_duration_seconds": v.avg_view_duration_seconds,
                "upload_date": v.upload_date.isoformat() if v.upload_date else None,
                "status": v.status,
                "color": STATUS_COLORS.get(v.status),
            }
            for v in videos
        ]

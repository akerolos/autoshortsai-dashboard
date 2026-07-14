"""Analytics-related schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class StatCardSchema(BaseModel):
    """بطاقة إحصائية."""

    label: str
    value: str | int | float
    raw_value: float | int | None = None
    unit: str | None = None
    change: float | None = None
    change_label: str | None = None
    icon: str | None = None
    color: str | None = None


class ChartSeriesSchema(BaseModel):
    """سلسلة بيانات لرسم chart."""

    name: str
    color: str
    points: list[dict]


class ChartSchema(BaseModel):
    """chart كامل."""

    id: str
    title: str
    type: str  # line | bar | donut | heatmap
    series: list[ChartSeriesSchema] = []
    x_labels: list[str] = []
    unit: str | None = None


class AnalyticsOverviewSchema(BaseModel):
    """نظرة عامة على التحليلات."""

    stats: list[StatCardSchema]
    charts: list[ChartSchema]
    top_videos: list[dict] = []
    worst_videos: list[dict] = []
    best_hooks: list[dict] = []
    avg_hook_performance: float | None = None
    upload_frequency: dict | None = None


class VideoPerformanceSchema(BaseModel):
    """أداء فيديو في الـ analytics."""

    id: int
    title: str
    thumbnail_url: str | None = None
    views: int
    ctr: float
    retention: float
    avg_view_duration_seconds: float
    upload_date: date | None = None

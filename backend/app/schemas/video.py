"""Video-related schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VideoSchema(BaseModel):
    """مخطط فيديو كامل."""

    id: int
    pipeline_run_id: int | None = None
    channel_id: str
    platform: str
    title: str
    description: str | None = None
    category: str
    thumbnail_url: str | None = None
    video_url: str | None = None
    duration_seconds: int
    status: str
    render_time_seconds: float | None = None
    upload_time_seconds: float | None = None
    generation_time_seconds: float | None = None
    upload_date: datetime | None = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    ctr: float = 0.0
    retention: float = 0.0
    avg_view_duration_seconds: float = 0.0
    external_video_id: str | None = None
    created_at: datetime
    updated_at: datetime
    color: str | None = None

    model_config = {"from_attributes": True}


class VideoListItemSchema(BaseModel):
    """مخطط مختصر لعنصر في قائمة الفيديوهات."""

    id: int
    title: str
    thumbnail_url: str | None = None
    duration_seconds: int
    status: str
    upload_date: datetime | None = None
    views: int = 0
    ctr: float = 0.0
    retention: float = 0.0
    platform: str
    color: str | None = None

    model_config = {"from_attributes": True}


class VideoFiltersSchema(BaseModel):
    """فلاتر البحث في الفيديوهات."""

    status: str | None = None
    platform: str | None = None
    category: str | None = None
    search: str | None = None
    sort_by: str = "upload_date"
    sort_order: str = "desc"


class DashboardVideoSchema(BaseModel):
    """مخطط فيديو في صفحة Dashboard (اليوم)."""

    id: int
    title: str
    status: str
    render_time_seconds: float | None = None
    upload_time_seconds: float | None = None
    thumbnail_url: str | None = None
    video_url: str | None = None
    duration_seconds: int
    color: str | None = None

    model_config = {"from_attributes": True}

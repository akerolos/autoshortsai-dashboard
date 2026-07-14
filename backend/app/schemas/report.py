"""Report schema — البيانات اللي بتيجي من GitHub Actions."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StageReportSchema(BaseModel):
    """تقرير مرحلة واحدة من الـ pipeline."""

    stage_key: str
    stage_name: str
    status: str = "completed"  # completed | failed | skipped
    progress: float = 100.0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    execution_time_seconds: float | None = None
    memory_usage_mb: float | None = None
    cpu_usage_percent: float | None = None
    current_task: str | None = None
    message: str | None = None
    error_message: str | None = None


class VideoReportSchema(BaseModel):
    """تقرير فيديو واحد تم إنتاجه."""

    title: str
    description: str | None = None
    category: str = "general"
    thumbnail_url: str | None = None
    video_url: str | None = None
    duration_seconds: int = 60
    status: str = "published"  # published | failed | pending
    render_time_seconds: float | None = None
    upload_time_seconds: float | None = None
    generation_time_seconds: float | None = None
    external_video_id: str | None = None
    niche: str | None = None
    hook: str | None = None
    script: str | None = None


class LogReportSchema(BaseModel):
    """سجل واحد من الـ pipeline."""

    level: str = "INFO"
    source: str = "system"
    message: str
    extra: dict | None = None
    timestamp: datetime | None = None


class PipelineReportSchema(BaseModel):
    """التقرير الكامل اللي بيتنبعت من GitHub Actions بعد كل run."""

    # معرّفات
    run_uid: str  # GitHub Actions run ID مثلاً
    channel_id: str = "default"
    platform: str = "youtube"

    # حالة الـ run
    status: str = "completed"  # completed | failed | partial
    target_videos: int = 5
    completed_videos: int = 0
    failed_videos: int = 0

    # الأوقات
    started_at: datetime
    finished_at: datetime | None = None
    execution_time_seconds: float | None = None

    # المراحل
    stages: list[StageReportSchema] = []

    # الفيديوهات
    videos: list[VideoReportSchema] = []

    # الـ logs
    logs: list[LogReportSchema] = []

    # معلومات إضافية
    github_run_id: str | None = None
    github_repository: str | None = None
    git_commit_sha: str | None = None
    error_message: str | None = None

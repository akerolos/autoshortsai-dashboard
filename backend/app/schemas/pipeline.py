"""Pipeline-related schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StageSchema(BaseModel):
    """مخطط مرحلة pipeline."""

    id: int
    stage_key: str
    stage_name: str
    order_index: int
    status: str
    progress: float = Field(ge=0, le=100)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    execution_time_seconds: float | None = None
    memory_usage_mb: float | None = None
    cpu_usage_percent: float | None = None
    current_task: str | None = None
    message: str | None = None
    error_message: str | None = None
    color: str | None = None

    model_config = {"from_attributes": True}


class PipelineRunSchema(BaseModel):
    """مخطط تنفيذ pipeline."""

    id: int
    run_uid: str
    channel_id: str
    status: str
    target_videos: int
    completed_videos: int
    failed_videos: int
    current_stage: str | None = None
    current_progress: float = Field(ge=0, le=100)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    execution_time_seconds: float | None = None
    error_message: str | None = None
    stages: list[StageSchema] = []
    color: str | None = None

    model_config = {"from_attributes": True}


class PipelineOverviewSchema(BaseModel):
    """نظرة عامة على pipeline اليوم."""

    today_run: PipelineRunSchema | None = None
    recent_runs: list[PipelineRunSchema] = []
    last_7_days_count: int = 0
    success_rate: float = 0.0


class StageUpdateSchema(BaseModel):
    """تحديث حالة مرحلة (للـ WebSocket)."""

    run_id: int
    stage_key: str
    status: str
    progress: float = 0.0
    current_task: str | None = None
    message: str | None = None
    error_message: str | None = None
    memory_usage_mb: float | None = None
    cpu_usage_percent: float | None = None
    timestamp: datetime | None = None

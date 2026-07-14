"""Log-related schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LogEntrySchema(BaseModel):
    """مخطط سجل واحد."""

    id: int
    pipeline_run_id: int | None = None
    level: str
    source: str
    message: str
    extra: str | None = None
    trace_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LogFiltersSchema(BaseModel):
    """فلاتر الـ logs."""

    level: str | None = None
    source: str | None = None
    search: str | None = None
    pipeline_run_id: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class LogEntryCreateSchema(BaseModel):
    """إنشاء سجل جديد."""

    level: str = Field(default="INFO")
    source: str = Field(default="system")
    message: str
    extra: str | None = None
    pipeline_run_id: int | None = None

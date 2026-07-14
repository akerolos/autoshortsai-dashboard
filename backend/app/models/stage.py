"""Stage model — represents a single stage within a pipeline run.

المراحل: content_engine, image_engine, narrator, whisper, timeline,
         render, quality_check, upload
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.pipeline_run import PipelineRun


# تعريف مراحل الـ pipeline بالترتيب
STAGE_DEFINITIONS: list[dict[str, str]] = [
    {"key": "content_engine", "name": "Content Engine", "icon": "file-text"},
    {"key": "image_engine", "name": "Image Engine", "icon": "image"},
    {"key": "narrator", "name": "Narrator", "icon": "mic"},
    {"key": "whisper", "name": "Whisper", "icon": "waveform"},
    {"key": "timeline", "name": "Timeline", "icon": "layers"},
    {"key": "render", "name": "Render", "icon": "film"},
    {"key": "quality_check", "name": "Quality Check", "icon": "check-circle"},
    {"key": "upload", "name": "Upload", "icon": "upload"},
]
STAGE_KEYS: list[str] = [s["key"] for s in STAGE_DEFINITIONS]


class Stage(Base, IDMixin, TimestampMixin):
    """مرحلة واحدة ضمن تنفيذ pipeline."""

    __tablename__ = "stages"
    __table_args__ = (
        Index("ix_stages_pipeline_run_id", "pipeline_run_id"),
        Index("ix_stages_status", "status"),
    )

    pipeline_run_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # معرّف المرحلة
    stage_key: Mapped[str] = mapped_column(String(64), nullable=False)
    stage_name: Mapped[str] = mapped_column(String(128), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # الحالة
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="waiting")
    # waiting | running | completed | failed | skipped

    # التقدم
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # الأوقات
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # الموارد المستهلكة
    memory_usage_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    cpu_usage_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    # المهمة الحالية والرسالة
    current_task: Mapped[str | None] = mapped_column(String(256), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # العلاقة
    pipeline_run: Mapped["PipelineRun"] = relationship(back_populates="stages")

    def __repr__(self) -> str:
        return f"<Stage(key={self.stage_key!r}, status={self.status!r})>"

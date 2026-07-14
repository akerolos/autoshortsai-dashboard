"""PipelineRun model — represents a single execution of the production pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.video import Video
    from app.models.stage import Stage
    from app.models.log import LogEntry


class PipelineRun(Base, IDMixin, TimestampMixin):
    """تنفيذ واحد لخط إنتاج الفيديوهات (يومياً عادةً)."""

    __tablename__ = "pipeline_runs"
    __table_args__ = (
        Index("ix_pipeline_runs_started_at", "started_at"),
        Index("ix_pipeline_runs_status", "status"),
    )

    # معرّف فريد للـ run
    run_uid: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    # القناة (Future-ready)
    channel_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default="default", index=True
    )

    # الحالة العامة
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="waiting")
    # القيم المحتملة: waiting | running | completed | failed | cancelled

    # عدد الفيديوهات المستهدفة
    target_videos: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    completed_videos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_videos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # المرحلة الحالية
    current_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # الأوقات
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # رسالة خطأ (إن وجدت)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # العلاقات
    videos: Mapped[list["Video"]] = relationship(
        back_populates="pipeline_run",
        lazy="selectin",
    )
    stages: Mapped[list["Stage"]] = relationship(
        back_populates="pipeline_run",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Stage.order_index",
    )
    logs: Mapped[list["LogEntry"]] = relationship(
        back_populates="pipeline_run",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<PipelineRun(id={self.id}, status={self.status!r})>"

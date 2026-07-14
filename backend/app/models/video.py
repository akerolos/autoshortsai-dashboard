"""Video model — represents a generated short video."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.pipeline_run import PipelineRun


class Video(Base, IDMixin, TimestampMixin):
    """فيديو تم إنتاجه عبر الـ pipeline."""

    __tablename__ = "videos"
    __table_args__ = (
        Index("ix_videos_upload_date", "upload_date"),
        Index("ix_videos_status", "status"),
        Index("ix_videos_channel_id", "channel_id"),
    )

    # العلاقة مع الـ pipeline run
    pipeline_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("pipeline_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # معرّف القناة (Future-ready: multi-channel)
    channel_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="default",
    )

    # المنصة (Future-ready: multi-platform)
    platform: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="youtube",
    )

    # المحتوى الأساسي
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    # الحالة
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    # القيم المحتملة: pending | rendering | uploading | published | failed

    # أوقات التنفيذ
    render_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    upload_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    generation_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # تاريخ النشر على المنصة
    upload_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # إحصائيات من المنصة (تُحدّث لاحقاً)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ctr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    retention: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_view_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # معرّفات خارجية
    external_video_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # العلاقات
    pipeline_run: Mapped["PipelineRun | None"] = relationship(
        back_populates="videos",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, title={self.title!r}, status={self.status!r})>"

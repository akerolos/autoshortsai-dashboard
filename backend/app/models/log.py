"""LogEntry model — structured application logs stored in DB."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.pipeline_run import PipelineRun


# مستويات الـ logs المدعومة
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "SUCCESS")


class LogEntry(Base, IDMixin, TimestampMixin):
    """سجل واحد في الـ logs."""

    __tablename__ = "logs"
    __table_args__ = (
        Index("ix_logs_level", "level"),
        Index("ix_logs_created_at", "created_at"),
        Index("ix_logs_pipeline_run_id", "pipeline_run_id"),
    )

    pipeline_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("pipeline_runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    level: Mapped[str] = mapped_column(String(16), nullable=False, default="INFO")
    # DEBUG | INFO | WARNING | ERROR | SUCCESS

    source: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    # مثلاً: content_engine | render | uploader | system

    message: Mapped[str] = mapped_column(Text, nullable=False)

    # بيانات إضافية (JSON string)
    extra: Mapped[str | None] = mapped_column(Text, nullable=True)

    # معرّف الـ trace
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # العلاقة
    pipeline_run: Mapped["PipelineRun | None"] = relationship(back_populates="logs")

    def __repr__(self) -> str:
        return f"<LogEntry(level={self.level!r}, source={self.source!r})>"

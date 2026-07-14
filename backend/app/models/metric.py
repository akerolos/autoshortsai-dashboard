"""DailyMetric model — aggregated metrics per day for charts and analytics."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class DailyMetric(Base, IDMixin, TimestampMixin):
    """إحصائيات يومية مُجمّعة لرسم الـ charts."""

    __tablename__ = "daily_metrics"
    __table_args__ = (
        UniqueConstraint("metric_date", "channel_id", "metric_key", name="uq_daily_metric"),
        Index("ix_daily_metrics_date_key", "metric_date", "metric_key"),
    )

    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    channel_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default="default"
    )

    # نوع المقياس: views | subscribers | ctr | retention | render_time | execution_time | videos_produced
    metric_key: Mapped[str] = mapped_column(String(64), nullable=False)

    # القيمة
    metric_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    def __repr__(self) -> str:
        return f"<DailyMetric(date={self.metric_date}, key={self.metric_key!r}, value={self.metric_value})>"

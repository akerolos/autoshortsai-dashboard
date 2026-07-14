"""Daily metric repository."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metric import DailyMetric
from app.repositories.base import BaseRepository


class MetricRepository(BaseRepository[DailyMetric]):
    """مستودع المقاييس اليومية."""

    model = DailyMetric

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_series(
        self,
        metric_key: str,
        days: int = 30,
        channel_id: str = "default",
    ) -> list[dict]:
        """سلسلة بيانات لمفتاح معيّن خلال آخر n يوم."""
        start_date = date.today() - timedelta(days=days - 1)
        result = await self.session.execute(
            select(DailyMetric)
            .where(DailyMetric.metric_key == metric_key)
            .where(DailyMetric.channel_id == channel_id)
            .where(DailyMetric.metric_date >= start_date)
            .order_by(DailyMetric.metric_date.asc())
        )
        rows = result.scalars().all()

        # ملء الأيام الناقصة بقيمة 0
        date_value_map = {r.metric_date: r.metric_value for r in rows}
        series = []
        for i in range(days):
            d = start_date + timedelta(days=i)
            series.append({
                "date": d.isoformat(),
                "value": float(date_value_map.get(d, 0.0)),
            })
        return series

    async def upsert_metric(
        self,
        metric_date: date,
        metric_key: str,
        metric_value: float,
        channel_id: str = "default",
    ) -> DailyMetric:
        """إدراج أو تحديث مقياس يومي."""
        result = await self.session.execute(
            select(DailyMetric)
            .where(DailyMetric.metric_date == metric_date)
            .where(DailyMetric.channel_id == channel_id)
            .where(DailyMetric.metric_key == metric_key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.metric_value = metric_value
            await self.session.flush()
            return existing
        return await self.create(
            metric_date=metric_date,
            channel_id=channel_id,
            metric_key=metric_key,
            metric_value=metric_value,
        )

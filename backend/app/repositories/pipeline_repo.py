"""Pipeline run repository."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pipeline_run import PipelineRun
from app.repositories.base import BaseRepository


class PipelineRunRepository(BaseRepository[PipelineRun]):
    """مستودع تنفيذات الـ pipeline."""

    model = PipelineRun

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_with_stages(self, run_id: int) -> PipelineRun | None:
        """يجلب run مع كل مراحله."""
        result = await self.session.execute(
            select(PipelineRun)
            .options(selectinload(PipelineRun.stages))
            .where(PipelineRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_today_run(self, channel_id: str = "default") -> PipelineRun | None:
        """آخر run لليوم."""
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await self.session.execute(
            select(PipelineRun)
            .options(selectinload(PipelineRun.stages))
            .where(PipelineRun.channel_id == channel_id)
            .where(PipelineRun.created_at >= today_start)
            .order_by(PipelineRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_recent_runs(self, limit: int = 10, channel_id: str = "default") -> list[PipelineRun]:
        """آخر n runs."""
        result = await self.session.execute(
            select(PipelineRun)
            .options(selectinload(PipelineRun.stages))
            .where(PipelineRun.channel_id == channel_id)
            .order_by(PipelineRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_last_7_days_count(self, channel_id: str = "default") -> int:
        """عدد runs آخر 7 أيام."""
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        result = await self.session.execute(
            select(func.count(PipelineRun.id))
            .where(PipelineRun.channel_id == channel_id)
            .where(PipelineRun.created_at >= week_ago)
        )
        return result.scalar() or 0

    async def get_success_rate(self, channel_id: str = "default") -> float:
        """نسبة نجاح الـ runs."""
        from sqlalchemy import case
        result = await self.session.execute(
            select(
                func.count(PipelineRun.id).label("total"),
                func.sum(
                    case(
                        (PipelineRun.status == "completed", 1),
                        else_=0,
                    )
                ).label("completed"),
            ).where(PipelineRun.channel_id == channel_id)
        )
        row = result.one()
        if not row.total:
            return 0.0
        return (row.completed or 0) * 100.0 / row.total

    async def get_execution_time_avg(self, channel_id: str = "default") -> float:
        """متوسط زمن التنفيذ."""
        result = await self.session.execute(
            select(func.avg(PipelineRun.execution_time_seconds))
            .where(PipelineRun.channel_id == channel_id)
            .where(PipelineRun.execution_time_seconds.isnot(None))
        )
        return float(result.scalar() or 0.0)

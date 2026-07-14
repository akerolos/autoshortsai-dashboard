"""Stage repository."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stage import Stage
from app.repositories.base import BaseRepository


class StageRepository(BaseRepository[Stage]):
    """مستودع المراحل."""

    model = Stage

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_run(self, run_id: int) -> list[Stage]:
        """كل مراحل run معيّن."""
        from sqlalchemy import select
        result = await self.session.execute(
            select(Stage)
            .where(Stage.pipeline_run_id == run_id)
            .order_by(Stage.order_index.asc())
        )
        return list(result.scalars().all())

    async def get_running_stage(self, run_id: int) -> Stage | None:
        """المرحلة قيد التشغيل حالياً."""
        from sqlalchemy import select
        result = await self.session.execute(
            select(Stage)
            .where(Stage.pipeline_run_id == run_id)
            .where(Stage.status == "running")
            .limit(1)
        )
        return result.scalar_one_or_none()

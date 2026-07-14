"""Log repository."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import LogEntry
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginatedResult, PaginationParams


class LogRepository(BaseRepository[LogEntry]):
    """مستودع الـ logs."""

    model = LogEntry

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_filtered(
        self,
        *,
        pagination: PaginationParams,
        level: str | None = None,
        source: str | None = None,
        search: str | None = None,
        pipeline_run_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> PaginatedResult:
        """يجلب الـ logs مع فلاتر."""
        query = select(LogEntry)

        if level:
            if level.upper() == "SUCCESS":
                query = query.where(LogEntry.level == "SUCCESS")
            else:
                query = query.where(LogEntry.level == level.upper())
        if source:
            query = query.where(LogEntry.source == source)
        if pipeline_run_id:
            query = query.where(LogEntry.pipeline_run_id == pipeline_run_id)
        if start_date:
            query = query.where(LogEntry.created_at >= start_date)
        if end_date:
            query = query.where(LogEntry.created_at <= end_date)
        if search:
            query = query.where(LogEntry.message.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        query = query.order_by(LogEntry.created_at.desc())
        query = query.offset(pagination.offset).limit(pagination.limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return PaginatedResult(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_sources(self) -> list[str]:
        """كل المصادر المختلفة."""
        result = await self.session.execute(
            select(LogEntry.source)
            .distinct()
            .order_by(LogEntry.source.asc())
        )
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 50) -> list[LogEntry]:
        """آخر n logs."""
        result = await self.session.execute(
            select(LogEntry)
            .order_by(LogEntry.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

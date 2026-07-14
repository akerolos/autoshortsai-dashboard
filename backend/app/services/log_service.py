"""Log service — manages application logs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.log_repo import LogRepository
from app.schemas.log import LogEntrySchema
from app.utils.pagination import PaginationParams
from app.websocket.manager import manager

logger = get_logger(__name__)


class LogService:
    """منطق أعمال الـ logs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = LogRepository(session)

    async def get_logs(
        self,
        pagination: PaginationParams,
        *,
        level: str | None = None,
        source: str | None = None,
        search: str | None = None,
        pipeline_run_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[list[LogEntrySchema], int]:
        """يجلب الـ logs مع فلاتر."""
        result = await self.repo.get_filtered(
            pagination=pagination,
            level=level,
            source=source,
            search=search,
            pipeline_run_id=pipeline_run_id,
            start_date=start_date,
            end_date=end_date,
        )
        items = [self._serialize(log) for log in result.items]
        return items, result.total

    async def get_sources(self) -> list[str]:
        """المصادر المتاحة."""
        return await self.repo.get_sources()

    async def add_log(
        self,
        *,
        level: str = "INFO",
        source: str = "system",
        message: str,
        extra: dict[str, Any] | None = None,
        pipeline_run_id: int | None = None,
        broadcast: bool = True,
    ) -> LogEntrySchema:
        """يضيف سجلاً جديداً ويبثه عبر WebSocket."""
        log = await self.repo.create(
            level=level.upper(),
            source=source,
            message=message,
            extra=json.dumps(extra) if extra else None,
            pipeline_run_id=pipeline_run_id,
        )
        await self.session.commit()

        serialized = self._serialize(log)

        if broadcast:
            await manager.broadcast_log(serialized.model_dump(mode="json"))

        return serialized

    async def get_for_download(
        self,
        *,
        level: str | None = None,
        source: str | None = None,
        search: str | None = None,
    ) -> list[LogEntrySchema]:
        """يجلب الـ logs للتحميل (بدون pagination)."""
        result = await self.repo.get_filtered(
            pagination=PaginationParams(page=1, page_size=10000),
            level=level,
            source=source,
            search=search,
        )
        return [self._serialize(log) for log in result.items]

    @staticmethod
    def _serialize(log) -> LogEntrySchema:
        return LogEntrySchema(
            id=log.id,
            pipeline_run_id=log.pipeline_run_id,
            level=log.level,
            source=log.source,
            message=log.message,
            extra=log.extra,
            trace_id=log.trace_id,
            created_at=log.created_at,
        )

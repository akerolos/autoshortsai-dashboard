"""Logs API routes."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from app.schemas.common import PaginatedResponse, ResponseEnvelope
from app.schemas.log import LogEntrySchema
from app.services.log_service import LogService
from app.api.v1.dependencies import get_log_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=ResponseEnvelope[PaginatedResponse[LogEntrySchema]])
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    level: str | None = None,
    source: str | None = None,
    search: str | None = None,
    pipeline_run_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    service: LogService = Depends(get_log_service),
) -> ResponseEnvelope[PaginatedResponse[LogEntrySchema]]:
    """قائمة الـ logs مع فلاتر."""
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = await service.get_logs(
        pagination,
        level=level,
        source=source,
        search=search,
        pipeline_run_id=pipeline_run_id,
        start_date=start_date,
        end_date=end_date,
    )
    paginated = PaginatedResponse(
        items=items,
        pagination={
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total,
            "total_pages": (total + pagination.page_size - 1) // pagination.page_size if pagination.page_size else 0,
            "has_next": pagination.page * pagination.page_size < total,
            "has_prev": pagination.page > 1,
        },
    )
    return ResponseEnvelope(data=paginated)


@router.get("/sources", response_model=ResponseEnvelope[list[str]])
async def get_sources(
    service: LogService = Depends(get_log_service),
) -> ResponseEnvelope[list[str]]:
    """المصادر المتاحة."""
    sources = await service.get_sources()
    return ResponseEnvelope(data=sources)


@router.get("/download", response_class=PlainTextResponse)
async def download_logs(
    level: str | None = None,
    source: str | None = None,
    search: str | None = None,
    service: LogService = Depends(get_log_service),
) -> PlainTextResponse:
    """تحميل الـ logs كملف نصي."""
    logs = await service.get_for_download(
        level=level,
        source=source,
        search=search,
    )
    lines = []
    for log in logs:
        extra = f" | extra={log.extra}" if log.extra else ""
        lines.append(
            f"[{log.created_at.isoformat()}] [{log.level}] [{log.source}] "
            f"run={log.pipeline_run_id}{extra} | {log.message}"
        )
    content = "\n".join(lines) if lines else "No logs found."
    return PlainTextResponse(
        content=content,
        headers={
            "Content-Disposition": f"attachment; filename=autoshortsai_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        },
    )

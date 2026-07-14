"""Videos API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.schemas.common import PaginatedResponse, ResponseEnvelope
from app.schemas.video import VideoListItemSchema, VideoSchema
from app.services.video_service import VideoService
from app.api.v1.dependencies import get_video_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("", response_model=ResponseEnvelope[PaginatedResponse[VideoListItemSchema]])
async def list_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    platform: str | None = None,
    category: str | None = None,
    search: str | None = None,
    sort_by: str = "upload_date",
    sort_order: str = "desc",
    channel_id: str = "default",
    service: VideoService = Depends(get_video_service),
) -> ResponseEnvelope[PaginatedResponse[VideoListItemSchema]]:
    """قائمة الفيديوهات مع فلاتر."""
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = await service.get_filtered_videos(
        pagination,
        status=status,
        platform=platform,
        category=category,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        channel_id=channel_id,
    )
    paginated = PaginatedResponse(
        items=items,
        pagination={
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total,
            "total_pages": (total + pagination.page_size - 1) // pagination.page_size,
            "has_next": pagination.page * pagination.page_size < total,
            "has_prev": pagination.page > 1,
        },
    )
    return ResponseEnvelope(data=paginated)


@router.get("/recent", response_model=ResponseEnvelope[list[VideoSchema]])
async def get_recent_videos(
    limit: int = Query(5, ge=1, le=50),
    channel_id: str = "default",
    service: VideoService = Depends(get_video_service),
) -> ResponseEnvelope[list[VideoSchema]]:
    """آخر فيديوهات."""
    videos = await service.get_recent(limit, channel_id)
    return ResponseEnvelope(data=videos)


@router.get("/{video_id}", response_model=ResponseEnvelope[VideoSchema])
async def get_video(
    video_id: int,
    service: VideoService = Depends(get_video_service),
) -> ResponseEnvelope[VideoSchema]:
    """فيديو واحد بالتفاصيل."""
    video = await service.get_video(video_id)
    return ResponseEnvelope(data=video)

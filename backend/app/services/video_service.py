"""Video service — business logic for videos."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.video_repo import VideoRepository
from app.schemas.video import DashboardVideoSchema, VideoListItemSchema, VideoSchema
from app.utils.enums import STATUS_COLORS
from app.utils.pagination import PaginationParams


class VideoService:
    """منطق أعمال الفيديوهات."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = VideoRepository(session)

    async def get_today_videos(self, channel_id: str = "default") -> list[DashboardVideoSchema]:
        """فيديوهات اليوم للـ Dashboard."""
        videos = await self.repo.get_today_videos(channel_id)
        return [
            DashboardVideoSchema(
                id=v.id,
                title=v.title,
                status=v.status,
                render_time_seconds=v.render_time_seconds,
                upload_time_seconds=v.upload_time_seconds,
                thumbnail_url=v.thumbnail_url,
                video_url=v.video_url,
                duration_seconds=v.duration_seconds,
                color=STATUS_COLORS.get(v.status),
            )
            for v in videos
        ]

    async def get_video(self, video_id: int) -> VideoSchema:
        """فيديو واحد بالتفاصيل."""
        video = await self.repo.get_by_id(video_id)
        if not video:
            raise NotFoundError(f"Video {video_id} not found")
        return self._serialize(video)

    async def get_filtered_videos(
        self,
        pagination: PaginationParams,
        *,
        status: str | None = None,
        platform: str | None = None,
        category: str | None = None,
        search: str | None = None,
        sort_by: str = "upload_date",
        sort_order: str = "desc",
        channel_id: str = "default",
    ) -> tuple[list[VideoListItemSchema], int]:
        """فيديوهات مع فلاتر."""
        result = await self.repo.get_filtered(
            pagination=pagination,
            status=status,
            platform=platform,
            category=category,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            channel_id=channel_id,
        )
        items = [self._serialize_list_item(v) for v in result.items]
        return items, result.total

    async def get_recent(self, limit: int = 5, channel_id: str = "default") -> list[VideoSchema]:
        """آخر فيديوهات."""
        videos = await self.repo.get_recent(limit, channel_id)
        return [self._serialize(v) for v in videos]

    @staticmethod
    def _serialize(v) -> VideoSchema:
        return VideoSchema(
            id=v.id,
            pipeline_run_id=v.pipeline_run_id,
            channel_id=v.channel_id,
            platform=v.platform,
            title=v.title,
            description=v.description,
            category=v.category,
            thumbnail_url=v.thumbnail_url,
            video_url=v.video_url,
            duration_seconds=v.duration_seconds,
            status=v.status,
            render_time_seconds=v.render_time_seconds,
            upload_time_seconds=v.upload_time_seconds,
            generation_time_seconds=v.generation_time_seconds,
            upload_date=v.upload_date,
            views=v.views,
            likes=v.likes,
            comments=v.comments,
            ctr=v.ctr,
            retention=v.retention,
            avg_view_duration_seconds=v.avg_view_duration_seconds,
            external_video_id=v.external_video_id,
            created_at=v.created_at,
            updated_at=v.updated_at,
            color=STATUS_COLORS.get(v.status),
        )

    @staticmethod
    def _serialize_list_item(v) -> VideoListItemSchema:
        return VideoListItemSchema(
            id=v.id,
            title=v.title,
            thumbnail_url=v.thumbnail_url,
            duration_seconds=v.duration_seconds,
            status=v.status,
            upload_date=v.upload_date,
            views=v.views,
            ctr=v.ctr,
            retention=v.retention,
            platform=v.platform,
            color=STATUS_COLORS.get(v.status),
        )

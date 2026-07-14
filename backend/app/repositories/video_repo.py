"""Video repository — specialized queries for videos."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginatedResult, PaginationParams


class VideoRepository(BaseRepository[Video]):
    """مستودع الفيديوهات."""

    model = Video

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_today_videos(self, channel_id: str = "default") -> list[Video]:
        """يجلب فيديوهات اليوم."""
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await self.session.execute(
            select(Video)
            .where(Video.channel_id == channel_id)
            .where(Video.created_at >= today_start)
            .order_by(Video.created_at.desc())
            .limit(10)
        )
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 5, channel_id: str = "default") -> list[Video]:
        """آخر n فيديوهات."""
        result = await self.session.execute(
            select(Video)
            .where(Video.channel_id == channel_id)
            .order_by(Video.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_filtered(
        self,
        *,
        pagination: PaginationParams,
        status: str | None = None,
        platform: str | None = None,
        category: str | None = None,
        search: str | None = None,
        sort_by: str = "upload_date",
        sort_order: str = "desc",
        channel_id: str = "default",
    ) -> PaginatedResult:
        """يجلب الفيديوهات مع فلاتر متقدمة."""
        query = select(Video).where(Video.channel_id == channel_id)

        if status:
            query = query.where(Video.status == status)
        if platform:
            query = query.where(Video.platform == platform)
        if category:
            query = query.where(Video.category == category)
        if search:
            query = query.where(Video.title.ilike(f"%{search}%"))

        # العد الإجمالي
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        # الترتيب
        sort_column = getattr(Video, sort_by, Video.upload_date)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc().nulls_last())

        query = query.offset(pagination.offset).limit(pagination.limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return PaginatedResult(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_total_stats(self, channel_id: str = "default") -> dict[str, Any]:
        """إحصائيات إجمالية سريعة."""
        result = await self.session.execute(
            select(
                func.count(Video.id).label("total_videos"),
                func.sum(Video.views).label("total_views"),
                func.sum(Video.likes).label("total_likes"),
                func.avg(Video.ctr).label("avg_ctr"),
                func.avg(Video.retention).label("avg_retention"),
                func.avg(Video.avg_view_duration_seconds).label("avg_watch_time"),
                func.avg(Video.render_time_seconds).label("avg_render_time"),
                func.avg(Video.generation_time_seconds).label("avg_generation_time"),
            ).where(Video.channel_id == channel_id)
        )
        row = result.one()
        return {
            "total_videos": row.total_videos or 0,
            "total_views": int(row.total_views or 0),
            "total_likes": int(row.total_likes or 0),
            "avg_ctr": float(row.avg_ctr or 0.0),
            "avg_retention": float(row.avg_retention or 0.0),
            "avg_watch_time": float(row.avg_watch_time or 0.0),
            "avg_render_time": float(row.avg_render_time or 0.0),
            "avg_generation_time": float(row.avg_generation_time or 0.0),
        }

    async def get_today_count(self, channel_id: str = "default") -> int:
        """عدد فيديوهات اليوم."""
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await self.session.execute(
            select(func.count(Video.id))
            .where(Video.channel_id == channel_id)
            .where(Video.created_at >= today_start)
        )
        return result.scalar() or 0

    async def get_upload_success_rate(self, channel_id: str = "default") -> float:
        """نسبة نجاح الرفع."""
        from sqlalchemy import case
        result = await self.session.execute(
            select(
                func.count(Video.id).label("total"),
                func.sum(
                    case(
                        (Video.status == "published", 1),
                        else_=0,
                    )
                ).label("published"),
            ).where(Video.channel_id == channel_id)
        )
        row = result.one()
        if not row.total:
            return 0.0
        return (row.published or 0) * 100.0 / row.total

    async def get_top_videos(self, limit: int = 5, channel_id: str = "default") -> list[Video]:
        """أفضل الفيديوهات حسب المشاهدات."""
        result = await self.session.execute(
            select(Video)
            .where(Video.channel_id == channel_id)
            .order_by(Video.views.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_worst_videos(self, limit: int = 5, channel_id: str = "default") -> list[Video]:
        """أسوأ الفيديوهات حسب المشاهدات (من المنشورة)."""
        result = await self.session.execute(
            select(Video)
            .where(Video.channel_id == channel_id)
            .where(Video.status == "published")
            .order_by(Video.views.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_views_last_n_days(
        self, days: int = 30, channel_id: str = "default"
    ) -> list[dict]:
        """مشاهدات آخر n يوم."""
        start_date = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(
                func.date(Video.upload_date).label("d"),
                func.sum(Video.views).label("v"),
            )
            .where(Video.channel_id == channel_id)
            .where(Video.upload_date.isnot(None))
            .where(func.date(Video.upload_date) >= start_date)
            .group_by(func.date(Video.upload_date))
            .order_by(func.date(Video.upload_date).asc())
        )
        return [{"date": str(r.d), "value": int(r.v or 0)} for r in result.all()]

"""Base async repository — generic CRUD operations."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.utils.pagination import PaginatedResult, PaginationParams

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """مستودع عام يوفر عمليات CRUD أساسية."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, id: int) -> ModelT | None:
        """يجلب سجلاً واحداً بالـ id."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        pagination: PaginationParams | None = None,
        filters: dict[str, Any] | None = None,
        order_by: Any | None = None,
    ) -> PaginatedResult:
        """يجلب عدة سجلات مع pagination و filters."""
        query = select(self.model)

        # تطبيق الفلاتر
        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        # العد الإجمالي
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # الترتيب
        if order_by is not None:
            query = query.order_by(order_by)

        # الـ pagination
        if pagination:
            query = query.offset(pagination.offset).limit(pagination.limit)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return PaginatedResult(
            items=items,
            total=total,
            page=pagination.page if pagination else 1,
            page_size=pagination.page_size if pagination else len(items),
        )

    async def create(self, **kwargs: Any) -> ModelT:
        """ينشئ سجلاً جديداً."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelT, **kwargs: Any) -> ModelT:
        """يحدّث سجلاً موجوداً."""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        """يحذف سجلاً."""
        await self.session.delete(instance)
        await self.session.flush()

    async def count(self, **filters: Any) -> int:
        """يعد السجلات المطابقة."""
        query = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        result = await self.session.execute(query)
        return result.scalar() or 0

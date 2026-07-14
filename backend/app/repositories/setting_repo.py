"""Setting repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import DEFAULT_SETTINGS, Setting
from app.repositories.base import BaseRepository


class SettingRepository(BaseRepository[Setting]):
    """مستودع الإعدادات."""

    model = Setting

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_all(self) -> list[Setting]:
        """كل الإعدادات."""
        result = await self.session.execute(
            select(Setting).order_by(Setting.category.asc(), Setting.key.asc())
        )
        return list(result.scalars().all())

    async def get_by_key(self, key: str) -> Setting | None:
        """إعداد واحد بالمفتاح."""
        result = await self.session.execute(
            select(Setting).where(Setting.key == key)
        )
        return result.scalar_one_or_none()

    async def get_by_category(self, category: str) -> list[Setting]:
        """إعدادات فئة معيّنة."""
        result = await self.session.execute(
            select(Setting)
            .where(Setting.category == category)
            .order_by(Setting.key.asc())
        )
        return list(result.scalars().all())

    async def get_categories(self) -> list[str]:
        """كل الفئات."""
        result = await self.session.execute(
            select(Setting.category).distinct().order_by(Setting.category.asc())
        )
        return list(result.scalars().all())

    async def update_value(self, key: str, value: str) -> Setting | None:
        """تحديث قيمة إعداد."""
        setting = await self.get_by_key(key)
        if setting:
            setting.value = value
            await self.session.flush()
            await self.session.refresh(setting)
        return setting

    async def seed_defaults(self) -> int:
        """يزرع الإعدادات الافتراضية إذا لم تكن موجودة."""
        count = 0
        for item in DEFAULT_SETTINGS:
            existing = await self.get_by_key(item["key"])
            if not existing:
                await self.create(**item)
                count += 1
        return count

    async def get_value(self, key: str, default: Any = None) -> Any:
        """يجلب القيمة كـ Python type."""
        setting = await self.get_by_key(key)
        if not setting:
            return default
        return self._cast_value(setting.value, setting.value_type)

    @staticmethod
    def _cast_value(value: str, value_type: str) -> Any:
        """يحوّل القيمة من string إلى نوعها الأصلي."""
        if value_type == "int":
            try:
                return int(value)
            except ValueError:
                return 0
        if value_type == "float":
            try:
                return float(value)
            except ValueError:
                return 0.0
        if value_type == "bool":
            return value.lower() in ("true", "1", "yes")
        if value_type == "json":
            import json
            try:
                return json.loads(value)
            except Exception:
                return {}
        return value

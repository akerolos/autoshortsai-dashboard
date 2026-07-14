"""Settings service."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.setting_repo import SettingRepository
from app.schemas.settings import (
    SettingSchema,
    SettingsGroupSchema,
    SettingsResponseSchema,
    SettingUpdateSchema,
)
from app.websocket.events import EventType
from app.websocket.manager import manager


class SettingsService:
    """منطق أعمال الإعدادات."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SettingRepository(session)

    async def get_all(self) -> SettingsResponseSchema:
        """كل الإعدادات مجمّعة حسب الفئة."""
        all_settings = await self.repo.get_all()
        categories = await self.repo.get_categories()

        groups = []
        for cat in categories:
            cat_settings = [s for s in all_settings if s.category == cat]
            groups.append(SettingsGroupSchema(
                category=cat,
                settings=[self._serialize(s) for s in cat_settings],
            ))

        return SettingsResponseSchema(
            groups=groups,
            all=[self._serialize(s) for s in all_settings],
        )

    async def get_by_key(self, key: str) -> SettingSchema:
        """إعداد واحد."""
        setting = await self.repo.get_by_key(key)
        if not setting:
            raise NotFoundError(f"Setting '{key}' not found")
        return self._serialize(setting)

    async def update(self, key: str, payload: SettingUpdateSchema) -> SettingSchema:
        """تحديث إعداد."""
        setting = await self.repo.update_value(key, payload.value)
        if not setting:
            raise NotFoundError(f"Setting '{key}' not found")

        # validation إضافية
        if setting.value_type == "int":
            try:
                int(payload.value)
            except ValueError:
                raise ValidationError(f"Value must be an integer for setting '{key}'")
        elif setting.value_type == "float":
            try:
                float(payload.value)
            except ValueError:
                raise ValidationError(f"Value must be a float for setting '{key}'")

        await self.session.commit()

        # إشعار WebSocket
        await manager.broadcast("settings", EventType.SETTING_UPDATED, {
            "key": key,
            "value": payload.value,
            "value_type": setting.value_type,
        })

        return self._serialize(setting)

    async def seed_defaults(self) -> int:
        """يزرع الإعدادات الافتراضية."""
        count = await self.repo.seed_defaults()
        if count:
            await self.session.commit()
        return count

    @staticmethod
    def _serialize(s) -> SettingSchema:
        return SettingSchema(
            id=s.id,
            key=s.key,
            value=s.value,
            value_type=s.value_type,
            category=s.category,
            description=s.description,
        )

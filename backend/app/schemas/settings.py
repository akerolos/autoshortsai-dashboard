"""Settings-related schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SettingSchema(BaseModel):
    """مخطط إعداد واحد."""

    id: int
    key: str
    value: str
    value_type: str
    category: str
    description: str | None = None

    model_config = {"from_attributes": True}


class SettingUpdateSchema(BaseModel):
    """تحديث إعداد."""

    value: str = Field(..., min_length=1)


class SettingsGroupSchema(BaseModel):
    """مجموعة إعدادات حسب الفئة."""

    category: str
    settings: list[SettingSchema]


class SettingsResponseSchema(BaseModel):
    """كل الإعدادات مجمّعة حسب الفئة."""

    groups: list[SettingsGroupSchema]
    all: list[SettingSchema]

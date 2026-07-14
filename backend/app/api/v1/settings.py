"""Settings API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.common import ResponseEnvelope
from app.schemas.settings import SettingSchema, SettingsResponseSchema, SettingUpdateSchema
from app.services.settings_service import SettingsService
from app.api.v1.dependencies import get_settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=ResponseEnvelope[SettingsResponseSchema])
async def get_all_settings(
    service: SettingsService = Depends(get_settings_service),
) -> ResponseEnvelope[SettingsResponseSchema]:
    """كل الإعدادات."""
    settings = await service.get_all()
    return ResponseEnvelope(data=settings)


@router.get("/{key}", response_model=ResponseEnvelope[SettingSchema])
async def get_setting(
    key: str,
    service: SettingsService = Depends(get_settings_service),
) -> ResponseEnvelope[SettingSchema]:
    """إعداد واحد."""
    setting = await service.get_by_key(key)
    return ResponseEnvelope(data=setting)


@router.patch("/{key}", response_model=ResponseEnvelope[SettingSchema])
async def update_setting(
    key: str,
    payload: SettingUpdateSchema,
    service: SettingsService = Depends(get_settings_service),
) -> ResponseEnvelope[SettingSchema]:
    """تحديث إعداد."""
    setting = await service.update(key, payload)
    return ResponseEnvelope(data=setting)

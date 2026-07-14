"""Setting model — key-value application settings."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class Setting(Base, IDMixin, TimestampMixin):
    """إعداد تطبيق على شكل key-value."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(32), nullable=False, default="string")
    # string | int | float | bool | json

    category: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Setting(key={self.key!r}, value={self.value!r})>"


# الإعدادات الافتراضية
DEFAULT_SETTINGS: list[dict[str, object]] = [
    {
        "key": "videos_per_day",
        "value": "5",
        "value_type": "int",
        "category": "production",
        "description": "Number of videos to generate per day",
    },
    {
        "key": "narrator_voice",
        "value": "ar-MA-Jawad",
        "value_type": "string",
        "category": "narrator",
        "description": "Voice model used for narration",
    },
    {
        "key": "speech_rate",
        "value": "1.0",
        "value_type": "float",
        "category": "narrator",
        "description": "Speech playback rate multiplier",
    },
    {
        "key": "category",
        "value": "technology",
        "value_type": "string",
        "category": "production",
        "description": "Content category for video generation",
    },
    {
        "key": "prompt_version",
        "value": "v2.1",
        "value_type": "string",
        "category": "production",
        "description": "Version of the prompt template in use",
    },
    {
        "key": "upload_time",
        "value": "18:00",
        "value_type": "string",
        "category": "upload",
        "description": "Scheduled upload time (HH:MM, 24h format)",
    },
    {
        "key": "output_resolution",
        "value": "1080x1920",
        "value_type": "string",
        "category": "render",
        "description": "Output video resolution (width x height)",
    },
    {
        "key": "video_duration_seconds",
        "value": "60",
        "value_type": "int",
        "category": "render",
        "description": "Target video duration in seconds",
    },
    {
        "key": "subtitle_style",
        "value": "modern-bold",
        "value_type": "string",
        "category": "render",
        "description": "Subtitle visual style preset",
    },
    {
        "key": "theme",
        "value": "dark",
        "value_type": "string",
        "category": "ui",
        "description": "Dashboard theme (dark | light)",
    },
    {
        "key": "language",
        "value": "ar",
        "value_type": "string",
        "category": "ui",
        "description": "Dashboard interface language",
    },
    {
        "key": "active_channel_id",
        "value": "default",
        "value_type": "string",
        "category": "channels",
        "description": "Currently active channel identifier",
    },
]

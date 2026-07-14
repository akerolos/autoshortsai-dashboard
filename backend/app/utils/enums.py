"""Enums and constants shared across the application."""

from __future__ import annotations

from enum import StrEnum


class VideoStatus(StrEnum):
    PENDING = "pending"
    RENDERING = "rendering"
    UPLOADING = "uploading"
    PUBLISHED = "published"
    FAILED = "failed"


class PipelineStatus(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageStatus(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class Platform(StrEnum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"


# ألوان الـ statuses للواجهة (تُرسل عبر API)
STATUS_COLORS: dict[str, str] = {
    "running": "#3B82F6",
    "completed": "#10B981",
    "failed": "#EF4444",
    "waiting": "#F59E0B",
    "pending": "#F59E0B",
    "publishing": "#3B82F6",
    "published": "#10B981",
    "cancelled": "#71717A",
    "skipped": "#71717A",
    "idle": "#71717A",
}

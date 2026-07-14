"""WebSocket event types."""

from __future__ import annotations

from enum import StrEnum


class EventType(StrEnum):
    """أنواع الأحداث في WebSocket."""

    # Pipeline
    PIPELINE_RUN_UPDATE = "pipeline_run_update"
    STAGE_UPDATE = "stage_update"

    # Logs
    LOG_NEW = "log_new"

    # Stats
    STATS_UPDATE = "stats_update"

    # Settings
    SETTING_UPDATED = "setting_updated"

    # System
    PING = "ping"
    PONG = "pong"
    CONNECTED = "connected"
    ERROR = "error"


class WSTopic(StrEnum):
    """مواضيع الاشتراك في WebSocket."""

    PIPELINE = "pipeline"
    LOGS = "logs"
    STATS = "stats"
    ALL = "all"

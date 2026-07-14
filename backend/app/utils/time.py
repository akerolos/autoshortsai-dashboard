"""Time and duration formatting utilities."""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Timezone-aware UTC now."""
    return datetime.now(timezone.utc)


def format_duration(seconds: float | None) -> str:
    """يحوّل الثواني إلى صيغة مقروءة: '2m 15s' أو '1h 5m'."""
    if seconds is None:
        return "—"
    if seconds < 0:
        return "—"
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"

    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def format_number(value: int | float) -> str:
    """يحوّل الأرقام الكبيرة: 1500 → 1.5K, 1500000 → 1.5M."""
    if value is None:
        return "0"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, int):
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if abs(value) >= 1_000:
            return f"{value / 1_000:.1f}K"
        return str(value)
    return f"{value:.1f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """يحوّل نسبة مئوية: 65.4 → '65.4%'."""
    if value is None:
        return "—"
    return f"{value:.{decimals}f}%"


def format_datetime(dt: datetime | None, fmt: str = "%H:%M:%S") -> str:
    """يهيّئ datetime إلى صيغة مقروءة."""
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(fmt)


def time_ago(dt: datetime | None) -> str:
    """يرجع صيغة 'منذ كم': 'منذ 5 دقائق', 'منذ ساعتين'."""
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = utcnow()
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"

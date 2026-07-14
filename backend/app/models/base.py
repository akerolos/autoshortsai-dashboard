"""SQLAlchemy declarative base and shared mixins."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """يرجع الوقت الحالي بتوقيت UTC كـ timezone-aware."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """القاعدة المشتركة لكل الـ models."""
    pass


class TimestampMixin:
    """Mixin يضيف created_at و updated_at لكل جدول."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class IDMixin:
    """Mixin يضيف عمود id كـ primary key (UUID string)."""

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        index=True,
    )

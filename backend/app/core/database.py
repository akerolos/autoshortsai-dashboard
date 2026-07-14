"""Database engine and session management.

يوفر AsyncEngine و async_sessionmaker لـ SQLAlchemy.
يستخدم aiosqlite كـ async driver لـ SQLite.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


# إنشاء الـ AsyncEngine
engine = create_async_engine(
    settings.resolved_database_url,
    echo=settings.is_development and settings.app_debug,
    future=True,
    # إعدادات خاصة بـ SQLite
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

# مصنع الـ sessions
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency لحقن الـ session في الـ routes.

    يتم إغلاق الـ session تلقائياً بعد انتهاء الطلب.
    في حالة الخطأ يتم عمل rollback.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """ينشئ كل الجداول (يُستخدم عند بدء التشغيل في وضع التطوير).

    في الإنتاج يُفضّل استخدام Alembic migrations.
    """
    from app.models.base import Base
    # استيراد كل الـ models لتسجيلها في الـ metadata
    from app.models import (  # noqa: F401
        video,
        pipeline_run,
        stage,
        log,
        metric,
        setting,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """يُغلق الـ engine عند إيقاف التطبيق."""
    await engine.dispose()

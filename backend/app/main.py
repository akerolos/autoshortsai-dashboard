"""AutoShortsAI Dashboard — FastAPI application entry point.

يقوم بـ:
- إنشاء FastAPI app
- تسجيل middleware و exception handlers
- تضمين الـ API router
- خدمة الملفات الثابتة (frontend)
- startup/shutdown events
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.logging import get_logger, setup_logging
from app.core.middleware import setup_exception_handlers, setup_middleware
from app.websocket.manager import manager

logger = get_logger(__name__)

# المسار للـ frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """دورة حياة التطبيق: startup + shutdown."""
    # === Startup ===
    setup_logging()
    logger.info(
        "Starting AutoShortsAI Dashboard",
        env=settings.app_env,
        debug=settings.app_debug,
    )

    # تهيئة قاعدة البيانات
    await init_db()
    logger.info("Database initialized")

    # تحميل نسخة من الـ DB من GitHub (لو متفعّل)
    try:
        from app.core.github_storage import github_storage
        from app.core.config import settings
        if github_storage.enabled:
            db_path = settings.resolved_database_url.split(":///")[-1]
            await github_storage.download_db(db_path)
            logger.info("DB sync from GitHub completed")
    except Exception as e:
        logger.warning(f"Failed to sync DB from GitHub: {e}")

    # زرع البيانات التجريبية في وضع التطوير فقط (لو ENABLE_SEED=true)
    import os
    enable_seed = os.environ.get("ENABLE_SEED", "").lower() in ("true", "1", "yes")
    if settings.is_development and enable_seed:
        try:
            from app.seed import seed_all
            await seed_all()
        except Exception as e:
            logger.warning(f"Seeding skipped or failed: {e}")
    else:
        # نضمن بس إن الجداول والإعدادات الافتراضية موجودة
        try:
            from app.services.settings_service import SettingsService
            from app.core.database import async_session_factory
            async with async_session_factory() as session:
                service = SettingsService(session)
                count = await service.seed_defaults()
                if count:
                    logger.info(f"Seeded {count} default settings")
        except Exception as e:
            logger.warning(f"Settings seeding failed: {e}")

    logger.info(f"WebSocket connections: {manager.connection_count}")
    logger.info("AutoShortsAI Dashboard is ready!")

    yield

    # === Shutdown ===
    logger.info("Shutting down AutoShortsAI Dashboard...")
    await manager.shutdown()
    await close_db()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """ينشئ ويهيّئ تطبيق FastAPI."""
    app = FastAPI(
        title=settings.app_name,
        description="Mission Control Dashboard for AutoShortsAI",
        version="1.0.0",
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        openapi_url="/api/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Middleware + Exception handlers
    setup_middleware(app)
    setup_exception_handlers(app)

    # API routes
    app.include_router(api_router)

    # Health check
    @app.get("/api/health", tags=["health"])
    async def health_check() -> dict:
        return {
            "status": "ok",
            "app_name": settings.app_name,
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # خدمة الملفات الثابتة للـ frontend (CSS, JS, icons)
    if FRONTEND_DIR.exists():
        assets_dir = FRONTEND_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        # خدمة index.html و fallback للـ SPA routing
        @app.get("/", include_in_schema=False)
        async def serve_index():
            return FileResponse(str(FRONTEND_DIR / "index.html"))

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            # إذا كان المسار ملف API نتجاهله
            if full_path.startswith("api") or full_path.startswith("ws"):
                return {"detail": "Not Found"}
            # نحاول خدمة الملف مباشرة إن وُجد
            file_path = FRONTEND_DIR / full_path
            if file_path.is_file():
                return FileResponse(str(file_path))
            # وإلا نرجّع index.html (SPA fallback)
            index = FRONTEND_DIR / "index.html"
            if index.exists():
                return FileResponse(str(index))
            return {"detail": "Not Found"}

    return app


# إنشاء التطبيق
app = create_app()

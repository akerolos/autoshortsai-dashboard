"""Structured logging configuration using structlog.

يدعم صيغتين:
- JSON (للإنتاج)
- Console pretty (للتطوير)
"""

from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import settings


def setup_logging() -> None:
    """يهيئ structlog و standard logging معاً."""

    # معالجة مشتركة للأزمنة
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_json or settings.is_production:
        # صيغة JSON للإنتاج
        renderer = structlog.processors.JSONRenderer()
    else:
        # صيغة pretty ملونة للتطوير
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # تهيئة standard logging للتوافق مع مكتبات الطرف الثالث
    logging.basicConfig(
        level=logging.getLevelName(settings.log_level),
        format="%(message)s",
        stream=sys.stdout,
    )

    # تقليل ضجيج المكتبات الداخلية
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "alembic"):
        logging.getLogger(noisy).setLevel(
            logging.DEBUG if settings.app_debug and settings.is_development
            else logging.WARNING
        )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """يرجع logger جاهز للاستخدام."""
    return structlog.get_logger(name)

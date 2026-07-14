#!/usr/bin/env python
"""Uvicorn launcher for AutoShortsAI Dashboard."""

import uvicorn

from app.core.config import settings


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
        access_log=settings.app_debug,
    )

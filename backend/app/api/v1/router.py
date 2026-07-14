"""Aggregator router for API v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.logs import router as logs_router
from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.report import router as report_router
from app.api.v1.settings import router as settings_router
from app.api.v1.videos import router as videos_router
from app.api.v1.ws import router as ws_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(dashboard_router)
api_router.include_router(pipeline_router)
api_router.include_router(videos_router)
api_router.include_router(analytics_router)
api_router.include_router(logs_router)
api_router.include_router(settings_router)
api_router.include_router(report_router)
api_router.include_router(ws_router)

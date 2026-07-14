"""Pipeline API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.schemas.common import ResponseEnvelope
from app.schemas.pipeline import PipelineOverviewSchema, PipelineRunSchema
from app.services.pipeline_service import PipelineService
from app.api.v1.dependencies import get_pipeline_service

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/overview", response_model=ResponseEnvelope[PipelineOverviewSchema])
async def get_pipeline_overview(
    channel_id: str = "default",
    service: PipelineService = Depends(get_pipeline_service),
) -> ResponseEnvelope[PipelineOverviewSchema]:
    """نظرة عامة على الـ pipeline."""
    overview = await service.get_overview(channel_id)
    return ResponseEnvelope(data=overview)


@router.get("/today", response_model=ResponseEnvelope[PipelineRunSchema | None])
async def get_today_run(
    channel_id: str = "default",
    service: PipelineService = Depends(get_pipeline_service),
) -> ResponseEnvelope[PipelineRunSchema | None]:
    """آخر run لليوم."""
    run = await service.get_today_run(channel_id)
    if not run:
        return ResponseEnvelope(data=None)
    return ResponseEnvelope(data=service.serialize_run(run))


@router.get("/recent", response_model=ResponseEnvelope[list[PipelineRunSchema]])
async def get_recent_runs(
    limit: int = Query(10, ge=1, le=50),
    channel_id: str = "default",
    service: PipelineService = Depends(get_pipeline_service),
) -> ResponseEnvelope[list[PipelineRunSchema]]:
    """آخر runs."""
    runs = await service.get_recent_runs(limit, channel_id)
    return ResponseEnvelope(data=[service.serialize_run(r) for r in runs])


@router.get("/{run_id}", response_model=ResponseEnvelope[PipelineRunSchema])
async def get_run(
    run_id: int,
    service: PipelineService = Depends(get_pipeline_service),
) -> ResponseEnvelope[PipelineRunSchema]:
    """run واحد بالتفاصيل."""
    run = await service.get_run_with_stages(run_id)
    return ResponseEnvelope(data=service.serialize_run(run))


@router.post("/runs", response_model=ResponseEnvelope[PipelineRunSchema])
async def create_run(
    target_videos: int = 5,
    channel_id: str = "default",
    service: PipelineService = Depends(get_pipeline_service),
) -> ResponseEnvelope[PipelineRunSchema]:
    """ينشئ run جديداً."""
    run = await service.create_run(target_videos, channel_id)
    return ResponseEnvelope(data=service.serialize_run(run))


@router.post("/runs/{run_id}/start", response_model=ResponseEnvelope[PipelineRunSchema])
async def start_run(
    run_id: int,
    service: PipelineService = Depends(get_pipeline_service),
) -> ResponseEnvelope[PipelineRunSchema]:
    """يبدأ run."""
    run = await service.start_run(run_id)
    return ResponseEnvelope(data=service.serialize_run(run))

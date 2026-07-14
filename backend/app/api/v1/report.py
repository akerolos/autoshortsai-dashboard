"""Report API routes — endpoint لاستقبال تقارير GitHub Actions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Security

from app.core.logging import get_logger
from app.core.security import get_api_key
from app.schemas.common import ResponseEnvelope
from app.schemas.report import PipelineReportSchema
from app.services.report_service import ReportService
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

logger = get_logger(__name__)

router = APIRouter(prefix="/report", tags=["report"])


@router.post("/pipeline", response_model=ResponseEnvelope)
async def receive_pipeline_report(
    report: PipelineReportSchema,
    session: AsyncSession = Depends(get_db),
    api_key: str = Security(get_api_key),
) -> ResponseEnvelope:
    """يستقبل تقرير كامل من GitHub Actions بعد كل run.

    يتطلب X-API-Key header للمصادقة.
    """
    logger.info(
        "Received pipeline report",
        run_uid=report.run_uid,
        status=report.status,
        videos_count=len(report.videos),
        logs_count=len(report.logs),
    )

    service = ReportService(session)
    result = await service.process_report(report)

    return ResponseEnvelope(
        success=True,
        data=result,
    )


@router.get("/health", response_model=ResponseEnvelope)
async def report_endpoint_health() -> ResponseEnvelope:
    """فحص بسيط إن الـ endpoint شغّال."""
    return ResponseEnvelope(
        success=True,
        data={"status": "ok", "endpoint": "/api/v1/report/pipeline"},
    )

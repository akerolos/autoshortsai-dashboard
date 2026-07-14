"""Pipeline service — manages pipeline runs and stages."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.pipeline_run import PipelineRun
from app.models.stage import STAGE_DEFINITIONS, Stage
from app.repositories.pipeline_repo import PipelineRunRepository
from app.repositories.stage_repo import StageRepository
from app.schemas.pipeline import PipelineOverviewSchema, PipelineRunSchema, StageSchema
from app.utils.enums import STATUS_COLORS
from app.websocket.manager import manager

logger = get_logger(__name__)


class PipelineService:
    """منطق أعمال الـ pipeline."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.run_repo = PipelineRunRepository(session)
        self.stage_repo = StageRepository(session)

    async def get_today_run(self, channel_id: str = "default") -> PipelineRun | None:
        """آخر run لليوم."""
        return await self.run_repo.get_today_run(channel_id)

    async def get_recent_runs(self, limit: int = 10, channel_id: str = "default") -> list[PipelineRun]:
        """آخر runs."""
        return await self.run_repo.get_recent_runs(limit, channel_id)

    async def get_run_with_stages(self, run_id: int) -> PipelineRun:
        """run مع كل مراحله."""
        run = await self.run_repo.get_with_stages(run_id)
        if not run:
            raise NotFoundError(f"Pipeline run {run_id} not found")
        return run

    async def get_overview(self, channel_id: str = "default") -> PipelineOverviewSchema:
        """نظرة عامة على الـ pipeline."""
        today_run = await self.run_repo.get_today_run(channel_id)
        recent_runs = await self.run_repo.get_recent_runs(5, channel_id)
        last_7_days = await self.run_repo.get_last_7_days_count(channel_id)
        success_rate = await self.run_repo.get_success_rate(channel_id)

        return PipelineOverviewSchema(
            today_run=self._serialize_run(today_run) if today_run else None,
            recent_runs=[self._serialize_run(r) for r in recent_runs],
            last_7_days_count=last_7_days,
            success_rate=success_rate,
        )

    async def create_run(
        self,
        target_videos: int = 5,
        channel_id: str = "default",
    ) -> PipelineRun:
        """ينشئ run جديداً مع كل المراحل."""
        run = await self.run_repo.create(
            run_uid=str(uuid.uuid4()),
            channel_id=channel_id,
            status="waiting",
            target_videos=target_videos,
        )

        # إنشاء المراحل
        for idx, stage_def in enumerate(STAGE_DEFINITIONS):
            await self.stage_repo.create(
                pipeline_run_id=run.id,
                stage_key=stage_def["key"],
                stage_name=stage_def["name"],
                order_index=idx,
                status="waiting",
                progress=0.0,
            )

        await self.session.commit()
        logger.info("Pipeline run created", run_id=run.id, run_uid=run.run_uid)
        return run

    async def start_run(self, run_id: int) -> PipelineRun:
        """يبدأ تنفيذ run."""
        run = await self.get_run_with_stages(run_id)
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        run.current_stage = "content_engine"
        run.current_progress = 0.0
        await self.session.commit()

        # إشعار WebSocket
        await manager.broadcast_pipeline_update({
            "run_id": run.id,
            "status": "running",
            "started_at": run.started_at.isoformat() if run.started_at else None,
        })
        return run

    async def update_stage(
        self,
        run_id: int,
        stage_key: str,
        status: str,
        progress: float = 0.0,
        current_task: str | None = None,
        message: str | None = None,
        error_message: str | None = None,
        memory_usage_mb: float | None = None,
        cpu_usage_percent: float | None = None,
    ) -> Stage:
        """يحدّث حالة مرحلة."""
        stages = await self.stage_repo.get_by_run(run_id)
        stage = next((s for s in stages if s.stage_key == stage_key), None)
        if not stage:
            raise NotFoundError(f"Stage {stage_key} not found in run {run_id}")

        now = datetime.now(timezone.utc)
        stage.status = status
        stage.progress = progress
        stage.current_task = current_task
        stage.message = message
        stage.error_message = error_message
        stage.memory_usage_mb = memory_usage_mb
        stage.cpu_usage_percent = cpu_usage_percent

        if status == "running" and stage.started_at is None:
            stage.started_at = now
        if status in ("completed", "failed", "skipped") and stage.finished_at is None:
            stage.finished_at = now
            if stage.started_at:
                stage.execution_time_seconds = (now - stage.started_at).total_seconds()

        # تحديث الـ run نفسه
        run = await self.run_repo.get_by_id(run_id)
        if run:
            run.current_stage = stage_key if status == "running" else run.current_stage
            if status == "running":
                run.current_progress = progress

        await self.session.commit()

        # إشعار WebSocket
        await manager.broadcast_stage_update({
            "run_id": run_id,
            "stage_key": stage_key,
            "stage_name": stage.stage_name,
            "status": status,
            "progress": progress,
            "current_task": current_task,
            "message": message,
            "error_message": error_message,
            "memory_usage_mb": memory_usage_mb,
            "cpu_usage_percent": cpu_usage_percent,
            "execution_time_seconds": stage.execution_time_seconds,
        })

        logger.info(
            "Stage updated",
            run_id=run_id,
            stage=stage_key,
            status=status,
            progress=progress,
        )
        return stage

    async def complete_run(self, run_id: int, success: bool = True) -> PipelineRun:
        """إنهاء run."""
        run = await self.get_run_with_stages(run_id)
        now = datetime.now(timezone.utc)
        run.status = "completed" if success else "failed"
        run.finished_at = now
        if run.started_at:
            run.execution_time_seconds = (now - run.started_at).total_seconds()

        await self.session.commit()

        await manager.broadcast_pipeline_update({
            "run_id": run_id,
            "status": run.status,
            "finished_at": run.finished_at.isoformat(),
            "execution_time_seconds": run.execution_time_seconds,
        })
        return run

    @staticmethod
    def _serialize_run(run: PipelineRun) -> PipelineRunSchema:
        """يحوّل الـ model إلى schema مع حقول إضافية."""
        stages = [
            StageSchema(
                id=s.id,
                stage_key=s.stage_key,
                stage_name=s.stage_name,
                order_index=s.order_index,
                status=s.status,
                progress=s.progress,
                started_at=s.started_at,
                finished_at=s.finished_at,
                execution_time_seconds=s.execution_time_seconds,
                memory_usage_mb=s.memory_usage_mb,
                cpu_usage_percent=s.cpu_usage_percent,
                current_task=s.current_task,
                message=s.message,
                error_message=s.error_message,
                color=STATUS_COLORS.get(s.status),
            )
            for s in (run.stages or [])
        ]
        return PipelineRunSchema(
            id=run.id,
            run_uid=run.run_uid,
            channel_id=run.channel_id,
            status=run.status,
            target_videos=run.target_videos,
            completed_videos=run.completed_videos,
            failed_videos=run.failed_videos,
            current_stage=run.current_stage,
            current_progress=run.current_progress,
            started_at=run.started_at,
            finished_at=run.finished_at,
            execution_time_seconds=run.execution_time_seconds,
            error_message=run.error_message,
            stages=stages,
            color=STATUS_COLORS.get(run.status),
        )

    def serialize_run(self, run: PipelineRun) -> PipelineRunSchema:
        """public wrapper للـ serialization."""
        return self._serialize_run(run)

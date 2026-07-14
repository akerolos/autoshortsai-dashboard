"""Report service — يستقبل ويخزّن تقارير GitHub Actions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.log import LogEntry
from app.models.pipeline_run import PipelineRun
from app.models.stage import STAGE_DEFINITIONS, Stage
from app.models.video import Video
from app.repositories.pipeline_repo import PipelineRunRepository
from app.repositories.stage_repo import StageRepository
from app.repositories.video_repo import VideoRepository
from app.schemas.report import PipelineReportSchema
from app.utils.enums import STATUS_COLORS
from app.websocket.manager import manager

logger = get_logger(__name__)


class ReportService:
    """يستقبل تقارير GitHub Actions ويخزّنها في الـ DB."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.run_repo = PipelineRunRepository(session)
        self.stage_repo = StageRepository(session)
        self.video_repo = VideoRepository(session)

    async def process_report(self, report: PipelineReportSchema) -> dict[str, Any]:
        """يعالج تقرير كامل من GitHub Actions."""
        logger.info(
            "Processing pipeline report",
            run_uid=report.run_uid,
            status=report.status,
            videos=len(report.videos),
        )

        # 1. إنشاء/تحديث الـ pipeline run
        run = await self._upsert_run(report)

        # 2. تخزين المراحل
        await self._store_stages(run.id, report.stages)

        # 3. تخزين الفيديوهات
        stored_videos = await self._store_videos(run.id, report.videos, report.channel_id, report.platform)

        # 4. تخزين الـ logs
        await self._store_logs(run.id, report.logs)

        await self.session.commit()

        # 5. إشعار WebSocket بالـ update
        await manager.broadcast_pipeline_update({
            "run_id": run.id,
            "run_uid": run.run_uid,
            "status": run.status,
            "completed_videos": run.completed_videos,
            "failed_videos": run.failed_videos,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "execution_time_seconds": run.execution_time_seconds,
        })

        logger.info(
            "Report processed successfully",
            run_id=run.id,
            videos_stored=len(stored_videos),
        )

        return {
            "run_id": run.id,
            "run_uid": run.run_uid,
            "status": run.status,
            "videos_stored": len(stored_videos),
            "logs_stored": len(report.logs),
        }

    async def _upsert_run(self, report: PipelineReportSchema) -> PipelineRun:
        """ينشئ run جديد أو يحدّث موجود (لو نفس run_uid)."""
        # البحث عن run موجود بنفس run_uid
        from sqlalchemy import select
        result = await self.session.execute(
            select(PipelineRun).where(PipelineRun.run_uid == report.run_uid)
        )
        run = result.scalar_one_or_none()

        if run:
            # تحديث موجود
            run.status = report.status
            run.target_videos = report.target_videos
            run.completed_videos = report.completed_videos
            run.failed_videos = report.failed_videos
            run.started_at = report.started_at
            run.finished_at = report.finished_at
            run.execution_time_seconds = report.execution_time_seconds
            run.error_message = report.error_message
            run.current_stage = "upload" if report.status == "completed" else run.current_stage
            run.current_progress = 100.0 if report.status == "completed" else run.current_progress
            await self.session.flush()
        else:
            # إنشاء جديد
            run = await self.run_repo.create(
                run_uid=report.run_uid,
                channel_id=report.channel_id,
                status=report.status,
                target_videos=report.target_videos,
                completed_videos=report.completed_videos,
                failed_videos=report.failed_videos,
                current_stage="upload" if report.status == "completed" else "unknown",
                current_progress=100.0 if report.status == "completed" else 0.0,
                started_at=report.started_at,
                finished_at=report.finished_at,
                execution_time_seconds=report.execution_time_seconds,
                error_message=report.error_message,
            )

        return run

    async def _store_stages(self, run_id: int, stages: list) -> None:
        """يخزّن مراحل الـ pipeline."""
        # مسح المراحل القديمة (لو الـ run موجود من قبل)
        from sqlalchemy import delete
        await self.session.execute(delete(Stage).where(Stage.pipeline_run_id == run_id))

        for stage_data in stages:
            await self.stage_repo.create(
                pipeline_run_id=run_id,
                stage_key=stage_data.stage_key,
                stage_name=stage_data.stage_name,
                order_index=self._get_stage_order(stage_data.stage_key),
                status=stage_data.status,
                progress=stage_data.progress,
                started_at=stage_data.started_at,
                finished_at=stage_data.finished_at,
                execution_time_seconds=stage_data.execution_time_seconds,
                memory_usage_mb=stage_data.memory_usage_mb,
                cpu_usage_percent=stage_data.cpu_usage_percent,
                current_task=stage_data.current_task,
                message=stage_data.message,
                error_message=stage_data.error_message,
            )

    @staticmethod
    def _get_stage_order(stage_key: str) -> int:
        """يرجع ترتيب المرحلة."""
        for idx, stage_def in enumerate(STAGE_DEFINITIONS):
            if stage_def["key"] == stage_key:
                return idx
        return 99

    async def _store_videos(
        self,
        run_id: int,
        videos: list,
        channel_id: str,
        platform: str,
    ) -> list[Video]:
        """يخزّن الفيديوهات."""
        stored = []
        for video_data in videos:
            # التحقق لو الفيديو موجود بالفعل (بنفس external_video_id)
            existing = None
            if video_data.external_video_id:
                from sqlalchemy import select
                result = await self.session.execute(
                    select(Video).where(Video.external_video_id == video_data.external_video_id)
                )
                existing = result.scalar_one_or_none()

            if existing:
                # تحديث إحصائيات الفيديو الموجود
                existing.title = video_data.title
                existing.status = video_data.status
                existing.render_time_seconds = video_data.render_time_seconds
                existing.upload_time_seconds = video_data.upload_time_seconds
                existing.generation_time_seconds = video_data.generation_time_seconds
                existing.video_url = video_data.video_url or existing.video_url
                existing.thumbnail_url = video_data.thumbnail_url or existing.thumbnail_url
                existing.description = video_data.description or existing.description
                await self.session.flush()
                stored.append(existing)
            else:
                # فيديو جديد
                video = await self.video_repo.create(
                    pipeline_run_id=run_id,
                    channel_id=channel_id,
                    platform=platform,
                    title=video_data.title,
                    description=video_data.description,
                    category=video_data.category or "general",
                    thumbnail_url=video_data.thumbnail_url,
                    video_url=video_data.video_url,
                    duration_seconds=video_data.duration_seconds,
                    status=video_data.status,
                    render_time_seconds=video_data.render_time_seconds,
                    upload_time_seconds=video_data.upload_time_seconds,
                    generation_time_seconds=video_data.generation_time_seconds,
                    upload_date=datetime.now(timezone.utc) if video_data.status == "published" else None,
                    external_video_id=video_data.external_video_id,
                )
                stored.append(video)

        return stored

    async def _store_logs(self, run_id: int, logs: list) -> None:
        """يخزّن الـ logs."""
        for log_data in logs:
            log_entry = LogEntry(
                pipeline_run_id=run_id,
                level=log_data.level.upper(),
                source=log_data.source,
                message=log_data.message,
                extra=json.dumps(log_data.extra) if log_data.extra else None,
                created_at=log_data.timestamp or datetime.now(timezone.utc),
            )
            self.session.add(log_entry)

        # إشعار WebSocket بآخر logs
        if logs:
            for log_data in logs[-5:]:  # آخر 5 logs بس
                await manager.broadcast_log({
                    "level": log_data.level.upper(),
                    "source": log_data.source,
                    "message": log_data.message,
                    "pipeline_run_id": run_id,
                    "created_at": (log_data.timestamp or datetime.now(timezone.utc)).isoformat(),
                })

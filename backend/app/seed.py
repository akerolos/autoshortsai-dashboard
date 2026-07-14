"""Database seeder — generates realistic demo data.

يُشغّل عند بدء التطبيق في وضع التطوير إذا كانت قاعدة البيانات فارغة.
"""

from __future__ import annotations

import asyncio
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import async_session_factory, init_db
from app.core.logging import get_logger, setup_logging
from app.models.log import LogEntry
from app.models.metric import DailyMetric
from app.models.pipeline_run import PipelineRun
from app.models.setting import Setting
from app.models.stage import STAGE_DEFINITIONS, Stage
from app.models.video import Video
from app.services.settings_service import SettingsService

logger = get_logger(__name__)


# عناوين فيديوهات تجريبية واقعية (تقنية)
SAMPLE_TITLES = [
    "AI Revolution: How GPT Changed Everything in 2025",
    "The Hidden Power of Python Decorators Explained",
    "Why Every Developer Should Learn Rust in 2025",
    "Building Scalable Microservices with FastAPI",
    "The Complete Guide to Docker Compose",
    "10 JavaScript Tricks You Didn't Know Existed",
    "Understanding Async/Await in Python Deeply",
    "Machine Learning Pipeline from Scratch",
    "Why TypeScript is Taking Over the Web",
    "The Art of Clean Code: Principles That Matter",
    "Kubernetes Explained: From Zero to Hero",
    "How to Ace Your Next System Design Interview",
    "The Future of WebAssembly: What's Coming",
    "GraphQL vs REST: The Ultimate Comparison",
    "Building Real-Time Apps with WebSockets",
    "React Server Components: A Complete Guide",
    "Database Indexing Strategies That Actually Work",
    "The Hidden Costs of Technical Debt",
    "Why Monorepos Are Making a Comeback",
    "Edge Computing: The Next Big Shift",
]

SAMPLE_DESCRIPTIONS = [
    "In this video, we explore the latest trends and breakthroughs in technology.",
    "A deep dive into modern development practices and tools.",
    "Everything you need to know about this exciting topic.",
    "Practical examples and real-world applications included.",
]

SAMPLE_CATEGORIES = ["technology", "programming", "ai", "web-dev", "tutorial"]


async def seed_all() -> None:
    """يزرع كل البيانات التجريبية."""
    setup_logging()
    await init_db()

    async with async_session_factory() as session:
        # التحقق إن كانت البيانات موجودة
        existing = await session.execute(select(Video).limit(1))
        if existing.scalar_one_or_none():
            logger.info("Database already seeded, skipping.")
            return

        # 1. الإعدادات الافتراضية
        settings_service = SettingsService(session)
        count = await settings_service.seed_defaults()
        logger.info(f"Seeded {count} settings")

        # 2. الـ pipeline runs + stages + videos + metrics
        await seed_pipeline_runs(session)
        await seed_videos(session)
        await seed_metrics(session)
        await seed_logs(session)

        await session.commit()

    logger.info("Database seeding completed!")


async def seed_pipeline_runs(session) -> None:
    """ينشئ pipeline runs لآخر 30 يوم."""
    today = date.today()
    statuses_cycle = ["completed", "completed", "completed", "completed", "failed", "completed"]

    for i in range(30):
        run_date = today - timedelta(days=i)
        status = statuses_cycle[i % len(statuses_cycle)]
        started_at = datetime.combine(run_date, datetime.min.time()).replace(
            hour=18, minute=0, second=0, tzinfo=timezone.utc
        )
        exec_time = random.uniform(1800, 3600)  # 30-60 دقيقة
        finished_at = started_at + timedelta(seconds=exec_time)

        run = PipelineRun(
            run_uid=f"run-{run_date.isoformat()}-{random.randint(1000, 9999)}",
            channel_id="default",
            status=status,
            target_videos=5,
            completed_videos=5 if status == "completed" else random.randint(0, 4),
            failed_videos=0 if status == "completed" else random.randint(1, 5),
            current_stage="upload" if status == "completed" else "render",
            current_progress=100.0 if status == "completed" else random.uniform(40, 80),
            started_at=started_at,
            finished_at=finished_at if status != "running" else None,
            execution_time_seconds=exec_time if status != "running" else None,
            error_message="Render timeout exceeded 1800s" if status == "failed" else None,
        )
        session.add(run)
        await session.flush()

        # المراحل
        stage_duration = exec_time / len(STAGE_DEFINITIONS)
        for idx, stage_def in enumerate(STAGE_DEFINITIONS):
            stage_status = status if idx < len(STAGE_DEFINITIONS) - 1 else status
            if status == "failed" and idx == 5:  # render stage failed
                stage_status = "failed"
            elif status == "completed":
                stage_status = "completed"
            elif status == "running" and idx == 3:
                stage_status = "running"
            else:
                stage_status = "waiting"

            stage_started = started_at + timedelta(seconds=stage_duration * idx)
            stage_finished = stage_started + timedelta(seconds=stage_duration)

            stage = Stage(
                pipeline_run_id=run.id,
                stage_key=stage_def["key"],
                stage_name=stage_def["name"],
                order_index=idx,
                status=stage_status,
                progress=100.0 if stage_status == "completed" else (random.uniform(40, 80) if stage_status == "running" else 0.0),
                started_at=stage_started if stage_status != "waiting" else None,
                finished_at=stage_finished if stage_status in ("completed", "failed") else None,
                execution_time_seconds=stage_duration if stage_status in ("completed", "failed") else None,
                memory_usage_mb=random.uniform(150, 800) if stage_status != "waiting" else None,
                cpu_usage_percent=random.uniform(15, 85) if stage_status != "waiting" else None,
                current_task=f"Processing {stage_def['name'].lower()} batch" if stage_status == "running" else None,
                error_message="FFmpeg process terminated unexpectedly" if stage_status == "failed" else None,
            )
            session.add(stage)

    await session.flush()
    logger.info("Seeded pipeline runs and stages")


async def seed_videos(session) -> None:
    """ينشئ 100 فيديو تجريبي."""
    today = date.today()

    # نجلب الـ pipeline runs الموجودة
    runs = await session.execute(select(PipelineRun).order_by(PipelineRun.created_at.desc()))
    runs = list(runs.scalars().all())

    for i in range(100):
        run = runs[i % len(runs)] if runs else None
        days_ago = i // 5  # 5 فيديوهات يومياً تقريباً
        video_date = today - timedelta(days=days_ago)
        upload_dt = datetime.combine(video_date, datetime.min.time()).replace(
            hour=random.randint(17, 23), minute=random.randint(0, 59),
            second=random.randint(0, 59), tzinfo=timezone.utc
        )

        # إحصائيات متفاوتة
        views = random.randint(100, 50000) if i > 5 else random.randint(50000, 200000)
        ctr = round(random.uniform(2.0, 15.0), 2)
        retention = round(random.uniform(35.0, 75.0), 2)
        avg_watch = round(random.uniform(15, 55), 1)

        video = Video(
            pipeline_run_id=run.id if run else None,
            channel_id="default",
            platform="youtube",
            title=f"{random.choice(SAMPLE_TITLES)}",
            description=random.choice(SAMPLE_DESCRIPTIONS),
            category=random.choice(SAMPLE_CATEGORIES),
            thumbnail_url=f"https://picsum.photos/seed/video{i}/640/360",
            video_url=f"https://youtube.com/watch?v=demo{i}",
            duration_seconds=random.choice([30, 45, 60, 90]),
            status="published",
            render_time_seconds=round(random.uniform(120, 600), 2),
            upload_time_seconds=round(random.uniform(30, 120), 2),
            generation_time_seconds=round(random.uniform(180, 900), 2),
            upload_date=upload_dt,
            views=views,
            likes=int(views * random.uniform(0.03, 0.08)),
            comments=int(views * random.uniform(0.005, 0.02)),
            ctr=ctr,
            retention=retention,
            avg_view_duration_seconds=avg_watch,
            external_video_id=f"demo-{i:04d}",
        )
        session.add(video)

    await session.flush()
    logger.info("Seeded 100 videos")


async def seed_metrics(session) -> None:
    """ينشئ مقاييس يومية لآخر 30 يوم."""
    today = date.today()
    base_views = 5000
    base_subs = 1000

    for i in range(30, 0, -1):
        d = today - timedelta(days=i)
        growth_factor = 1 + (30 - i) * 0.03  # نمو تدريجي

        metrics = [
            ("views", int(base_views * growth_factor * random.uniform(0.7, 1.3))),
            ("subscribers", int(base_subs * growth_factor * random.uniform(0.8, 1.2))),
            ("ctr", round(random.uniform(4.0, 9.0), 2)),
            ("retention", round(random.uniform(45.0, 65.0), 2)),
            ("render_time", round(random.uniform(180, 400), 2)),
            ("execution_time", round(random.uniform(1800, 3200), 2)),
            ("videos_produced", random.choice([4, 5, 5, 5, 6])),
        ]

        for key, value in metrics:
            session.add(DailyMetric(
                metric_date=d,
                channel_id="default",
                metric_key=key,
                metric_value=float(value),
            ))

    await session.flush()
    logger.info("Seeded daily metrics (30 days)")


async def seed_logs(session) -> None:
    """ينشئ logs تجريبية."""
    today = datetime.now(timezone.utc)
    levels_cycle = ["INFO", "INFO", "INFO", "SUCCESS", "WARNING", "INFO", "ERROR"]
    sources = ["content_engine", "image_engine", "narrator", "whisper", "timeline",
               "render", "quality_check", "upload", "system"]
    messages = [
        "Pipeline initialized successfully",
        "Generating script for video #{n}",
        "Content engine completed: 5 scripts generated",
        "Image generation started for batch {n}",
        "Stable Diffusion model loaded: SDXL 1.0",
        "Generated {n} images in {t}s",
        "Narrator TTS started with voice: ar-MA-Jawad",
        "Audio synthesis completed for video #{n}",
        "Whisper transcription started",
        "Transcribed {n} segments",
        "Timeline assembly in progress",
        "FFmpeg render started: 1080x1920 @ 30fps",
        "Render completed in {t}s",
        "Quality check passed: all metrics within range",
        "Uploading to YouTube...",
        "Upload completed successfully",
        "Video published: https://youtube.com/watch?v={n}",
        "GPU memory usage: 4.2GB / 8GB",
        "CPU utilization peaked at 78%",
        "Retrying failed operation (attempt {n}/3)",
        "FFmpeg process timeout after 1800s",
        "Database connection pool exhausted",
    ]

    for i in range(200):
        minutes_ago = i * 5
        log_time = today - timedelta(minutes=minutes_ago)
        level = levels_cycle[i % len(levels_cycle)]
        source = random.choice(sources)
        msg_template = random.choice(messages)
        message = msg_template.format(
            n=random.randint(1, 100),
            t=random.randint(30, 600),
        )

        session.add(LogEntry(
            pipeline_run_id=None,
            level=level,
            source=source,
            message=message,
            extra=None,
            created_at=log_time,
        ))

    await session.flush()
    logger.info("Seeded 200 log entries")


if __name__ == "__main__":
    asyncio.run(seed_all())

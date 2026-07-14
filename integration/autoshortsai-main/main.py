"""
=========================================
Project : AutoShortsAI
File    : main.py (نسخة بسيطة للـ static dashboard)
=========================================

الـ dashboard دلوقتي بيقرأ من قاعدة البيانات مباشرة (videos.db)
مش محتاج reporter منفصل — كل اللي عليك إن main.py يشتغل صح
والـ DB هتتبعت تلقائياً للـ dashboard repo عبر daily_run.yml.

التعديلات اللي في النسخة دي:
- بسيطة جداً — بتسجّل الـ stages في الـ DB بتاعتك
- مش محتاج API key ولا connection للـ dashboard
- كل اللي بيتعمل: تحديث videos.db (اللي أصلاً بيعملها)
"""

import config
from utils.logger import logger
from utils.file_manager import FileManager
from utils.cleaner import Cleaner
from database.manager import Database

from brain.content_engine import ContentEngine
from brain.store import BrainStore

from narrator.narrator_engine import NarratorEngine
from narrator.whisper_engine import WhisperEngine
from images.downloader import ImageDownloader
from video.composer import VideoComposer
from video.subtitle_engine import SubtitleEngine
from quality.quality_checker import QualityChecker
from youtube.uploader import YouTubeUploader

import time
import os
import json
import sqlite3
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

MAX_RETRIES = 3


def log_stage_to_db(stage_key, stage_name, status, started_at=None, finished_at=None,
                    execution_time=None, message=None, error_message=None):
    """يسجّل حالة المرحلة في DB بسيطة (pipeline_logs.db).

    الـ DB دي منفصلة عن videos.db ومش هتتدخل في حاجة عندك.
    """
    try:
        conn = sqlite3.connect("pipeline_logs.db")
        cursor = conn.cursor()

        # إنشاء الجدول لو مش موجود
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_uid TEXT,
                stage_key TEXT,
                stage_name TEXT,
                status TEXT,
                started_at TEXT,
                finished_at TEXT,
                execution_time_seconds REAL,
                message TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        run_uid = os.getenv("GITHUB_RUN_ID", f"local-{int(time.time())}")

        cursor.execute("""
            INSERT INTO stages (run_uid, stage_key, stage_name, status,
                              started_at, finished_at, execution_time_seconds,
                              message, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_uid, stage_key, stage_name, status,
              started_at, finished_at, execution_time,
              message, error_message))

        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not log stage to DB: {e}")


def log_pipeline_run_to_db(status, started_at, finished_at, execution_time,
                          target_videos, completed_videos, failed_videos, error_message=None):
    """يسجّل حالة الـ run الكامل."""
    try:
        conn = sqlite3.connect("pipeline_logs.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_uid TEXT UNIQUE,
                status TEXT,
                started_at TEXT,
                finished_at TEXT,
                execution_time_seconds REAL,
                target_videos INTEGER,
                completed_videos INTEGER,
                failed_videos INTEGER,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        run_uid = os.getenv("GITHUB_RUN_ID", f"local-{int(time.time())}")

        cursor.execute("""
            INSERT OR REPLACE INTO pipeline_runs
            (run_uid, status, started_at, finished_at, execution_time_seconds,
             target_videos, completed_videos, failed_videos, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_uid, status, started_at, finished_at, execution_time,
              target_videos, completed_videos, failed_videos, error_message))

        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not log pipeline run to DB: {e}")


def run_pipeline(video_index: int):
    """ينفّذ الـ pipeline الكامل لفيديو واحد."""
    logger.info(f"=========================================")
    logger.info(f"Starting Video #{video_index + 1} Pipeline")
    logger.info(f"=========================================")

    FileManager.create_project_folders()

    db = Database()
    db.create_tables()
    banned_ideas = db.get_recent_ideas(limit=10)

    # 1. Content Generation
    stage_start = time.time()
    log_stage_to_db("content_engine", "Content Engine", "running",
                    started_at=datetime.now().isoformat())
    try:
        categories = config.CATEGORIES
        topic = categories[video_index % len(categories)]
        logger.info(f"Selected Category: {topic}")

        engine = ContentEngine()
        content, embedding, idea_status = engine.generate_unique_content(topic, banned_ideas)

        if not content:
            logger.error("Engine failed to generate content. Skipping.")
            log_stage_to_db("content_engine", "Content Engine", "failed",
                          started_at=datetime.now().isoformat(),
                          finished_at=datetime.now().isoformat(),
                          execution_time=time.time() - stage_start,
                          error_message="Engine failed to generate content")
            db.close()
            return False

        log_stage_to_db("content_engine", "Content Engine", "completed",
                        started_at=datetime.now().isoformat(),
                        finished_at=datetime.now().isoformat(),
                        execution_time=time.time() - stage_start,
                        message=f"Generated: {content.title[:50]}")
    except Exception as e:
        log_stage_to_db("content_engine", "Content Engine", "failed",
                        execution_time=time.time() - stage_start,
                        error_message=str(e))
        db.close()
        return False

    # 2. Parallel: Voice + Images
    logger.info("Starting Parallel Processing (Voice + Images)...")
    voice_start = time.time()
    log_stage_to_db("image_engine", "Image Engine", "running")
    log_stage_to_db("narrator", "Narrator", "running")

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            voice_future = executor.submit(NarratorEngine().generate, content, topic)
            images_future = executor.submit(ImageDownloader().download_all, content.image_keywords)
            voice = voice_future.result()
            images = images_future.result()

        log_stage_to_db("image_engine", "Image Engine", "completed",
                        execution_time=time.time() - voice_start)
        log_stage_to_db("narrator", "Narrator", "completed",
                        execution_time=time.time() - voice_start)
    except Exception as e:
        log_stage_to_db("image_engine", "Image Engine", "failed", error_message=str(e))
        log_stage_to_db("narrator", "Narrator", "failed", error_message=str(e))
        db.close()
        return False

    # 3. Whisper Timestamps
    whisper_start = time.time()
    log_stage_to_db("whisper", "Whisper", "running")
    try:
        timestamps_path = "output/audio/voice_timestamps.json"
        WhisperEngine.generate_timestamps(voice.audio_path, timestamps_path)
        voice.timestamps_path = timestamps_path
        log_stage_to_db("whisper", "Whisper", "completed",
                        execution_time=time.time() - whisper_start)
    except Exception as e:
        log_stage_to_db("whisper", "Whisper", "failed", error_message=str(e))
        db.close()
        return False

    # 4. Subtitles
    timeline_start = time.time()
    log_stage_to_db("timeline", "Timeline", "running")
    try:
        _, ass_path = SubtitleEngine().generate(content, voice)
        log_stage_to_db("timeline", "Timeline", "completed",
                        execution_time=time.time() - timeline_start)
    except Exception as e:
        log_stage_to_db("timeline", "Timeline", "failed", error_message=str(e))
        db.close()
        return False

    # 5. Render
    render_start = time.time()
    log_stage_to_db("render", "Render", "running")
    try:
        video_model = VideoComposer().compose(content, voice, images, ass_path, topic)
        video_path = video_model.video_path
        render_time = time.time() - render_start
        log_stage_to_db("render", "Render", "completed",
                        execution_time=render_time,
                        message=f"Video rendered: {video_path}")
    except Exception as e:
        log_stage_to_db("render", "Render", "failed",
                        execution_time=time.time() - render_start,
                        error_message=str(e))
        db.close()
        return False

    # 6. Quality Check
    qc_start = time.time()
    log_stage_to_db("quality_check", "Quality Check", "running")
    logger.info("Running Quality Checks...")
    try:
        quality_result = QualityChecker().run_all_checks(
            content, voice, images, ass_path, video_path
        )

        if quality_result["status"] == "FAIL":
            logger.error(f"Video #{video_index + 1} REJECTED: {quality_result['reason']}")
            log_stage_to_db("quality_check", "Quality Check", "failed",
                            execution_time=time.time() - qc_start,
                            error_message=quality_result['reason'])
            Cleaner.cleanup_temp_files()
            Cleaner.cleanup_final_video(video_path)
            db.close()
            return False

        log_stage_to_db("quality_check", "Quality Check", "completed",
                        execution_time=time.time() - qc_start)
    except Exception as e:
        log_stage_to_db("quality_check", "Quality Check", "failed", error_message=str(e))
        db.close()
        return False

    # 7. Upload
    upload_start = time.time()
    log_stage_to_db("upload", "Upload", "running")
    try:
        youtube_video_id = YouTubeUploader().upload(video_path, content, topic)
        upload_time = time.time() - upload_start
        video_url = f"https://www.youtube.com/watch?v={youtube_video_id}" if youtube_video_id else None
        log_stage_to_db("upload", "Upload", "completed",
                        execution_time=upload_time,
                        message=f"Uploaded: {video_url}")
    except Exception as e:
        upload_time = time.time() - upload_start
        log_stage_to_db("upload", "Upload", "failed",
                        execution_time=upload_time,
                        error_message=str(e))
        logger.error(f"Upload failed: {e}")
        youtube_video_id = None

    # Save to database
    try:
        db.save_video(content.title, getattr(content, 'hook', ''),
                     getattr(content, 'script', ''), topic)
    except Exception as e:
        logger.warning(f"Failed to save to local DB: {e}")

    db.close()
    logger.info(f"Video #{video_index + 1} Pipeline Completed Successfully!")
    return True


def main():
    """Entry point."""
    logger.info("Starting AutoShortsAI Daily Run...")

    run_start = time.time()
    started_at = datetime.now().isoformat()

    success_count = 0
    failure_count = 0

    try:
        for i in range(config.VIDEOS_PER_DAY):
            success = run_pipeline(i)
            if success:
                success_count += 1
            else:
                failure_count += 1

        # تحديد الحالة النهائية
        if failure_count == 0:
            run_status = "completed"
            error_msg = None
        elif success_count == 0:
            run_status = "failed"
            error_msg = f"All {failure_count} videos failed"
        else:
            run_status = "partial"
            error_msg = f"{failure_count} of {config.VIDEOS_PER_DAY} videos failed"

        execution_time = time.time() - run_start
        log_pipeline_run_to_db(
            status=run_status,
            started_at=started_at,
            finished_at=datetime.now().isoformat(),
            execution_time=execution_time,
            target_videos=config.VIDEOS_PER_DAY,
            completed_videos=success_count,
            failed_videos=failure_count,
            error_message=error_msg,
        )

        logger.info(f"\n{'='*50}")
        logger.info(f"Pipeline completed: {success_count}/{config.VIDEOS_PER_DAY} videos")
        logger.info(f"Status: {run_status}")
        logger.info(f"Total time: {execution_time:.1f}s")
        logger.info(f"{'='*50}")

    except Exception as e:
        error_msg = f"Pipeline crashed: {str(e)}\n{traceback.format_exc()}"
        log_pipeline_run_to_db(
            status="failed",
            started_at=started_at,
            finished_at=datetime.now().isoformat(),
            execution_time=time.time() - run_start,
            target_videos=config.VIDEOS_PER_DAY,
            completed_videos=success_count,
            failed_videos=failure_count,
            error_message=error_msg,
        )
        logger.error(error_msg)
        raise


if __name__ == "__main__":
    main()

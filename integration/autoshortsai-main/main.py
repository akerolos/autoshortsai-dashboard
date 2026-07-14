"""
=========================================
Project : AutoShortsAI
File    : main.py (مُعدّل)
=========================================
تم إضافة تكامل مع Dashboard Reporter.
التعديلات مميزة بـ: [DASHBOARD INTEGRATION]
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

# [DASHBOARD INTEGRATION] استيراد الـ reporter
from dashboard import get_reporter

import time
import os
import traceback
from concurrent.futures import ThreadPoolExecutor

MAX_RETRIES = 3


def run_pipeline(video_index: int):
    """
    Executes the full pipeline for a single video.
    """
    # [DASHBOARD INTEGRATION] الحصول على الـ reporter
    reporter = get_reporter()

    logger.info(f"=========================================")
    logger.info(f"Starting Video #{video_index + 1} Pipeline")
    logger.info(f"=========================================")

    FileManager.create_project_folders()

    # Initialize Main Database
    db = Database()
    db.create_tables()
    banned_ideas = db.get_recent_ideas(limit=10)

    # 1. Brain: Content Generation
    # [DASHBOARD INTEGRATION] تسجيل بداية مرحلة content_engine
    reporter.stage_start("content_engine", "Content Engine", current_task="Generating content ideas")
    try:
        categories = config.CATEGORIES
        topic = categories[video_index % len(categories)]
        logger.info(f"Selected Category: {topic}")

        engine = ContentEngine()
        content, embedding, idea_status = engine.generate_unique_content(
            topic, banned_ideas
        )

        if not content:
            logger.error("Engine failed to generate content. Skipping.")
            reporter.stage_end("content_engine", status="failed",
                              error_message="Engine failed to generate content")
            reporter.add_log("ERROR", "content_engine", "Content generation failed")
            db.close()
            return False

        reporter.stage_end("content_engine", status="completed",
                          message=f"Generated content: {content.title[:50]}")
        reporter.add_log("SUCCESS", "content_engine",
                        f"Content generated successfully for category: {topic}")
    except Exception as e:
        reporter.stage_end("content_engine", status="failed", error_message=str(e))
        reporter.add_log("ERROR", "content_engine", f"Exception: {str(e)}")
        logger.error(f"Content engine failed: {e}")
        db.close()
        return False

    # 2. Parallel Processing: Generate Voice & Download Images simultaneously
    logger.info("Starting Parallel Processing (Voice + Images)...")
    # [DASHBOARD INTEGRATION] تسجيل بداية image_engine و narrator
    reporter.stage_start("image_engine", "Image Engine", current_task="Downloading images from Pexels")
    reporter.stage_start("narrator", "Narrator", current_task="Generating voice with TTS")

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            voice_future = executor.submit(NarratorEngine().generate, content, topic)
            images_future = executor.submit(
                ImageDownloader().download_all, content.image_keywords
            )

            voice = voice_future.result()
            images = images_future.result()

        reporter.stage_end("image_engine", status="completed",
                          message=f"Downloaded {len(images) if images else 0} images")
        reporter.stage_end("narrator", status="completed",
                          message=f"Voice generated: {voice.audio_path}")
        reporter.add_log("SUCCESS", "image_engine", "Image download completed")
        reporter.add_log("SUCCESS", "narrator", "Voice generation completed")
    except Exception as e:
        reporter.stage_end("image_engine", status="failed", error_message=str(e))
        reporter.stage_end("narrator", status="failed", error_message=str(e))
        reporter.add_log("ERROR", "parallel", f"Parallel processing failed: {str(e)}")
        logger.error(f"Parallel processing failed: {e}")
        db.close()
        return False

    logger.info("Parallel Processing completed.")

    # 3. Generate Timestamps (The Single Source of Truth via Whisper)
    # [DASHBOARD INTEGRATION] تسجيل مرحلة whisper
    reporter.stage_start("whisper", "Whisper", current_task="Generating timestamps")
    try:
        timestamps_path = "output/audio/voice_timestamps.json"
        WhisperEngine.generate_timestamps(voice.audio_path, timestamps_path)
        voice.timestamps_path = timestamps_path  # Inject the SSOT

        reporter.stage_end("whisper", status="completed",
                          message="Timestamps generated")
        reporter.add_log("SUCCESS", "whisper", "Whisper transcription completed")
    except Exception as e:
        reporter.stage_end("whisper", status="failed", error_message=str(e))
        reporter.add_log("ERROR", "whisper", f"Whisper failed: {str(e)}")
        logger.error(f"Whisper failed: {e}")
        db.close()
        return False

    # 4. Generate Subtitles (Reading from Whisper SSOT)
    # [DASHBOARD INTEGRATION] تسجيل مرحلة timeline
    reporter.stage_start("timeline", "Timeline", current_task="Assembling timeline")
    try:
        _, ass_path = SubtitleEngine().generate(content, voice)
        reporter.stage_end("timeline", status="completed",
                          message="Timeline assembled")
    except Exception as e:
        reporter.stage_end("timeline", status="failed", error_message=str(e))
        logger.error(f"Timeline failed: {e}")
        db.close()
        return False

    # 5. Compose Video (Timeline inside will read Whisper SSOT)
    # [DASHBOARD INTEGRATION] تسجيل مرحلة render مع قياس الزمن
    render_start = time.time()
    reporter.stage_start("render", "Render", current_task="Composing video with FFmpeg")
    try:
        video_model = VideoComposer().compose(content, voice, images, ass_path, topic)
        video_path = video_model.video_path
        render_time = time.time() - render_start

        reporter.stage_end("render", status="completed",
                          message=f"Video rendered: {video_path}",
                          execution_time_seconds=round(render_time, 2))
        reporter.add_log("SUCCESS", "render", f"Video rendered in {render_time:.1f}s")
    except Exception as e:
        reporter.stage_end("render", status="failed", error_message=str(e))
        reporter.add_log("ERROR", "render", f"Render failed: {str(e)}")
        logger.error(f"Render failed: {e}")
        db.close()
        return False

    # 6. Quality Gate
    # [DASHBOARD INTEGRATION] تسجيل مرحلة quality_check
    reporter.stage_start("quality_check", "Quality Check", current_task="Running quality checks")
    logger.info("Running Quality Checks...")
    try:
        quality_result = QualityChecker().run_all_checks(
            content, voice, images, ass_path, video_path
        )

        if quality_result["status"] == "FAIL":
            logger.error(f"Video #{video_index + 1} REJECTED: {quality_result['reason']}")
            reporter.stage_end("quality_check", status="failed",
                              error_message=quality_result['reason'])
            reporter.add_log("ERROR", "quality_check",
                           f"Quality check failed: {quality_result['reason']}")

            # [DASHBOARD INTEGRATION] تسجيل الفيديو كـ failed
            reporter.add_video(
                title=content.title,
                status="failed",
                category=topic,
                niche=config.NICHE,
                hook=getattr(content, 'hook', None),
                script=getattr(content, 'script', None),
                render_time_seconds=round(render_time, 2),
            )

            Cleaner.cleanup_temp_files()
            Cleaner.cleanup_final_video(video_path)
            db.close()
            return False

        reporter.stage_end("quality_check", status="completed",
                          message="All quality checks passed")
        reporter.add_log("SUCCESS", "quality_check", "Quality checks passed")
    except Exception as e:
        reporter.stage_end("quality_check", status="failed", error_message=str(e))
        logger.error(f"Quality check failed: {e}")
        db.close()
        return False

    # 7. Upload to YouTube
    # [DASHBOARD INTEGRATION] تسجيل مرحلة upload مع قياس الزمن
    upload_start = time.time()
    reporter.stage_start("upload", "Upload", current_task="Uploading to YouTube")
    try:
        # محاولة الرفع
        youtube_video_id = YouTubeUploader().upload(video_path, content, topic)
        upload_time = time.time() - upload_start

        # [DASHBOARD INTEGRATION] تسجيل الفيديو كـ published
        video_url = f"https://www.youtube.com/watch?v={youtube_video_id}" if youtube_video_id else None
        reporter.stage_end("upload", status="completed",
                          message=f"Uploaded: {video_url}",
                          execution_time_seconds=round(upload_time, 2))

        reporter.add_video(
            title=content.title,
            status="published",
            video_url=video_url,
            duration_seconds=config.VIDEO_DURATION,
            external_video_id=youtube_video_id,
            category=topic,
            niche=config.NICHE,
            hook=getattr(content, 'hook', None),
            script=getattr(content, 'script', None),
            render_time_seconds=round(render_time, 2),
            upload_time_seconds=round(upload_time, 2),
            generation_time_seconds=round(render_time + upload_time, 2),
        )
        reporter.add_log("SUCCESS", "upload", f"Video uploaded: {video_url}")

    except Exception as e:
        upload_time = time.time() - upload_start
        reporter.stage_end("upload", status="failed", error_message=str(e))
        reporter.add_log("ERROR", "upload", f"Upload failed: {str(e)}")

        # [DASHBOARD INTEGRATION] تسجيل الفيديو كـ failed
        reporter.add_video(
            title=content.title,
            status="failed",
            category=topic,
            niche=config.NICHE,
            render_time_seconds=round(render_time, 2),
            upload_time_seconds=round(upload_time, 2),
        )

        logger.error(f"Upload failed: {e}")
        # نكمل عادي حتى لو الرفع فشل، الفيديو موجود محلياً
        youtube_video_id = None
        video_url = None

    # Save to database
    try:
        db.save_video(content.title, getattr(content, 'hook', ''), getattr(content, 'script', ''), topic)
    except Exception as e:
        logger.warning(f"Failed to save video to local DB: {e}")

    db.close()
    logger.info(f"Video #{video_index + 1} Pipeline Completed Successfully!")
    return True


def main():
    """الـ entry point الرئيسي."""
    # [DASHBOARD INTEGRATION] تهيئة الـ reporter
    reporter = get_reporter()
    reporter.add_log("INFO", "system", f"Pipeline started — target: {config.VIDEOS_PER_DAY} videos")

    success_count = 0
    failure_count = 0

    try:
        for i in range(config.VIDEOS_PER_DAY):
            success = run_pipeline(i)
            if success:
                success_count += 1
            else:
                failure_count += 1

        # [DASHBOARD INTEGRATION] إنهاء الـ run
        if failure_count == 0:
            run_status = "completed"
            error_msg = None
        elif success_count == 0:
            run_status = "failed"
            error_msg = f"All {failure_count} videos failed"
        else:
            run_status = "partial"
            error_msg = f"{failure_count} of {config.VIDEOS_PER_DAY} videos failed"

        reporter.finish_run(status=run_status, error_message=error_msg)
        reporter.add_log(
            "SUCCESS" if run_status == "completed" else "WARNING",
            "system",
            f"Pipeline finished: {success_count} success, {failure_count} failed"
        )

        logger.info(f"\n{'='*50}")
        logger.info(f"Pipeline completed: {success_count}/{config.VIDEOS_PER_DAY} videos")
        logger.info(f"{'='*50}")

    except Exception as e:
        # [DASHBOARD INTEGRATION] لو حصل خطأ عام
        error_msg = f"Pipeline crashed: {str(e)}\n{traceback.format_exc()}"
        reporter.finish_run(status="failed", error_message=error_msg)
        reporter.add_log("ERROR", "system", f"Pipeline crashed: {str(e)}")
        logger.error(error_msg)
        raise

    finally:
        # [DASHBOARD INTEGRATION] إرسال التقرير للـ dashboard في كل الحالات
        logger.info("Sending report to dashboard...")
        reporter.send()


if __name__ == "__main__":
    main()

"""
=========================================
Project : AutoShortsAI
File    : dashboard/reporter.py
=========================================
Dashboard Reporter — يبعت تقارير الـ pipeline للـ Dashboard.

يُستخدم بعد كل run على GitHub Actions عشان يحدّث الـ dashboard بحالة:
- الـ run ككل (وقت البداية/النهاية، الحالة، عدد الفيديوهات)
- كل مرحلة من الـ pipeline وحالتها
- الفيديوهات اللي اتعملت
- الـ logs المهمة

الاستخدام:
    from dashboard.reporter import DashboardReporter

    reporter = DashboardReporter()
    reporter.start_run()
    reporter.stage_start("content_engine")
    # ... شغل الـ stage ...
    reporter.stage_end("content_engine", status="completed")

    reporter.add_video(title, video_url, ...)
    reporter.finish_run(status="completed")

    reporter.send()  # يبعت كل ده للـ dashboard
"""

import os
import time
import requests
from datetime import datetime, timezone
from typing import Optional
from utils.logger import logger


class DashboardReporter:
    """يبعت تقارير الـ pipeline للـ Dashboard المستضاف."""

    def __init__(self):
        # نقرأ الإعدادات من متغيرات البيئة
        self.dashboard_url = os.getenv("DASHBOARD_URL", "").rstrip("/")
        self.api_key = os.getenv("DASHBOARD_API_KEY", "")

        # معرّف فريد للـ run ده
        # نستخدم GitHub Actions run ID لو موجود، وإلا نولّد واحد
        github_run_id = os.getenv("GITHUB_RUN_ID", "")
        if github_run_id:
            self.run_uid = f"github-{github_run_id}"
        else:
            import uuid
            self.run_uid = f"local-{uuid.uuid4().hex[:12]}"

        # بيانات الـ report
        self.report = {
            "run_uid": self.run_uid,
            "channel_id": "default",
            "platform": "youtube",
            "status": "running",
            "target_videos": 5,
            "completed_videos": 0,
            "failed_videos": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "execution_time_seconds": None,
            "stages": [],
            "videos": [],
            "logs": [],
            "github_run_id": github_run_id or None,
            "github_repository": os.getenv("GITHUB_REPOSITORY"),
            "git_commit_sha": os.getenv("GITHUB_SHA"),
            "error_message": None,
        }

        # توقيت بداية الـ run
        self._run_start_time = time.time()
        # توقيت بداية كل مرحلة
        self._stage_start_times = {}

        logger.info(f"DashboardReporter initialized (run_uid={self.run_uid})")

    def is_enabled(self) -> bool:
        """يتحقق لو الـ reporter مفعّل (لو الدومين والـ API key موجودين)."""
        return bool(self.dashboard_url and self.api_key)

    def stage_start(self, stage_key: str, stage_name: str = None, current_task: str = None):
        """يسجّل بداية مرحلة من الـ pipeline."""
        stage_name = stage_name or stage_key.replace("_", " ").title()
        self._stage_start_times[stage_key] = time.time()

        stage_data = {
            "stage_key": stage_key,
            "stage_name": stage_name,
            "status": "running",
            "progress": 0.0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "execution_time_seconds": None,
            "current_task": current_task,
        }
        self.report["stages"].append(stage_data)
        logger.info(f"[Dashboard] Stage started: {stage_key}")

    def stage_end(self, stage_key: str, status: str = "completed",
                  message: str = None, error_message: str = None,
                  memory_usage_mb: float = None, cpu_usage_percent: float = None):
        """يسجّل نهاية مرحلة."""
        # نلاقي الـ stage في القائمة
        stage = None
        for s in self.report["stages"]:
            if s["stage_key"] == stage_key:
                stage = s
                break

        if not stage:
            logger.warning(f"[Dashboard] Stage not found: {stage_key}")
            return

        stage["status"] = status
        stage["progress"] = 100.0 if status == "completed" else 0.0
        stage["finished_at"] = datetime.now(timezone.utc).isoformat()

        # حساب زمن التنفيذ
        start_time = self._stage_start_times.get(stage_key)
        if start_time:
            stage["execution_time_seconds"] = round(time.time() - start_time, 2)

        stage["message"] = message
        stage["error_message"] = error_message
        stage["memory_usage_mb"] = memory_usage_mb
        stage["cpu_usage_percent"] = cpu_usage_percent

        logger.info(f"[Dashboard] Stage ended: {stage_key} ({status})")

    def add_video(
        self,
        title: str,
        status: str = "published",
        video_url: str = None,
        thumbnail_url: str = None,
        duration_seconds: int = 40,
        external_video_id: str = None,
        category: str = None,
        niche: str = None,
        hook: str = None,
        script: str = None,
        render_time_seconds: float = None,
        upload_time_seconds: float = None,
        generation_time_seconds: float = None,
    ):
        """يضيف فيديو للـ report."""
        video_data = {
            "title": title,
            "status": status,
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
            "duration_seconds": duration_seconds,
            "external_video_id": external_video_id,
            "category": category or "general",
            "niche": niche,
            "hook": hook,
            "script": script,
            "render_time_seconds": render_time_seconds,
            "upload_time_seconds": upload_time_seconds,
            "generation_time_seconds": generation_time_seconds,
        }
        self.report["videos"].append(video_data)

        # تحديث عدّادات الـ run
        if status == "published":
            self.report["completed_videos"] += 1
        elif status == "failed":
            self.report["failed_videos"] += 1

        logger.info(f"[Dashboard] Video added: {title} ({status})")

    def add_log(self, level: str, source: str, message: str, extra: dict = None):
        """يضيف سجل للـ report."""
        log_data = {
            "level": level.upper(),
            "source": source,
            "message": message,
            "extra": extra,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.report["logs"].append(log_data)

    def finish_run(self, status: str = "completed", error_message: str = None):
        """يسجّل نهاية الـ run كله."""
        self.report["status"] = status
        self.report["finished_at"] = datetime.now(timezone.utc).isoformat()
        self.report["execution_time_seconds"] = round(time.time() - self._run_start_time, 2)
        self.report["error_message"] = error_message

        logger.info(
            f"[Dashboard] Run finished: {status} "
            f"({self.report['execution_time_seconds']}s, "
            f"{self.report['completed_videos']} videos)"
        )

    def send(self) -> bool:
        """يبعت الـ report الكامل للـ dashboard.

        Returns:
            True لو اتقرأ بنجاح، False لو فشل أو الـ reporter معطّل.
        """
        if not self.is_enabled():
            logger.warning("[Dashboard] Reporter disabled (DASHBOARD_URL or DASHBOARD_API_KEY missing)")
            return False

        url = f"{self.dashboard_url}/api/v1/report/pipeline"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

        try:
            logger.info(f"[Dashboard] Sending report to {url}...")
            response = requests.post(url, json=self.report, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"[Dashboard] Report sent successfully: "
                    f"run_id={data.get('data', {}).get('run_id')}"
                )
                return True
            else:
                logger.error(
                    f"[Dashboard] Failed to send report: "
                    f"HTTP {response.status_code} - {response.text[:200]}"
                )
                return False

        except requests.exceptions.Timeout:
            logger.error("[Dashboard] Timeout while sending report")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[Dashboard] Connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"[Dashboard] Unexpected error: {e}")
            return False


# Singleton lazy
_reporter_instance = None


def get_reporter() -> DashboardReporter:
    """يرجع singleton instance من الـ reporter."""
    global _reporter_instance
    if _reporter_instance is None:
        _reporter_instance = DashboardReporter()
    return _reporter_instance


if __name__ == "__main__":
    # اختبار سريع
    reporter = DashboardReporter()
    print(f"Run UID: {reporter.run_uid}")
    print(f"Enabled: {reporter.is_enabled()}")
    print(f"Dashboard URL: {reporter.dashboard_url or '(not set)'}")

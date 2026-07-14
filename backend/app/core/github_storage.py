"""GitHub-based storage fallback for Render free tier.

يستخدم GitHub repo لتخزين نسخة من قاعدة البيانات.
كل ما الـ Dashboard يفتح، بيحمّل آخر نسخة من الـ DB.
كل ما تقرير جديد يوصل، بيـ push نسخة جديدة.
"""

from __future__ import annotations

import os
import base64
from datetime import datetime, timezone

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


class GitHubStorage:
    """يخزّن قاعدة البيانات على GitHub repo."""

    def __init__(self) -> None:
        self.token = os.environ.get("GITHUB_TOKEN", "")
        self.repo = os.environ.get("GITHUB_DB_REPO", "")  # مثلاً "akerolos/autoshortsai-dashboard-db"
        self.branch = os.environ.get("GITHUB_DB_BRANCH", "main")
        self.db_path_in_repo = os.environ.get("GITHUB_DB_PATH", "dashboard.db")
        self.enabled = bool(self.token and self.repo)

    async def download_db(self, local_path: str) -> bool:
        """يحمّل آخر نسخة من الـ DB من GitHub."""
        if not self.enabled:
            return False

        url = f"https://api.github.com/repos/{self.repo}/contents/{self.db_path_in_repo}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params={"ref": self.branch})

                if response.status_code == 404:
                    logger.info("No existing DB on GitHub, starting fresh")
                    return False

                if response.status_code != 200:
                    logger.error(f"GitHub API error: {response.status_code}")
                    return False

                data = response.json()
                content = base64.b64decode(data["content"])
                sha = data.get("sha")

                with open(local_path, "wb") as f:
                    f.write(content)

                # حفظ الـ sha للتحديث لاحقاً
                with open(f"{local_path}.sha", "w") as f:
                    f.write(sha or "")

                logger.info(f"Downloaded DB from GitHub (sha: {sha[:8] if sha else 'none'})")
                return True

        except Exception as e:
            logger.error(f"Failed to download DB: {e}")
            return False

    async def upload_db(self, local_path: str) -> bool:
        """يرفع نسخة جديدة من الـ DB لـ GitHub."""
        if not self.enabled:
            return False

        if not os.path.exists(local_path):
            return False

        # قراءة الـ sha القديم (لو موجود) عشان GitHub يحل PLACE update
        sha = ""
        sha_path = f"{local_path}.sha"
        if os.path.exists(sha_path):
            with open(sha_path) as f:
                sha = f.read().strip()

        # قراءة الملف وتحويله لـ base64
        with open(local_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        url = f"https://api.github.com/repos/{self.repo}/contents/{self.db_path_in_repo}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {
            "message": f"Update dashboard DB — {datetime.now(timezone.utc).isoformat()}",
            "content": content,
            "branch": self.branch,
        }
        if sha:
            payload["sha"] = sha

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(url, headers=headers, json=payload)

                if response.status_code in (200, 201):
                    new_sha = response.json().get("content", {}).get("sha", "")
                    with open(sha_path, "w") as f:
                        f.write(new_sha)
                    logger.info(f"Uploaded DB to GitHub (sha: {new_sha[:8]})")
                    return True
                else:
                    logger.error(f"GitHub upload failed: {response.status_code} - {response.text[:200]}")
                    return False

        except Exception as e:
            logger.error(f"Failed to upload DB: {e}")
            return False


github_storage = GitHubStorage()

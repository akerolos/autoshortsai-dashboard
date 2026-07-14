"""Application configuration management.

يتم تحميل الإعدادات من ملف .env أو من متغيرات البيئة.
يستخدم pydantic-settings للـ validation والـ type safety.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# المسار الجذري للمشروع (backend/)
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """إعدادات التطبيق المركزية.

    نستخدم env_prefix مخصص لتجنّب التعارض مع متغيرات البيئة الخارجية
    (مثل DATABASE_URL التي قد تكون موجودة مسبقاً في النظام).
    """

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AutoShortsAI Dashboard"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database — نسخدم ASA_DATABASE_URL لتجنّب التعارض
    asa_database_url: str = "sqlite+aiosqlite:///./data/autoshortsai.db"

    # CORS
    cors_origins: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]

    # Logging
    log_level: str = "INFO"
    log_json: bool = False

    # WebSocket
    ws_heartbeat_interval: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """يدعم صيغة JSON list أو comma-separated string."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return []

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def data_dir(self) -> Path:
        """مجلد تخزين قاعدة البيانات (على مستوى المشروع)."""
        path = BASE_DIR.parent / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def database_url(self) -> str:
        """Alias للتوافق مع باقي الكود."""
        return self.asa_database_url

    @property
    def resolved_database_url(self) -> str:
        """يحوّل المسار النسبي إلى مسار مطلق لـ SQLite.

        المسار النسبي في .env يكون نسبة لمجلد data/ على مستوى المشروع.
        """
        url = self.asa_database_url
        if "sqlite" in url and ":///" in url:
            prefix = url.split(":///")[0] + ":///"
            relative_path = url.split(":///")[1]
            if not relative_path.startswith("/"):
                # المسار النسبي قد يكون "./data/autoshortsai.db" أو "autoshortsai.db"
                # نأخذ اسم الملف فقط وضعه في data_dir
                clean = relative_path.lstrip("./").lstrip("/")
                # إذا كان المسار يبدأ بـ "data/" نأخذ ما بعده
                if clean.startswith("data/"):
                    clean = clean[5:]
                absolute_path = str(self.data_dir / clean)
                return f"{prefix}{absolute_path}"
        return url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton للإعدادات."""
    return Settings()


settings = get_settings()

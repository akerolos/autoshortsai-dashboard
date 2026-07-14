"""
=========================================
AutoShortsAI Dashboard — Static Data Generator
=========================================
يولّد ملفات JSON من قاعدة البيانات لاستخدامها في الـ static dashboard.

يُشتغل تلقائياً على GitHub Actions بعد كل run.
يقرأ الـ DB (اللي بيتنقل من مشروع AutoShortsAI)
ويولّد ملفات JSON في مجلد docs/data/ للـ dashboard.

الاستخدام:
    python generate_static_data.py
"""

import json
import os
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

# ===== الإعدادات =====
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "autoshortsai.db"
OUTPUT_DIR = BASE_DIR / "docs" / "data"

# ضمان وجود مجلد الإخراج
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def log(msg):
    """طباعة بسيطة مع timestamp."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def get_connection():
    """يتصل بقاعدة البيانات."""
    if not DB_PATH.exists():
        log(f"⚠️  DB not found at {DB_PATH}")
        log("Creating empty DB with default settings...")
        create_empty_db()
    return sqlite3.connect(str(DB_PATH))


def create_empty_db():
    """ينشئ قاعدة بيانات فاضية بالـ schema الصحيح."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # جدول الإعدادات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            value_type TEXT DEFAULT 'string',
            category TEXT DEFAULT 'general',
            description TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # جدول الفيديوهات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_run_id INTEGER,
            channel_id TEXT DEFAULT 'default',
            platform TEXT DEFAULT 'youtube',
            title TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'general',
            thumbnail_url TEXT,
            video_url TEXT,
            duration_seconds INTEGER DEFAULT 60,
            status TEXT DEFAULT 'pending',
            render_time_seconds REAL,
            upload_time_seconds REAL,
            generation_time_seconds REAL,
            upload_date TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            ctr REAL DEFAULT 0,
            retention REAL DEFAULT 0,
            avg_view_duration_seconds REAL DEFAULT 0,
            external_video_id TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # جدول الـ pipeline runs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_uid TEXT UNIQUE NOT NULL,
            channel_id TEXT DEFAULT 'default',
            status TEXT DEFAULT 'waiting',
            target_videos INTEGER DEFAULT 5,
            completed_videos INTEGER DEFAULT 0,
            failed_videos INTEGER DEFAULT 0,
            current_stage TEXT,
            current_progress REAL DEFAULT 0,
            started_at TEXT,
            finished_at TEXT,
            execution_time_seconds REAL,
            error_message TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # جدول المراحل
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_run_id INTEGER NOT NULL,
            stage_key TEXT NOT NULL,
            stage_name TEXT NOT NULL,
            order_index INTEGER DEFAULT 0,
            status TEXT DEFAULT 'waiting',
            progress REAL DEFAULT 0,
            started_at TEXT,
            finished_at TEXT,
            execution_time_seconds REAL,
            memory_usage_mb REAL,
            cpu_usage_percent REAL,
            current_task TEXT,
            message TEXT,
            error_message TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs(id) ON DELETE CASCADE
        )
    """)

    # جدول الـ logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_run_id INTEGER,
            level TEXT DEFAULT 'INFO',
            source TEXT DEFAULT 'system',
            message TEXT NOT NULL,
            extra TEXT,
            trace_id TEXT,
            created_at TEXT
        )
    """)

    # جدول المقاييس اليومية
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_date TEXT NOT NULL,
            channel_id TEXT DEFAULT 'default',
            metric_key TEXT NOT NULL,
            metric_value REAL DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(metric_date, channel_id, metric_key)
        )
    """)

    # إدراج الإعدادات الافتراضية
    default_settings = [
        ("videos_per_day", "5", "int", "production", "Number of videos to generate per day"),
        ("narrator_voice", "ar-MA-Jawad", "string", "narrator", "Voice model used for narration"),
        ("speech_rate", "1.0", "float", "narrator", "Speech playback rate multiplier"),
        ("category", "technology", "string", "production", "Content category for video generation"),
        ("prompt_version", "v2.1", "string", "production", "Version of the prompt template in use"),
        ("upload_time", "18:00", "string", "upload", "Scheduled upload time (HH:MM, 24h format)"),
        ("output_resolution", "1080x1920", "string", "render", "Output video resolution (width x height)"),
        ("video_duration_seconds", "60", "int", "render", "Target video duration in seconds"),
        ("subtitle_style", "modern-bold", "string", "render", "Subtitle visual style preset"),
        ("theme", "dark", "string", "ui", "Dashboard theme (dark | light)"),
        ("language", "ar", "string", "ui", "Dashboard interface language"),
        ("active_channel_id", "default", "string", "channels", "Currently active channel identifier"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO settings (key, value, value_type, category, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(k, v, t, c, d, datetime.now().isoformat(), datetime.now().isoformat()) for k, v, t, c, d in default_settings]
    )

    conn.commit()
    conn.close()
    log(f"✅ Created empty DB at {DB_PATH}")


def save_json(filename, data):
    """يحفظ بيانات كـ JSON في مجلد الإخراج (وبيأنشئ subfolders لو لازم)."""
    path = OUTPUT_DIR / filename
    # إنشاء subfolders لو مش موجودة (مثلاً: dashboard/, pipeline/, analytics/)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    log(f"  📄 Saved {filename} ({len(str(data))} bytes)")


def row_to_dict(row, cursor):
    """يحوّل صف لـ dict باستخدام أسماء الأعمدة."""
    return {desc[0]: row[i] for i, desc in enumerate(cursor.description)}


# ===== Generators =====


def generate_overview(conn):
    """يولّد ملف dashboard/overview.json — كل ما يحتاجه الـ Dashboard Home."""
    log("Generating dashboard/overview.json...")
    cursor = conn.cursor()

    # آخر run لليوم
    today_start = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT * FROM pipeline_runs
        WHERE created_at >= ?
        ORDER BY created_at DESC LIMIT 1
    """, (today_start,))
    today_run_row = cursor.fetchone()

    today_run = None
    if today_run_row:
        today_run = row_to_dict(today_run_row, cursor)
        # نضيف المراحل
        cursor.execute("""
            SELECT * FROM stages WHERE pipeline_run_id = ? ORDER BY order_index
        """, (today_run["id"],))
        today_run["stages"] = [row_to_dict(r, cursor) for r in cursor.fetchall()]

    # فيديوهات اليوم
    cursor.execute("""
        SELECT * FROM videos
        WHERE created_at >= ?
        ORDER BY created_at DESC LIMIT 10
    """, (today_start,))
    today_videos = [row_to_dict(r, cursor) for r in cursor.fetchall()]

    # إحصائيات
    cursor.execute("""
        SELECT
            COUNT(*) as total_videos,
            COALESCE(SUM(views), 0) as total_views,
            COALESCE(AVG(ctr), 0) as avg_ctr,
            COALESCE(AVG(retention), 0) as avg_retention,
            COALESCE(AVG(render_time_seconds), 0) as avg_render_time
        FROM videos
    """)
    stats_row = cursor.fetchone()

    # عدد فيديوهات اليوم
    cursor.execute("""
        SELECT COUNT(*) FROM videos WHERE created_at >= ?
    """, (today_start,))
    today_count = cursor.fetchone()[0]

    # نسبة نجاح الرفع
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published
        FROM videos
    """)
    success_row = cursor.fetchone()
    success_rate = (success_row[1] or 0) * 100.0 / success_row[0] if success_row[0] else 0

    # آخر 7 أيام
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT COUNT(*) FROM pipeline_runs WHERE created_at >= ?
    """, (week_ago,))
    last_7_days_count = cursor.fetchone()[0]

    # مراحل الـ pipeline (للعرض الافتراضي)
    pipeline_stages = [
        {"key": "content_engine", "name": "Content Engine", "icon": "file-text", "status": "waiting", "color": "#F59E0B"},
        {"key": "image_engine", "name": "Image Engine", "icon": "image", "status": "waiting", "color": "#F59E0B"},
        {"key": "narrator", "name": "Narrator", "icon": "mic", "status": "waiting", "color": "#F59E0B"},
        {"key": "whisper", "name": "Whisper", "icon": "waveform", "status": "waiting", "color": "#F59E0B"},
        {"key": "timeline", "name": "Timeline", "icon": "layers", "status": "waiting", "color": "#F59E0B"},
        {"key": "render", "name": "Render", "icon": "film", "status": "waiting", "color": "#F59E0B"},
        {"key": "quality_check", "name": "Quality Check", "icon": "check-circle", "status": "waiting", "color": "#F59E0B"},
        {"key": "upload", "name": "Upload", "icon": "upload", "status": "waiting", "color": "#F59E0B"},
    ]

    # لو فيه run اليوم، نحدّث المراحل
    if today_run and today_run.get("stages"):
        status_colors = {
            "running": "#3B82F6",
            "completed": "#10B981",
            "failed": "#EF4444",
            "waiting": "#F59E0B",
            "skipped": "#71717A",
        }
        stage_map = {s["stage_key"]: s for s in today_run["stages"]}
        for stage in pipeline_stages:
            real = stage_map.get(stage["key"])
            if real:
                stage["status"] = real["status"]
                stage["color"] = status_colors.get(real["status"], "#71717A")
                stage["progress"] = real.get("progress", 0)

    # الإحصائيات النهائية
    status_colors = {
        "running": "#3B82F6",
        "completed": "#10B981",
        "failed": "#EF4444",
        "waiting": "#F59E0B",
        "published": "#10B981",
        "failed_video": "#EF4444",
    }

    today_run_data = None
    if today_run:
        today_run_data = {
            "run_uid": today_run.get("run_uid"),
            "status": today_run.get("status", "waiting"),
            "started_at": today_run.get("started_at"),
            "finished_at": today_run.get("finished_at"),
            "execution_time_seconds": today_run.get("execution_time_seconds"),
            "current_stage": today_run.get("current_stage"),
            "current_progress": today_run.get("current_progress", 0),
            "target_videos": today_run.get("target_videos", 5),
            "completed_videos": today_run.get("completed_videos", 0),
            "failed_videos": today_run.get("failed_videos", 0),
            "color": status_colors.get(today_run.get("status"), "#71717A"),
        }

    stats = [
        {"label": "Total Videos", "value": stats_row[0], "icon": "film", "color": "#8B5CF6", "raw_value": stats_row[0]},
        {"label": "Today's Videos", "value": today_count, "icon": "calendar", "color": "#3B82F6", "raw_value": today_count},
        {"label": "Total Views", "value": stats_row[1], "icon": "eye", "color": "#10B981", "raw_value": stats_row[1]},
        {"label": "Avg CTR", "value": f"{stats_row[2]:.1f}%", "icon": "mouse-pointer", "color": "#F59E0B", "raw_value": stats_row[2], "unit": "%"},
        {"label": "Avg Retention", "value": f"{stats_row[3]:.1f}%", "icon": "clock", "color": "#06B6D4", "raw_value": stats_row[3], "unit": "%"},
        {"label": "Upload Success", "value": f"{success_rate:.1f}%", "icon": "check-circle", "color": "#10B981", "raw_value": success_rate, "unit": "%"},
    ]

    # آخر runs
    cursor.execute("""
        SELECT * FROM pipeline_runs ORDER BY created_at DESC LIMIT 10
    """)
    recent_runs = [row_to_dict(r, cursor) for r in cursor.fetchall()]
    for run in recent_runs:
        run["color"] = status_colors.get(run.get("status"), "#71717A")

    # charts بسيطة (آخر 14 يوم)
    charts = []
    for metric_key in ["views", "ctr"]:
        start_date = date.today() - timedelta(days=14)
        cursor.execute("""
            SELECT metric_date, metric_value FROM daily_metrics
            WHERE metric_key = ? AND metric_date >= ?
            ORDER BY metric_date ASC
        """, (metric_key, start_date.isoformat()))
        rows = cursor.fetchall()

        # ملء الأيام الفاضية
        date_value_map = {r[0]: r[1] for r in rows}
        points = []
        for i in range(14):
            d = start_date + timedelta(days=i)
            d_str = d.isoformat()
            points.append({"date": d_str, "value": float(date_value_map.get(d_str, 0))})

        charts.append({
            "id": f"dashboard_{metric_key}",
            "title": f"{metric_key.title()} (Last 14 Days)",
            "type": "line" if metric_key == "views" else "bar",
            "series": [{"name": metric_key.title(), "color": "#3B82F6" if metric_key == "views" else "#10B981", "points": points}],
            "x_labels": [p["date"] for p in points],
        })

    # فيديوهات اليوم مع color
    for v in today_videos:
        v["color"] = status_colors.get(v.get("status"), "#71717A")

    overview = {
        "today_run": today_run_data,
        "pipeline_overview": {
            "today_run": today_run_data,
            "recent_runs": recent_runs,
            "last_7_days_count": last_7_days_count,
            "success_rate": 0,  # سيتم حسابه لو احتجنا
        },
        "today_videos": today_videos,
        "stats": stats,
        "charts": charts,
        "pipeline_stages": pipeline_stages,
        "generated_at": datetime.now().isoformat(),
    }

    save_json("dashboard/overview.json", overview)


def generate_pipeline_overview(conn):
    """يولّد ملف pipeline/overview.json."""
    log("Generating pipeline/overview.json...")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM pipeline_runs ORDER BY created_at DESC LIMIT 10
    """)
    recent_runs = [row_to_dict(r, cursor) for r in cursor.fetchall()]

    # آخر run مع stages
    if recent_runs:
        latest_run = recent_runs[0]
        cursor.execute("""
            SELECT * FROM stages WHERE pipeline_run_id = ? ORDER BY order_index
        """, (latest_run["id"],))
        latest_run["stages"] = [row_to_dict(r, cursor) for r in cursor.fetchall()]

    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM pipeline_runs WHERE created_at >= ?", (week_ago,))
    last_7_days = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM pipeline_runs
    """)
    row = cursor.fetchone()
    success_rate = (row[1] or 0) * 100.0 / row[0] if row[0] else 0

    status_colors = {
        "running": "#3B82F6", "completed": "#10B981", "failed": "#EF4444",
        "waiting": "#F59E0B", "skipped": "#71717A",
    }
    for run in recent_runs:
        run["color"] = status_colors.get(run.get("status"), "#71717A")

    overview = {
        "today_run": recent_runs[0] if recent_runs else None,
        "recent_runs": recent_runs,
        "last_7_days_count": last_7_days,
        "success_rate": success_rate,
        "generated_at": datetime.now().isoformat(),
    }

    save_json("pipeline/overview.json", overview)


def generate_pipeline_today(conn):
    """يولّد ملف pipeline/today.json."""
    log("Generating pipeline/today.json...")
    cursor = conn.cursor()

    today_start = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT * FROM pipeline_runs
        WHERE created_at >= ?
        ORDER BY created_at DESC LIMIT 1
    """, (today_start,))
    row = cursor.fetchone()

    if row:
        run = row_to_dict(row, cursor)
        cursor.execute("""
            SELECT * FROM stages WHERE pipeline_run_id = ? ORDER BY order_index
        """, (run["id"],))
        run["stages"] = [row_to_dict(r, cursor) for r in cursor.fetchall()]
    else:
        run = None

    save_json("pipeline/today.json", run)


def generate_videos(conn, page=1, page_size=20):
    """يولّد ملف videos.json (أول 100 فيديو)."""
    log("Generating videos.json...")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM videos")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT * FROM videos ORDER BY created_at DESC LIMIT ?
    """, (page_size * 5,))  # أول 100 فيديو

    videos = [row_to_dict(r, cursor) for r in cursor.fetchall()]

    status_colors = {
        "published": "#10B981", "failed": "#EF4444", "pending": "#F59E0B",
        "rendering": "#3B82F6", "uploading": "#3B82F6",
    }
    for v in videos:
        v["color"] = status_colors.get(v.get("status"), "#71717A")

    data = {
        "items": videos,
        "pagination": {
            "page": 1,
            "page_size": len(videos),
            "total": total,
            "total_pages": 1,
            "has_next": False,
            "has_prev": False,
        },
        "generated_at": datetime.now().isoformat(),
    }

    save_json("videos.json", data)


def generate_analytics(conn):
    """يولّد ملف analytics/overview.json."""
    log("Generating analytics/overview.json...")
    cursor = conn.cursor()

    # إحصائيات شاملة
    cursor.execute("""
        SELECT
            COUNT(*) as total_videos,
            COALESCE(SUM(views), 0) as total_views,
            COALESCE(SUM(likes), 0) as total_likes,
            COALESCE(AVG(ctr), 0) as avg_ctr,
            COALESCE(AVG(retention), 0) as avg_retention,
            COALESCE(AVG(avg_view_duration_seconds), 0) as avg_watch_time,
            COALESCE(AVG(render_time_seconds), 0) as avg_render_time,
            COALESCE(AVG(generation_time_seconds), 0) as avg_generation_time
        FROM videos
    """)
    row = cursor.fetchone()
    totals = {
        "total_videos": row[0],
        "total_views": row[1],
        "total_likes": row[2],
        "avg_ctr": row[3],
        "avg_retention": row[4],
        "avg_watch_time": row[5],
        "avg_render_time": row[6],
        "avg_generation_time": row[7],
    }

    # نسبة النجاح
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published
        FROM videos
    """)
    srow = cursor.fetchone()
    success_rate = (srow[1] or 0) * 100.0 / srow[0] if srow[0] else 0

    today_start = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM videos WHERE created_at >= ?", (today_start,))
    today_count = cursor.fetchone()[0]

    # Stats cards
    stats = [
        {"label": "Total Videos Generated", "value": totals["total_videos"], "icon": "film", "color": "#8B5CF6", "raw_value": totals["total_videos"]},
        {"label": "Today's Videos", "value": today_count, "icon": "calendar", "color": "#3B82F6", "raw_value": today_count},
        {"label": "Total Views", "value": totals["total_views"], "icon": "eye", "color": "#10B981", "raw_value": totals["total_views"]},
        {"label": "Total Likes", "value": totals["total_likes"], "icon": "heart", "color": "#EC4899", "raw_value": totals["total_likes"]},
        {"label": "Average CTR", "value": f"{totals['avg_ctr']:.1f}%", "icon": "mouse-pointer", "color": "#F59E0B", "raw_value": totals["avg_ctr"], "unit": "%"},
        {"label": "Average Retention", "value": f"{totals['avg_retention']:.1f}%", "icon": "clock", "color": "#06B6D4", "raw_value": totals["avg_retention"], "unit": "%"},
        {"label": "Average Watch Time", "value": f"{totals['avg_watch_time']:.0f}s", "icon": "play", "color": "#A855F7", "raw_value": totals["avg_watch_time"], "unit": "s"},
        {"label": "Upload Success Rate", "value": f"{success_rate:.1f}%", "icon": "check-circle", "color": "#10B981", "raw_value": success_rate, "unit": "%"},
        {"label": "Average Render Time", "value": f"{totals['avg_render_time']:.0f}s", "icon": "cpu", "color": "#EF4444", "raw_value": totals["avg_render_time"], "unit": "s"},
        {"label": "Average Generation Time", "value": f"{totals['avg_generation_time']:.0f}s", "icon": "zap", "color": "#7C3AED", "raw_value": totals["avg_generation_time"], "unit": "s"},
    ]

    # Charts (آخر 30 يوم)
    chart_configs = [
        ("views", "Views (Last 30 Days)", "line", "#3B82F6", ""),
        ("subscribers", "Subscribers Growth", "line", "#8B5CF6", ""),
        ("ctr", "CTR (Last 30 Days)", "bar", "#10B981", "%"),
        ("retention", "Retention Rate", "line", "#F59E0B", "%"),
        ("render_time", "Render Time (Avg)", "bar", "#EC4899", "s"),
        ("execution_time", "Pipeline Execution Time", "line", "#06B6D4", "s"),
        ("videos_produced", "Video Production Volume", "bar", "#A855F7", ""),
    ]

    charts = []
    start_date = date.today() - timedelta(days=30)
    for key, title, type_, color, unit in chart_configs:
        cursor.execute("""
            SELECT metric_date, metric_value FROM daily_metrics
            WHERE metric_key = ? AND metric_date >= ?
            ORDER BY metric_date ASC
        """, (key, start_date.isoformat()))
        rows = cursor.fetchall()

        date_value_map = {r[0]: r[1] for r in rows}
        points = []
        for i in range(30):
            d = start_date + timedelta(days=i)
            d_str = d.isoformat()
            points.append({"date": d_str, "value": float(date_value_map.get(d_str, 0))})

        charts.append({
            "id": f"{key}_chart",
            "title": title,
            "type": type_,
            "series": [{"name": key.title(), "color": color, "points": points}],
            "x_labels": [p["date"] for p in points],
            "unit": unit,
        })

    # Top & Worst videos
    cursor.execute("""
        SELECT * FROM videos ORDER BY views DESC LIMIT 5
    """)
    top_videos = [row_to_dict(r, cursor) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT * FROM videos WHERE status = 'published' ORDER BY views ASC LIMIT 5
    """)
    worst_videos = [row_to_dict(r, cursor) for r in cursor.fetchall()]

    # Best hooks (أعلى CTR)
    cursor.execute("""
        SELECT * FROM videos ORDER BY ctr DESC LIMIT 5
    """)
    best_hooks = [row_to_dict(r, cursor) for r in cursor.fetchall()]
    avg_hook = sum(h.get("ctr", 0) for h in best_hooks) / len(best_hooks) if best_hooks else 0

    # Upload frequency
    cursor.execute("""
        SELECT DATE(upload_date) as d, COUNT(*) as c
        FROM videos
        WHERE upload_date IS NOT NULL AND upload_date >= ?
        GROUP BY DATE(upload_date)
        ORDER BY d ASC
    """, (start_date.isoformat(),))
    freq_rows = cursor.fetchall()
    freq_map = {r[0]: r[1] for r in freq_rows}

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    today = date.today()
    weekday = today.weekday()
    values = []
    for i in range(7):
        d = today - timedelta(days=(6 - i + weekday) % 7)
        d_str = d.isoformat()
        values.append(freq_map.get(d_str, 0))

    upload_frequency = {"labels": days, "values": values}

    overview = {
        "stats": stats,
        "charts": charts,
        "top_videos": top_videos,
        "worst_videos": worst_videos,
        "best_hooks": best_hooks,
        "avg_hook_performance": avg_hook,
        "upload_frequency": upload_frequency,
        "generated_at": datetime.now().isoformat(),
    }

    save_json("analytics/overview.json", overview)


def generate_logs(conn, limit=200):
    """يولّد ملف logs.json (آخر 200 log)."""
    log("Generating logs.json...")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM logs ORDER BY created_at DESC LIMIT ?
    """, (limit,))
    logs = [row_to_dict(r, cursor) for r in cursor.fetchall()]

    # المصادر المتاحة
    cursor.execute("SELECT DISTINCT source FROM logs ORDER BY source ASC")
    sources = [r[0] for r in cursor.fetchall()]

    data = {
        "items": logs,
        "sources": sources,
        "pagination": {
            "page": 1,
            "page_size": len(logs),
            "total": len(logs),
            "total_pages": 1,
            "has_next": False,
            "has_prev": False,
        },
        "generated_at": datetime.now().isoformat(),
    }

    save_json("logs.json", data)


def generate_settings(conn):
    """يولّد ملف settings.json."""
    log("Generating settings.json...")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM settings ORDER BY category, key")
    all_settings = [row_to_dict(r, cursor) for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT category FROM settings ORDER BY category")
    categories = [r[0] for r in cursor.fetchall()]

    groups = []
    for cat in categories:
        cat_settings = [s for s in all_settings if s["category"] == cat]
        groups.append({"category": cat, "settings": cat_settings})

    data = {
        "groups": groups,
        "all": all_settings,
        "generated_at": datetime.now().isoformat(),
    }

    save_json("settings.json", data)


def generate_health():
    """يولّد ملف health.json — حالة الـ dashboard."""
    log("Generating health.json...")
    data = {
        "status": "ok",
        "app_name": "AutoShortsAI Dashboard",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "mode": "static",
        "host": "GitHub Pages",
    }
    save_json("health.json", data)


def copy_frontend_assets():
    """ينسخ ملفات الـ frontend لـ docs/ عشان تتصاحب على GitHub Pages."""
    import shutil
    frontend_dir = BASE_DIR / "frontend"
    docs_dir = BASE_DIR / "docs"

    if not frontend_dir.exists():
        log(f"⚠️ Frontend folder not found: {frontend_dir}")
        return

    log("📁 Copying frontend assets to docs/...")

    # ضمان وجود مجلد docs
    docs_dir.mkdir(parents=True, exist_ok=True)

    # نسخ مجلد assets (بدون مسح docs كاملة)
    src_assets = frontend_dir / "assets"
    dst_assets = docs_dir / "assets"
    if dst_assets.exists():
        shutil.rmtree(dst_assets)
    shutil.copytree(src_assets, dst_assets)

    # نسخ favicon
    favicon = frontend_dir / "assets" / "icons" / "favicon.svg"
    if favicon.exists():
        shutil.copy(favicon, docs_dir / "favicon.svg")

    # نسخ index.html (لو مش موجود في docs)
    src_index = frontend_dir / "index.html"
    dst_index = docs_dir / "index.html"
    if src_index.exists():
        shutil.copy(src_index, dst_index)

    log("✅ Frontend assets copied")


def main():
    """نقطة الدخول الرئيسية."""
    log("=" * 60)
    log("🚀 AutoShortsAI Static Dashboard Generator")
    log("=" * 60)
    log(f"DB path: {DB_PATH}")
    log(f"Output dir: {OUTPUT_DIR}")
    log("")

    conn = get_connection()

    try:
        # توليد كل الملفات
        generate_overview(conn)
        generate_pipeline_overview(conn)
        generate_pipeline_today(conn)
        generate_videos(conn)
        generate_analytics(conn)
        generate_logs(conn)
        generate_settings(conn)
        generate_health()

        # نسخ الـ frontend assets
        copy_frontend_assets()

        log("")
        log("✅ All JSON files generated successfully!")
        log(f"📁 Output: {OUTPUT_DIR}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

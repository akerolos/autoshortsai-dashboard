"""WebSocket connection manager with topic-based pub/sub."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

from app.core.logging import get_logger
from app.websocket.events import EventType, WSTopic

logger = get_logger(__name__)


class ConnectionManager:
    """يدير اتصالات WebSocket ويدعم topic-based subscriptions."""

    def __init__(self) -> None:
        # كل اتصال يشترك في مواضيع معيّنة
        self._connections: dict[WebSocket, set[str]] = {}
        # عكسياً: لكل موضوع قائمة اتصالات
        self._topics: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        topics: set[str] | None = None,
    ) -> None:
        """يقبل اتصالاً جديداً ويشتركه في المواضيع."""
        await websocket.accept()

        async with self._lock:
            self._connections[websocket] = topics or {WSTopic.ALL}
            for topic in self._connections[websocket]:
                self._topics[topic].add(websocket)

        # رسالة ترحيب
        await self._send_to(websocket, {
            "type": EventType.CONNECTED,
            "data": {
                "message": "Connected to AutoShortsAI WebSocket",
                "topics": list(self._connections[websocket]),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })

        logger.info(
            "WebSocket connected",
            topics=list(self._connections[websocket]),
            total_connections=len(self._connections),
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """يقطع اتصالاً ويزيله من كل المواضيع."""
        async with self._lock:
            topics = self._connections.pop(websocket, set())
            for topic in topics:
                self._topics[topic].discard(websocket)

        logger.info(
            "WebSocket disconnected",
            total_connections=len(self._connections),
        )

    async def broadcast(self, topic: str, event_type: str, data: Any) -> None:
        """يبث حدثاً لكل المشتركين في موضوع معيّن + المشتركين في ALL."""
        recipients: set[WebSocket] = set()
        async with self._lock:
            recipients.update(self._topics.get(topic, set()))
            recipients.update(self._topics.get(WSTopic.ALL, set()))

        if not recipients:
            return

        message = {
            "type": event_type,
            "topic": topic,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # إرسال متزامن لكل المستقبلين
        failed: list[WebSocket] = []
        for ws in recipients:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.debug("Failed to send WS message", error=str(e))
                failed.append(ws)

        # تنظيف الاتصالات الميتة
        if failed:
            async with self._lock:
                for ws in failed:
                    topics = self._connections.pop(ws, set())
                    for topic in topics:
                        self._topics[topic].discard(ws)

    async def _send_to(self, websocket: WebSocket, message: dict) -> None:
        """يرسل رسالة لاتصال واحد."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.debug("Failed to send direct WS message", error=str(e))

    async def broadcast_stage_update(self, data: dict) -> None:
        """يبث تحديث مرحلة pipeline."""
        await self.broadcast(WSTopic.PIPELINE, EventType.STAGE_UPDATE, data)

    async def broadcast_pipeline_update(self, data: dict) -> None:
        """يبث تحديث pipeline run."""
        await self.broadcast(WSTopic.PIPELINE, EventType.PIPELINE_RUN_UPDATE, data)

    async def broadcast_log(self, data: dict) -> None:
        """يبث سجل جديد."""
        await self.broadcast(WSTopic.LOGS, EventType.LOG_NEW, data)

    async def broadcast_stats(self, data: dict) -> None:
        """يبث تحديث إحصائيات."""
        await self.broadcast(WSTopic.STATS, EventType.STATS_UPDATE, data)

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    async def shutdown(self) -> None:
        """يغلق كل الاتصالات عند إيقاف التطبيق."""
        async with self._lock:
            connections = list(self._connections.keys())
            self._connections.clear()
            self._topics.clear()

        for ws in connections:
            try:
                await ws.close(code=1001, reason="Server shutting down")
            except Exception:
                pass

        logger.info("All WebSocket connections closed", count=len(connections))


# Singleton
manager = ConnectionManager()

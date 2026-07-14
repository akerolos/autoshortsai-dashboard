"""WebSocket message handlers."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import WebSocket

from app.core.logging import get_logger
from app.websocket.events import EventType
from app.websocket.manager import manager

logger = get_logger(__name__)


async def handle_message(websocket: WebSocket, raw: str) -> None:
    """يعالج رسالة واردة من العميل."""
    try:
        import json
        message = json.loads(raw)
    except Exception:
        await websocket.send_json({
            "type": EventType.ERROR,
            "data": {"message": "Invalid JSON"},
        })
        return

    msg_type = message.get("type", "")

    if msg_type == EventType.PING:
        await websocket.send_json({
            "type": EventType.PONG,
            "data": {"timestamp": datetime.now(timezone.utc).isoformat()},
        })
    elif msg_type == "subscribe":
        # الاشتراك في مواضيع إضافية
        topics = message.get("topics", [])
        if topics:
            async with manager._lock:
                current = manager._connections.get(websocket, set())
                for topic in topics:
                    current.add(topic)
                    manager._topics[topic].add(websocket)
        logger.debug("Client subscribed", topics=topics)
    else:
        await websocket.send_json({
            "type": EventType.ERROR,
            "data": {"message": f"Unknown message type: {msg_type}"},
        })

"""WebSocket API routes."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from setproctitle import setproctitle  # noqa: F401  (optional)

from app.core.logging import get_logger
from app.websocket.handlers import handle_message
from app.websocket.manager import manager

logger = get_logger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
@router.websocket("/ws/{topic}")
async def websocket_endpoint(
    websocket: WebSocket,
    topic: str = "all",
) -> None:
    """نقطة نهاية WebSocket الرئيسية.

    يدعم تمرير topic في URL: /ws/pipeline أو /ws/logs أو /ws/all
    """
    topics = {topic} if topic else {"all"}
    await manager.connect(websocket, topics)

    try:
        while True:
            raw = await websocket.receive_text()
            await handle_message(websocket, raw)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.exception("WebSocket error", error=str(e))
        await manager.disconnect(websocket)

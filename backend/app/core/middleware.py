"""Application middleware and exception handlers.

يحتوي على:
- RequestID middleware (للـ tracing)
- Global exception handlers
- CORS configuration
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """يضيف request_id فريد لكل طلب ويضعه في الـ response headers."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # إضافة الـ context للـ logger
        from structlog.contextvars import bind_contextvars, clear_contextvars
        bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        clear_contextvars()
        return response


def setup_middleware(app: FastAPI) -> None:
    """يسجّل كل الـ middleware على التطبيق."""

    # Request ID (يجب أن يكون أولاً)
    app.add_middleware(RequestIDMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """يسجّل معالجات الأخطاء العامة."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            "Application error",
            error_code=exc.error_code,
            message=exc.message,
            path=request.url.path,
            request_id=request_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                },
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception(
            "Unhandled exception",
            error=str(exc),
            path=request.url.path,
            request_id=request_id,
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred." if settings.is_production else str(exc),
                },
                "request_id": request_id,
            },
        )

"""Custom application exceptions.

كل استثناء يحمل HTTP status code مناسب عبر الخاصية status_code.
"""

from __future__ import annotations


class AppError(Exception):
    """الاستثناء الأساسي لكل أخطاء التطبيق."""

    status_code: int = 500
    error_code: str = "internal_error"
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, error_code: str | None = None):
        self.message = message or self.default_message
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)


class NotFoundError(AppError):
    """عندما لا يوجد المورد المطلوب."""

    status_code = 404
    error_code = "not_found"
    default_message = "Resource not found."


class ValidationError(AppError):
    """خطأ في التحقق من البيانات على مستوى الـ business logic."""

    status_code = 422
    error_code = "validation_error"
    default_message = "Validation failed."


class ConflictError(AppError):
    """تعارض في الحالة (مثلاً: pipeline يعمل بالفعل)."""

    status_code = 409
    error_code = "conflict"
    default_message = "Resource state conflict."


class PipelineError(AppError):
    """خطأ أثناء تنفيذ الـ pipeline."""

    status_code = 500
    error_code = "pipeline_error"
    default_message = "Pipeline execution failed."


class DatabaseError(AppError):
    """خطأ في قاعدة البيانات."""

    status_code = 500
    error_code = "database_error"
    default_message = "Database operation failed."


class WebSocketError(AppError):
    """خطأ في اتصال WebSocket."""

    status_code = 500
    error_code = "websocket_error"
    default_message = "WebSocket operation failed."

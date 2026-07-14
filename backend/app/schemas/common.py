"""Common schemas: response envelope, pagination, etc."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    """الغلاف القياسي لكل استجابات الـ API."""

    success: bool = True
    data: T | None = None
    error: dict[str, str] | None = None
    request_id: str | None = None


class PaginationMeta(BaseModel):
    """بيانات الـ pagination."""

    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """استجابة مُصفّحة."""

    items: list[T]
    pagination: PaginationMeta


class HealthResponse(BaseModel):
    """استجابة فحص الصحة."""

    status: str = "ok"
    app_name: str
    version: str
    timestamp: str

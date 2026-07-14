"""Pagination helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PaginationParams:
    """معاملات الـ pagination القياسية."""

    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return max(0, (self.page - 1) * self.page_size)

    @property
    def limit(self) -> int:
        return min(max(self.page_size, 1), 100)


@dataclass
class PaginatedResult:
    """نتيجة مُصفّحة جاهزة للإرسال."""

    items: list
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.total == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total": self.total,
                "total_pages": self.total_pages,
                "has_next": self.page < self.total_pages,
                "has_prev": self.page > 1,
            },
        }

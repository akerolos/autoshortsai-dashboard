"""API Key authentication for dashboard endpoints.

يُستخدم لتأمين endpoint الـ report اللي بيتنادى من GitHub Actions.
"""

from __future__ import annotations

import os
import secrets
import hmac

from fastapi import Header, HTTPException, Security

from app.core.config import settings


def get_api_key(x_api_key: str = Header(None, alias="X-API-Key")) -> str:
    """يتحقق من الـ API key المرسلة في الـ header.

    في وضع التطوير، لو مفيش API key مضبوطة في البيئة، بيرجّع default.
    في الإنتاج، لازم DASHBOARD_API_KEY يكون مضبوط.
    """
    expected_key = os.environ.get("DASHBOARD_API_KEY", "")

    # في وضع التطوير بدون API key، نسمح بالمرور
    if settings.is_development and not expected_key:
        return "dev-mode"

    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="DASHBOARD_API_KEY not configured on server",
        )

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="X-API-Key header is required",
        )

    # مقارنة آمنة ضد timing attacks
    if not hmac.compare_digest(x_api_key, expected_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )

    return x_api_key


def generate_api_key() -> str:
    """يولّد API key عشوائي قوي."""
    return secrets.token_urlsafe(32)

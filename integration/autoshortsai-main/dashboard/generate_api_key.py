#!/usr/bin/env python3
"""
سكربت لتوليد API key قوي للـ Dashboard.

شغّله مرة واحدة وانسخ الـ key الناتج:
    python generate_api_key.py
"""

import secrets
import string


def generate_api_key(length: int = 40) -> str:
    """يولّد API key عشوائي قوي."""
    # رموز مسموحة: حروف وأرقام و - و _
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


if __name__ == "__main__":
    api_key = generate_api_key()
    print("\n" + "=" * 60)
    print("🔐 Your Dashboard API Key:")
    print("=" * 60)
    print(api_key)
    print("=" * 60)
    print("\n📝 الخطوات الجاية:")
    print("1. انسخ الـ key ده")
    print("2. افتح repo بتاع AutoShortsAI على GitHub")
    print("3. Settings → Secrets and variables → Actions → New repository secret")
    print("4. Name: DASHBOARD_API_KEY")
    print(f"5. Value: {api_key}")
    print("6. اعمل نفس الحاجة على Render.com:")
    print("   Dashboard service → Environment → Add Environment Variable")
    print(f"   Key: DASHBOARD_API_KEY | Value: {api_key}")
    print("\n⚠️  احتفظ بهذا الـ key سرّياً! لا تشاركه مع أحد.")
    print("=" * 60 + "\n")

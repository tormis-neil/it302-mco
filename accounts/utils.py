"""Utility helpers for the accounts app."""
from __future__ import annotations

from typing import Optional

from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str:
    """Return the best-effort client IP address for rate limiting."""

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        parts = [part.strip() for part in forwarded_for.split(",") if part.strip()]
        if parts:
            return parts[0]
    remote_addr: Optional[str] = request.META.get("REMOTE_ADDR")
    return remote_addr or "0.0.0.0"
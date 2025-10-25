"""Utility helpers for the accounts app."""
from __future__ import annotations

from typing import Optional

from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str:
    """
    Get client IP address for rate limiting.

    Security Note:
    Uses REMOTE_ADDR which cannot be spoofed by the client, ensuring
    rate limiting cannot be bypassed by sending fake X-Forwarded-For headers.

    For academic demonstration, this prevents the IP spoofing attack where
    an attacker could bypass rate limits by cycling through fake IP addresses.

    Production deployment behind a reverse proxy (nginx, Cloudflare, etc.)
    would require configuring trusted proxy IPs to safely use X-Forwarded-For.
    See: https://docs.djangoproject.com/en/4.2/ref/settings/#secure-proxy-ssl-header

    Args:
        request: Django HttpRequest object

    Returns:
        Client IP address as string (e.g., "127.0.0.1")
    """
    remote_addr: Optional[str] = request.META.get("REMOTE_ADDR")
    return remote_addr or "0.0.0.0"
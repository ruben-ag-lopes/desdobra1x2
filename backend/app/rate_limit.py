"""Shared rate limiter (docs/plano-seguranca.md).

In-memory: works per serverless instance, not shared across them on Vercel. Good enough to blunt
basic abuse; a shared store (Upstash Redis) is the fase-2 upgrade once there's real traffic.
"""

from fastapi import Request
from slowapi import Limiter


def client_ip(request: Request) -> str:
    """The visitor's real IP. Behind Vercel's proxy `request.client.host` is the proxy, so every
    visitor would share one limit; Vercel overwrites X-Forwarded-For with the real client address
    (a client can't spoof it there). Locally there is no proxy and we fall back to the socket peer."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip)

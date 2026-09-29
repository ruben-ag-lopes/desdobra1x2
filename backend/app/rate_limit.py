"""Shared rate limiter (docs/plano-seguranca.md).

In-memory: works per serverless instance, not shared across them on Vercel. Good enough to blunt
basic abuse; a shared store (Upstash Redis) is the fase-2 upgrade once there's real traffic.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

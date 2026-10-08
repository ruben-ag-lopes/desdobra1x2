import time
from typing import Any, Callable

from fastapi import Response


def cdn_cache(response: Response, seconds: int) -> None:
    """Let a shared CDN (e.g. Vercel's) serve this response for `seconds`, then refresh it in the background."""
    response.headers["Cache-Control"] = f"public, max-age=60, s-maxage={seconds}, stale-while-revalidate={seconds * 4}"


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get_or_set(self, key: str, factory: Callable[[], Any], cache_empty: bool = True) -> Any:
        """`cache_empty=False` keeps an empty result (e.g. no contest found) from being served for a whole TTL."""
        now = time.time()
        cached = self._store.get(key)
        if cached is not None and now - cached[0] < self.ttl_seconds:
            return cached[1]

        value = factory()
        if cache_empty or value:
            self._store[key] = (now, value)
        return value

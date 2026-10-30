import time
from typing import Any, Callable

from fastapi import Response


def cdn_cache(response: Response, seconds: int) -> None:
    """Let a shared CDN (e.g. Vercel's) serve this response for `seconds`, then refresh it in the background."""
    response.headers["Cache-Control"] = f"public, max-age=60, s-maxage={seconds}, stale-while-revalidate={seconds * 4}"


FAILURE_TTL_SECONDS = 60


class _Failure:
    def __init__(self, error: Exception):
        self.error = error


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get_or_set(self, key: str, factory: Callable[[], Any], cache_empty: bool = True) -> Any:
        """`cache_empty=False` keeps an empty result (e.g. no contest found) from being served for a whole TTL.

        A failing `factory` is remembered for a minute and re-raised, so a site that is down is not
        called again by every visitor.
        """
        now = time.time()
        cached = self._store.get(key)
        if cached is not None:
            stored_at, value = cached
            failed = isinstance(value, _Failure)
            if now - stored_at < (FAILURE_TTL_SECONDS if failed else self.ttl_seconds):
                if failed:
                    raise value.error
                return value

        try:
            value = factory()
        except Exception as e:
            self._store[key] = (now, _Failure(e))
            raise
        if cache_empty or value:
            self._store[key] = (now, value)
        return value

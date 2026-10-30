"""Run with: python -m unittest tests.test_cache"""

import unittest

from app.cache import TTLCache


class FailureCacheTest(unittest.TestCase):
    def test_a_failing_source_is_called_once_not_by_every_visitor(self):
        calls = []

        def down():
            calls.append(1)
            raise RuntimeError("site is down")

        cache = TTLCache(ttl_seconds=3600)
        for _ in range(5):
            with self.assertRaises(RuntimeError):
                cache.get_or_set("k", down)
        self.assertEqual(len(calls), 1)

    def test_success_is_still_cached(self):
        calls = []
        cache = TTLCache(ttl_seconds=3600)
        for _ in range(3):
            cache.get_or_set("k", lambda: calls.append(1) or "ok")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()

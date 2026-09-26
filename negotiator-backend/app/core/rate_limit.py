# app/core/rate_limit.py
"""
Simple in-memory rate limiter. No external dependencies.

Not suitable for multi-process deployment (each worker has its own counter).
For production behind multiple workers, replace with Redis-backed slowapi.
"""
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str) -> bool:
        """Return True if request is allowed, False if rate limit exceeded."""
        now = time.time()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._buckets[key]
            bucket[:] = [t for t in bucket if t > cutoff]
            if len(bucket) >= self.max_requests:
                return False
            bucket.append(now)
            return True

    def reset(self) -> None:
        """Clear all buckets. Used in tests."""
        with self._lock:
            self._buckets.clear()


# 5 admin registrations per hour per IP
admin_register_limiter = InMemoryRateLimiter(
    max_requests=5,
    window_seconds=3600,
)
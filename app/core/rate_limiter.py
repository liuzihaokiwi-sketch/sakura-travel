"""
app/core/rate_limiter.py

In-memory sliding-window rate limiter middleware for FastAPI.

Design goals:
  - Zero external dependencies (no Redis required)
  - Backend interface (RateLimitBackend) allows drop-in Redis swap later
  - Per-IP tracking with configurable limits per route group
  - Proper 429 responses with retry_after and rate-limit headers

Route-group limits (requests / minute):
  - Generation endpoints (/trips/*/generate, /admin/generate): 5 req/min
  - Public form endpoints (/submissions, /detail-forms, /orders): 30 req/min
  - General API (everything else): 60 req/min

Skipped paths: /ops/*, /admin/sync*, /health, /docs, /redoc, /openapi
"""
from __future__ import annotations

import asyncio
import os
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Route group definitions
# ---------------------------------------------------------------------------

# (prefix_or_substring, window_seconds, max_requests)
_GENERATION_ROUTES: list[str] = [
    "/generate",          # matches /trips/{id}/generate and /admin/generate
]

_PUBLIC_FORM_ROUTES: list[str] = [
    "/submissions",
    "/detail-forms",
    "/orders",
    "/quiz",
]

# Paths that bypass rate limiting entirely
_SKIP_PREFIXES: tuple[str, ...] = (
    "/ops/",
    "/admin/sync",
    "/health",
    "/docs",
    "/redoc",
    "/openapi",
)

# Defaults
GENERATION_WINDOW = 60
GENERATION_MAX = 5

PUBLIC_FORM_WINDOW = 60
PUBLIC_FORM_MAX = 30

GENERAL_WINDOW = 60
GENERAL_MAX = 60


# ---------------------------------------------------------------------------
# Backend interface  (swap in Redis later by implementing this ABC)
# ---------------------------------------------------------------------------

class RateLimitBackend(ABC):
    """Abstract backend for rate-limit state storage."""

    @abstractmethod
    async def hit(
        self, key: str, window: int, max_requests: int
    ) -> tuple[bool, int, int, int]:
        """
        Record a request and check the limit.

        Returns:
            (is_allowed, current_count, limit, reset_after_seconds)
        """
        ...

    async def close(self) -> None:  # noqa: B027
        """Optional cleanup hook."""


# ---------------------------------------------------------------------------
# In-memory sliding-window backend
# ---------------------------------------------------------------------------

class InMemoryBackend(RateLimitBackend):
    """
    Sliding-window counter stored in a dict of lists.

    Each key maps to a sorted list of request timestamps.
    A periodic cleanup task evicts expired entries to bound memory usage.
    """

    def __init__(self, cleanup_interval: float = 60.0) -> None:
        # key -> list of timestamps (floats)
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None

    async def _start_cleanup(self) -> None:
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        """Periodically remove expired timestamps to prevent memory leak."""
        try:
            while True:
                await asyncio.sleep(self._cleanup_interval)
                now = time.time()
                async with self._lock:
                    empty_keys: list[str] = []
                    for key, timestamps in self._windows.items():
                        # Keep only timestamps within the widest possible window
                        # We use a generous cutoff; exact per-key windows are
                        # enforced in hit().
                        cutoff = now - 3600  # 1 hour max
                        self._windows[key] = [
                            t for t in timestamps if t > cutoff
                        ]
                        if not self._windows[key]:
                            empty_keys.append(key)
                    for key in empty_keys:
                        del self._windows[key]
        except asyncio.CancelledError:
            pass

    async def hit(
        self, key: str, window: int, max_requests: int
    ) -> tuple[bool, int, int, int]:
        now = time.time()
        cutoff = now - window

        # Ensure cleanup task is running
        await self._start_cleanup()

        async with self._lock:
            # Evict expired entries for this key
            timestamps = self._windows[key]
            self._windows[key] = [t for t in timestamps if t > cutoff]
            timestamps = self._windows[key]

            current_count = len(timestamps)
            is_allowed = current_count < max_requests

            if is_allowed:
                timestamps.append(now)
                current_count += 1

            # Compute reset: seconds until the oldest entry in the window expires
            if timestamps:
                reset_after = max(0, int(timestamps[0] + window - now))
            else:
                reset_after = window

            remaining = max(0, max_requests - current_count)
            return is_allowed, remaining, max_requests, reset_after

    async def close(self) -> None:
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


# ---------------------------------------------------------------------------
# Helper: extract client IP
# ---------------------------------------------------------------------------

def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


# ---------------------------------------------------------------------------
# Classify a request path into its rate-limit group
# ---------------------------------------------------------------------------

def _classify_path(path: str) -> tuple[str, int, int]:
    """
    Returns (group_name, window_seconds, max_requests) for the given path.
    """
    # Generation endpoints (most restrictive -- check first)
    for pattern in _GENERATION_ROUTES:
        if pattern in path:
            return "generate", GENERATION_WINDOW, GENERATION_MAX

    # Public form endpoints
    for prefix in _PUBLIC_FORM_ROUTES:
        if path.startswith(prefix):
            return "form", PUBLIC_FORM_WINDOW, PUBLIC_FORM_MAX

    # Everything else
    return "general", GENERAL_WINDOW, GENERAL_MAX


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI rate-limiting middleware using a pluggable backend.

    Usage in main.py:
        from app.core.rate_limiter import RateLimitMiddleware, InMemoryBackend
        app.add_middleware(RateLimitMiddleware, backend=InMemoryBackend())

    To switch to Redis later:
        from app.core.rate_limiter import RateLimitMiddleware
        app.add_middleware(RateLimitMiddleware, backend=RedisBackend(pool))
    """

    def __init__(self, app, backend: Optional[RateLimitBackend] = None) -> None:  # type: ignore[override]
        super().__init__(app)
        self.backend: RateLimitBackend = backend or InMemoryBackend()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # Skip paths that should not be rate-limited
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            return await call_next(request)

        ip = _get_client_ip(request)
        group, window, max_requests = _classify_path(path)
        key = f"rl:{ip}:{group}"

        try:
            is_allowed, remaining, limit, reset_after = await self.backend.hit(
                key, window, max_requests
            )
        except Exception:
            logger.debug("Rate-limit check failed, allowing request", exc_info=True)
            return await call_next(request)

        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_after),
        }

        if not is_allowed:
            logger.info(
                "Rate limit hit: ip=%s group=%s path=%s limit=%d",
                ip, group, path, limit,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "请求过于频繁，请稍后再试",
                    "retry_after": reset_after,
                },
                headers=headers,
            )

        response = await call_next(request)
        for k, v in headers.items():
            response.headers[k] = v
        return response


# ---------------------------------------------------------------------------
# 全局 AI API 调用限速器（供数据采集脚本使用，与 HTTP 中间件无关）
# ---------------------------------------------------------------------------

class GlobalRateLimiter:
    """
    全局 AI API 调用限速器，确保任意两次实际 AI 调用间隔 >= min_interval_seconds。

    使用方式：
        from app.core.rate_limiter import ai_rate_limiter
        await ai_rate_limiter.wait()   # 在调用 AI 前等待
    """

    def __init__(self, min_interval_seconds: float = 10.0) -> None:
        self.min_interval_seconds = min_interval_seconds
        self._last_call_time: float = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        """等待直到距上次调用已超过 min_interval_seconds。"""
        async with self._lock:
            elapsed = time.time() - self._last_call_time
            if elapsed < self.min_interval_seconds:
                sleep_secs = self.min_interval_seconds - elapsed
                logger.debug(
                    "GlobalRateLimiter: sleeping %.1fs before next AI call", sleep_secs
                )
                await asyncio.sleep(sleep_secs)
            self._last_call_time = time.time()


# 模块级单例，供 ai_cache.py 直接 import 使用
# DashScope 不封 IP，可以快跑。saiai 用时改为 30
_AI_MIN_INTERVAL = float(os.environ.get("AI_RATE_LIMIT_INTERVAL", "1.0"))
ai_rate_limiter = GlobalRateLimiter(min_interval_seconds=_AI_MIN_INTERVAL)

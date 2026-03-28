"""
app/core/rate_limit.py

基于 Redis 滑动窗口的 API 限流中间件。

限流策略（可通过 .env 覆盖）：
  RATE_LIMIT_PER_IP        每 IP 每分钟请求上限（默认 60）
  RATE_LIMIT_GENERATE      /trips/generate 每 IP 每小时上限（默认 10）
  RATE_LIMIT_SUBMISSIONS   /submissions 每 IP 每小时上限（默认 20）

Redis 不可用时：降级为放行（不阻断服务）。
管理接口 /ops/* 和 /admin/* 不限流。
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)

# ── 限流规则 ──────────────────────────────────────────────────────────────────

# (path_prefix, window_seconds, max_requests)
_ROUTE_RULES: list[tuple[str, int, int]] = [
    ("/trips/generate",  3600, 10),   # 生成接口：每小时10次
    ("/submissions",     3600, 20),   # 提单接口：每小时20次
    ("/orders",          3600, 30),   # 订单接口：每小时30次
]

_DEFAULT_WINDOW = 60      # 默认滑动窗口（秒）
_DEFAULT_MAX    = 60      # 默认每窗口最大请求数

# 跳过限流的前缀
_SKIP_PREFIXES = ("/ops/", "/admin/", "/health", "/docs", "/redoc", "/openapi")


def _get_client_ip(request: Request) -> str:
    """从请求头或连接信息中提取客户端 IP。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _check_rate_limit(
    redis_client,
    key: str,
    window: int,
    max_requests: int,
) -> tuple[bool, int, int]:
    """
    滑动窗口限流检查（Redis sorted set 实现）。
    返回 (is_allowed, current_count, reset_after_seconds)
    """
    now = time.time()
    window_start = now - window

    pipe = redis_client.pipeline()
    # 清除窗口外的旧请求
    pipe.zremrangebyscore(key, 0, window_start)
    # 计算当前窗口内的请求数
    pipe.zcard(key)
    # 记录本次请求
    pipe.zadd(key, {str(now): now})
    # 设置 key 过期（避免永久占用内存）
    pipe.expire(key, window + 10)

    results = await pipe.execute()
    current_count: int = results[1]  # zcard 结果（加入当前请求前）

    is_allowed = current_count < max_requests
    reset_after = int(window - (now - window_start))
    return is_allowed, current_count + 1, max(0, reset_after)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 限流中间件。
    依赖 app.core.queue 的 Redis 连接池（Redis 不可用时静默放行）。
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # 跳过不限流的路由
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            return await call_next(request)

        # 获取 Redis 连接（不可用则放行）
        from app.core.queue import get_redis_pool
        redis = get_redis_pool()
        if redis is None:
            return await call_next(request)

        ip = _get_client_ip(request)

        # 匹配路由规则
        window = _DEFAULT_WINDOW
        max_req = _DEFAULT_MAX
        for prefix, w, m in _ROUTE_RULES:
            if path.startswith(prefix):
                window, max_req = w, m
                break

        key = f"rl:{ip}:{path.split('/')[1]}:{window}"

        try:
            is_allowed, count, reset_after = await _check_rate_limit(
                redis, key, window, max_req
            )
        except Exception as e:
            logger.debug("限流检查异常（放行）: %s", e)
            return await call_next(request)

        # 添加限流响应头
        response_headers = {
            "X-RateLimit-Limit": str(max_req),
            "X-RateLimit-Remaining": str(max(0, max_req - count)),
            "X-RateLimit-Reset": str(reset_after),
        }

        if not is_allowed:
            logger.info("限流触发 ip=%s path=%s count=%d limit=%d", ip, path, count, max_req)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"请求过于频繁，请 {reset_after} 秒后重试",
                    "retry_after": reset_after,
                },
                headers=response_headers,
            )

        response = await call_next(request)
        for k, v in response_headers.items():
            response.headers[k] = v
        return response

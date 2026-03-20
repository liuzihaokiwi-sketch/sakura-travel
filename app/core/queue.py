from __future__ import annotations

"""
arq Redis pool 初始化与 job 入队工具。
"""
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings

# 模块级单例
_redis_pool: aioredis.Optional[Redis] = None


async def init_redis_pool() -> None:
    global _redis_pool
    _redis_pool = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=False,  # arq 需要 bytes
    )


async def close_redis_pool() -> None:
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None


def get_redis_pool() -> aioredis.Optional[Redis]:
    return _redis_pool


async def enqueue_job(job_name: str, *args: Any, **kwargs: Any) -> Optional[str]:
    """
    将 job 推入 arq 队列。
    返回 job_id（arq 生成的 UUID），失败返回 None。

    注意：arq 的 RedisSettings 在 worker 里配置，
    这里直接用 raw Redis 命令写 arq 协议。
    为了简洁，推荐使用 arq.create_pool 的方式。
    """
    from arq import create_pool
    from arq.connections import RedisSettings

    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    job = await pool.enqueue_job(job_name, *args, **kwargs)
    await pool.aclose()
    return job.job_id if job else None

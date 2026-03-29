"""
cleanup_snapshots.py — 过期快照清理 Job

触发方式：
  - arq cron job，每天凌晨 2 点自动跑
  - 手动入队：await enqueue_job("cleanup_snapshots")

功能：
  删除 source_snapshots 表中 expires_at < now() 的记录。
  每次最多删 10000 条，避免锁表。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

_BATCH_SIZE = 10_000


async def cleanup_snapshots(ctx: Any = None) -> dict:
    """
    删除所有已过期的 source_snapshots 记录。

    Returns:
        {"deleted": int, "remaining_expired": int}
    """
    from app.db.models.snapshots import SourceSnapshot

    now = datetime.now(timezone.utc)
    total_deleted = 0

    async with AsyncSessionLocal() as session:
        # 统计过期数量
        count_result = await session.execute(
            select(func.count()).where(SourceSnapshot.expires_at < now)
        )
        remaining = count_result.scalar() or 0

        if remaining == 0:
            logger.info("[cleanup_snapshots] 无过期快照，跳过")
            return {"deleted": 0, "remaining_expired": 0}

        # 分批删除，避免单次大事务锁表
        while True:
            # 取一批过期 ID
            ids_result = await session.execute(
                select(SourceSnapshot.snapshot_id)
                .where(SourceSnapshot.expires_at < now)
                .limit(_BATCH_SIZE)
            )
            ids = [row[0] for row in ids_result.all()]
            if not ids:
                break

            result = await session.execute(
                delete(SourceSnapshot).where(SourceSnapshot.snapshot_id.in_(ids))
            )
            await session.commit()
            deleted = result.rowcount or 0
            total_deleted += deleted
            logger.info("[cleanup_snapshots] 已删除 %d 条过期快照（本批）", deleted)

            if deleted < _BATCH_SIZE:
                break

    logger.info("[cleanup_snapshots] 完成，共删除 %d 条", total_deleted)
    return {"deleted": total_deleted, "remaining_expired": max(0, remaining - total_deleted)}

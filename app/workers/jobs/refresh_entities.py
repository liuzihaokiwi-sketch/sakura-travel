"""
app/workers/jobs/refresh_entities.py

定时实体刷新 Job。

策略：
- 每次取 last_refreshed_at 最旧的 N 个实体（或从未刷新过的）
- S 级（人工校准）实体跳过 AI 刷新，只更新时间戳
- A/B 级实体用 AI 重新生成数据
- 单个实体失败不影响其他

触发方式：
- arq cron job，每天凌晨 3 点自动跑
- 也可以手动入队：await enqueue_job("refresh_entities")

配置（环境变量可覆盖）：
- REFRESH_BATCH_SIZE      每次刷新多少个实体（默认 20）
- REFRESH_THRESHOLD_DAYS  超过多少天没刷新才纳入候选（默认 30）
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.models.catalog import EntityBase

logger = logging.getLogger(__name__)

REFRESH_BATCH_SIZE = int(os.environ.get("REFRESH_BATCH_SIZE", "20"))
REFRESH_THRESHOLD_DAYS = int(os.environ.get("REFRESH_THRESHOLD_DAYS", "30"))

# S 级数据不用 AI 刷新（人工校准过，AI 覆盖会降级）
_SKIP_AI_REFRESH_TIERS = frozenset(["S"])


async def refresh_entities(ctx: dict) -> dict[str, Any]:
    """
    arq job 入口：刷新一批最旧的实体数据。

    Returns:
        {refreshed: N, skipped_s_tier: N, skipped: N, errors: [...]}
    """
    stats: dict[str, Any] = {"refreshed": 0, "skipped_s_tier": 0, "skipped": 0, "errors": []}
    threshold = datetime.now(timezone.utc) - timedelta(days=REFRESH_THRESHOLD_DAYS)

    async with AsyncSessionLocal() as session:
        # 取候选：从未刷新过 或 超过阈值天数未刷新，按最旧优先
        result = await session.execute(
            select(
                EntityBase.entity_id,
                EntityBase.name_zh,
                EntityBase.city_code,
                EntityBase.entity_type,
                EntityBase.data_tier,
            )
            .where(
                EntityBase.is_active == True,
                EntityBase.entity_type.in_(["poi", "restaurant", "hotel"]),
                or_(
                    EntityBase.last_refreshed_at == None,
                    EntityBase.last_refreshed_at < threshold,
                ),
            )
            .order_by(EntityBase.last_refreshed_at.asc().nullsfirst())
            .limit(REFRESH_BATCH_SIZE)
        )
        candidates = result.all()

    if not candidates:
        logger.info("[refresh_entities] 没有需要刷新的实体")
        return stats

    logger.info("[refresh_entities] 本批候选 %d 个实体", len(candidates))

    for row in candidates:
        entity_id, name_zh, city_code, entity_type, data_tier = row

        # S 级数据跳过 AI 刷新，只更新时间戳
        if data_tier in _SKIP_AI_REFRESH_TIERS:
            try:
                async with AsyncSessionLocal() as session:
                    async with session.begin():
                        await session.execute(
                            EntityBase.__table__.update()
                            .where(EntityBase.entity_id == entity_id)
                            .values(last_refreshed_at=datetime.now(timezone.utc))
                        )
                stats["skipped_s_tier"] += 1
                logger.debug("[refresh_entities] S 级跳过 AI 刷新: %s", name_zh)
            except Exception as e:
                stats["errors"].append(f"{name_zh}: timestamp update failed: {e}")
            continue

        try:
            await _refresh_one(entity_id, name_zh, city_code, entity_type)
            stats["refreshed"] += 1
        except Exception as e:
            logger.warning(
                "[refresh_entities] 刷新失败: %s (%s) — %s",
                name_zh, entity_id, e,
            )
            stats["errors"].append(f"{name_zh}: {e}")
            stats["skipped"] += 1

    logger.info(
        "[refresh_entities] 完成 — 刷新: %d  S级跳过: %d  失败: %d  错误: %d",
        stats["refreshed"], stats["skipped_s_tier"], stats["skipped"], len(stats["errors"]),
    )
    return stats


async def _refresh_one(
    entity_id: Any,
    name_zh: str,
    city_code: str,
    entity_type: str,
) -> None:
    """
    刷新单个 A/B 级实体：用 AI 重新生成数据，写回 DB，更新 last_refreshed_at。
    """
    from app.domains.catalog.ai_generator import (
        generate_entity_by_name,
        CITY_MAP,
    )
    from app.domains.catalog.upsert import upsert_entity

    if not name_zh or city_code not in CITY_MAP:
        return

    # 重新生成
    data = await generate_entity_by_name(
        name_zh=name_zh,
        city_code=city_code,
        entity_type=entity_type,
    )
    if not data:
        return

    # 写回 DB（upsert 会通过 name_zh + city_code 命中同一条记录）
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await upsert_entity(
                session=session,
                entity_type=entity_type,
                data=data,
            )
            # 更新刷新时间
            await session.execute(
                EntityBase.__table__.update()
                .where(EntityBase.entity_id == entity_id)
                .values(last_refreshed_at=datetime.now(timezone.utc))
            )

    logger.debug("[refresh_entities] 刷新完成: %s / %s", city_code, name_zh)

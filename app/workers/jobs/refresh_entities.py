"""
app/workers/jobs/refresh_entities.py

定时实体刷新 Job。

策略：
- 每次取 last_refreshed_at 最旧的 N 个实体（或从未刷新过的）
- 用 AI 重新生成该实体的数据，更新 DB
- 更新 last_refreshed_at = now()
- 单个实体失败不影响其他

触发方式：
- arq cron job，每天凌晨 3 点自动跑
- 也可以手动入队：await enqueue_job("refresh_entities")

配置（默认）：
- REFRESH_BATCH_SIZE = 20   每次刷新多少个实体
- REFRESH_THRESHOLD_DAYS = 30  超过多少天没刷新才纳入候选
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.models.catalog import EntityBase

logger = logging.getLogger(__name__)

REFRESH_BATCH_SIZE = 20
REFRESH_THRESHOLD_DAYS = 30


async def refresh_entities(ctx: dict) -> dict[str, Any]:
    """
    arq job 入口：刷新一批最旧的实体数据。

    Returns:
        {refreshed: N, skipped: N, errors: [...]}
    """
    stats: dict[str, Any] = {"refreshed": 0, "skipped": 0, "errors": []}
    threshold = datetime.now(timezone.utc) - timedelta(days=REFRESH_THRESHOLD_DAYS)

    async with AsyncSessionLocal() as session:
        # 取候选：从未刷新过 或 超过阈值天数未刷新，按最旧优先
        result = await session.execute(
            select(EntityBase)
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
        entities = result.scalars().all()

    if not entities:
        logger.info("[refresh_entities] 没有需要刷新的实体")
        return stats

    logger.info("[refresh_entities] 本批刷新 %d 个实体", len(entities))

    for entity in entities:
        try:
            await _refresh_one(entity)
            stats["refreshed"] += 1
        except Exception as e:
            logger.warning(
                "[refresh_entities] 刷新失败: %s (%s) — %s",
                entity.name_zh, entity.entity_id, e,
            )
            stats["errors"].append(f"{entity.name_zh}: {e}")
            stats["skipped"] += 1

    logger.info(
        "[refresh_entities] 完成 — 刷新: %d  跳过: %d  错误: %d",
        stats["refreshed"], stats["skipped"], len(stats["errors"]),
    )
    return stats


async def _refresh_one(entity: EntityBase) -> None:
    """
    刷新单个实体：用 AI 重新生成数据，写回 DB，更新 last_refreshed_at。
    """
    from app.domains.catalog.ai_generator import (
        generate_entity_by_name,
        CITY_MAP,
    )
    from app.domains.catalog.upsert import upsert_entity

    city_code = entity.city_code
    name_zh = entity.name_zh
    entity_type = entity.entity_type

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

    # 写回 DB（upsert by name_zh + city_code，会命中同一条记录）
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
                .where(EntityBase.entity_id == entity.entity_id)
                .values(last_refreshed_at=datetime.now(timezone.utc))
            )

    logger.debug("[refresh_entities] 刷新完成: %s / %s", city_code, name_zh)

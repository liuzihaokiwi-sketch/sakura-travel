"""
arq Job: decay_recommendation_counts
每天凌晨2点运行，清零超过30天未被推荐的实体计数。
"""
from __future__ import annotations

import logging

from app.db.session import AsyncSessionLocal
from app.domains.ranking.rotation import decay_stale_counts

logger = logging.getLogger(__name__)


async def decay_recommendation_counts(ctx: dict) -> dict:
    logger.info("decay_recommendation_counts 开始")
    async with AsyncSessionLocal() as session:
        result = await decay_stale_counts(session)
    logger.info("decay_recommendation_counts 完成: %s", result)
    return result

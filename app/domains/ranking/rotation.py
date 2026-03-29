"""
app/domains/ranking/rotation.py

推荐轮转机制：
  - 每次实体被选入行程时，记录 recommendation_count_30d + last_recommended_at
  - 评分时对高推荐次数实体施加对数降权（rotation_penalty）
  - 每天凌晨2点运行 decay_stale_counts()，清除30天外的计数
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ─── 轮转降权公式 ─────────────────────────────────────────────────────────────
#
# rotation_penalty = min(MAX_PENALTY, α × log2(1 + count_30d))
#
# count_30d=0  → penalty=0      (不惩罚)
# count_30d=1  → penalty≈0.15   (-0.15分)
# count_30d=5  → penalty≈0.38   (-0.38分)
# count_30d=20 → penalty≈0.69   (-0.69分)
# count_30d=50 → MAX_PENALTY=1.0

_ROTATION_ALPHA = 0.30    # 降权系数，可调
_MAX_PENALTY    = 1.0     # 最大降权幅度（评分0-100量级下约1分）


def compute_rotation_penalty(recommendation_count_30d: int) -> float:
    """
    根据过去30天推荐次数计算轮转惩罚分（0 ~ MAX_PENALTY）。
    惩罚分在 compute_base_score 后直接减去。
    """
    if recommendation_count_30d <= 0:
        return 0.0
    penalty = _ROTATION_ALPHA * math.log2(1 + recommendation_count_30d)
    return min(_MAX_PENALTY, round(penalty, 3))


def apply_rotation_penalty(base_score: float, count_30d: int) -> float:
    """
    对高频推荐实体施加百分比软降权。

    分档规则：
      - 0-5 次推荐：无惩罚
      - 6-10 次：-5% score
      - 11-20 次：-10% score
      - 21+ 次：-15% score

    与 compute_rotation_penalty（对数绝对扣分）互补：
      compute_rotation_penalty 在 base_score 计算内部扣绝对分，
      apply_rotation_penalty 在 final_score 层做百分比缩放，
      两者共同实现平滑的轮转压制。
    """
    if count_30d <= 5:
        return base_score
    elif count_30d <= 10:
        return round(base_score * 0.95, 2)
    elif count_30d <= 20:
        return round(base_score * 0.90, 2)
    else:
        return round(base_score * 0.85, 2)


# ─── 记录推荐事件 ─────────────────────────────────────────────────────────────

async def record_recommendations(
    session: AsyncSession,
    entity_ids: Sequence[str],
) -> None:
    """
    批量记录实体被推荐进行程：
      - recommendation_count_30d += 1
      - last_recommended_at = now()

    调用方：generate_trip.py 在行程生成完成后调用。
    """
    if not entity_ids:
        return

    now = datetime.now(timezone.utc)
    try:
        await session.execute(
            text("""
                UPDATE entity_base
                SET recommendation_count_30d = recommendation_count_30d + 1,
                    last_recommended_at = :now
                WHERE entity_id = ANY(:ids::uuid[])
            """),
            {"now": now, "ids": list(entity_ids)},
        )
        logger.debug("推荐计数更新: %d 个实体", len(entity_ids))
    except Exception as e:
        logger.warning("推荐计数更新失败（不阻断流程）: %s", e)


async def increment_recommendation(
    session: AsyncSession,
    entity_ids: list[UUID],
) -> None:
    """
    行程定稿后调用：批量递增推荐计数并更新时间戳。

    这是 record_recommendations 的 UUID 类型入口，
    供 generate_trip 等上层直接传入 UUID 列表。
    """
    str_ids = [str(eid) for eid in entity_ids if eid]
    await record_recommendations(session, str_ids)


# ─── 30天衰减重置 ─────────────────────────────────────────────────────────────

async def decay_stale_counts(session: AsyncSession) -> dict:
    """
    将超过30天未被推荐的实体的 recommendation_count_30d 重置为0。
    设计为每天凌晨2点运行的 cron job 内调用。
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    result = await session.execute(
        text("""
            UPDATE entity_base
            SET recommendation_count_30d = 0
            WHERE last_recommended_at < :cutoff
              AND recommendation_count_30d > 0
            RETURNING entity_id
        """),
        {"cutoff": cutoff},
    )
    reset_count = len(result.fetchall())
    await session.commit()
    logger.info("轮转衰减完成：%d 个实体计数已重置", reset_count)
    return {"reset_count": reset_count}

"""
step07_5_commute_check.py — 酒店通勤可行性验证

检查每个候选酒店到各天主走廊锚点的公共交通通勤时间，
标记 pass / warning / fail 并按平均通勤时间升序排序。

判定规则：
  - 所有天均 <= max_commute_minutes → pass
  - 部分天超出 → warning（仍可选，但建议提示用户）
  - 所有天均超出 → fail（不可用，排除）

依赖：
  - app.domains.planning.route_matrix.get_travel_time
  - app.domains.planning_v2.models.CandidatePool
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.planning.route_matrix import get_travel_time
from app.domains.planning_v2.models import CandidatePool

logger = logging.getLogger(__name__)

# 当 get_travel_time 调用失败时的默认通勤分钟数
_FALLBACK_COMMUTE_MINUTES = 30


async def check_commute_feasibility(
    session: AsyncSession,
    hotel_candidates: list[CandidatePool],
    daily_main_corridors: list[dict],
    max_commute_minutes: int = 45,
    redis_client=None,
) -> list[dict]:
    """检查每个候选酒店到每天主走廊的通勤时间。

    对每个酒店：
      1. 取酒店 entity_id
      2. 对每个 daily_main_corridor 的 anchor_entity_id 调用 get_travel_time
      3. 如果任意一天超过 max_commute_minutes → 标记 warning
      4. 如果所有天都超过 → 标记 fail（该酒店不可用）

    Args:
        session: 数据库异步会话
        hotel_candidates: Step 6 产出的候选酒店列表
        daily_main_corridors: 每天主走廊信息列表
            [{"day": 1, "corridor": "higashiyama", "anchor_entity_id": "xxx"}, ...]
        max_commute_minutes: 单程通勤上限（分钟），默认 45
        redis_client: 可选 Redis 客户端，用于缓存交通查询

    Returns:
        按 avg_commute_minutes 升序排列的酒店通勤检查结果列表：
        [
          {
            "hotel_id": "xxx",
            "hotel_name": "xxx",
            "status": "pass" | "warning" | "fail",
            "commute_details": [
              {"day": 1, "corridor": "higashiyama", "minutes": 25, "mode": "transit"},
              ...
            ],
            "avg_commute_minutes": 28,
            "max_commute_minutes": 35,
          }
        ]
    """
    if not hotel_candidates:
        logger.warning("step07.5: 无候选酒店，跳过通勤检查")
        return []

    if not daily_main_corridors:
        logger.warning("step07.5: 无每日主走廊信息，跳过通勤检查")
        return []

    results: list[dict] = []

    for hotel in hotel_candidates:
        hotel_id = uuid.UUID(hotel.entity_id) if isinstance(hotel.entity_id, str) else hotel.entity_id
        commute_details: list[dict] = []

        for corridor in daily_main_corridors:
            anchor_id_raw = corridor.get("anchor_entity_id")
            if not anchor_id_raw:
                logger.warning(
                    "step07.5: day %s 走廊 %s 缺少 anchor_entity_id，跳过",
                    corridor.get("day"), corridor.get("corridor"),
                )
                continue

            anchor_id = uuid.UUID(anchor_id_raw) if isinstance(anchor_id_raw, str) else anchor_id_raw

            # 串行调用，不做高并发（Anthropic/Google API 限制）
            try:
                travel = await get_travel_time(
                    session,
                    origin_id=hotel_id,
                    dest_id=anchor_id,
                    mode="transit",
                    redis_client=redis_client,
                )
                minutes = travel.get("duration_min", _FALLBACK_COMMUTE_MINUTES)
                mode = travel.get("mode", "transit")
            except (ValueError, KeyError) as e:
                # 数据质量问题（无效ID、缺失字段）— 记录 error 级别
                logger.error(
                    "step07.5: 酒店 %s → 走廊 %s (day %s) 数据错误: %s",
                    hotel.name_zh, corridor.get("corridor"), corridor.get("day"), e,
                )
                minutes = _FALLBACK_COMMUTE_MINUTES
                mode = "fallback_data_error"
            except (ConnectionError, TimeoutError, OSError) as e:
                # 网络/API 瞬时故障 — 记录 warning 级别
                logger.warning(
                    "step07.5: 酒店 %s → 走廊 %s (day %s) 网络错误: %s，使用默认 %d 分钟",
                    hotel.name_zh, corridor.get("corridor"), corridor.get("day"),
                    e, _FALLBACK_COMMUTE_MINUTES,
                )
                minutes = _FALLBACK_COMMUTE_MINUTES
                mode = "fallback_network_error"
            except Exception as e:
                # 未预期的错误 — 记录 error 级别，标记 mode 便于追踪
                logger.error(
                    "step07.5: 酒店 %s → 走廊 %s (day %s) 未知错误: %s (%s)",
                    hotel.name_zh, corridor.get("corridor"), corridor.get("day"),
                    type(e).__name__, e,
                )
                minutes = _FALLBACK_COMMUTE_MINUTES
                mode = "fallback_unknown_error"

            commute_details.append({
                "day": corridor.get("day"),
                "corridor": corridor.get("corridor"),
                "minutes": minutes,
                "mode": mode,
            })

        # ── 汇总判定 ──────────────────────────────────────────────
        if not commute_details:
            # 没有走廊数据可校验，保守通过
            results.append({
                "hotel_id": str(hotel.entity_id),
                "hotel_name": hotel.name_zh,
                "status": "pass",
                "commute_details": [],
                "avg_commute_minutes": 0,
                "max_commute_minutes": 0,
            })
            continue

        all_minutes = [d["minutes"] for d in commute_details]
        avg_min = round(sum(all_minutes) / len(all_minutes))
        max_min = max(all_minutes)

        exceeded = [m for m in all_minutes if m > max_commute_minutes]
        if len(exceeded) == len(all_minutes):
            status = "fail"
        elif len(exceeded) > 0:
            status = "warning"
        else:
            status = "pass"

        results.append({
            "hotel_id": str(hotel.entity_id),
            "hotel_name": hotel.name_zh,
            "status": status,
            "commute_details": commute_details,
            "avg_commute_minutes": avg_min,
            "max_commute_minutes": max_min,
        })

        logger.info(
            "step07.5: 酒店 [%s] status=%s avg=%d min max=%d min (%d天/%d天超限)",
            hotel.name_zh, status, avg_min, max_min,
            len(exceeded), len(all_minutes),
        )

    # 按平均通勤时间升序排列
    results.sort(key=lambda r: r["avg_commute_minutes"])

    # 汇总日志
    total = len(results)
    pass_count = sum(1 for r in results if r["status"] == "pass")
    warn_count = sum(1 for r in results if r["status"] == "warning")
    fail_count = sum(1 for r in results if r["status"] == "fail")
    logger.info(
        "step07.5: 通勤检查完成 — 共 %d 酒店: pass=%d, warning=%d, fail=%d",
        total, pass_count, warn_count, fail_count,
    )

    return results

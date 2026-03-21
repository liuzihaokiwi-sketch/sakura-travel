"""
candidate_pool_precompute.py
T12: 候选池预计算脚本

给定 plan_id（或 --all 批量） → 为每个 slot 预计算 3-5 个候选 → 写入 candidate_pool_cache

用法:
    python -m app.workers.scripts.candidate_pool_precompute --plan-id <uuid>
    python -m app.workers.scripts.candidate_pool_precompute --all --city tokyo
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)

# 候选缓存有效期（天）
CACHE_TTL_DAYS = 7

# 每个 slot 预计算候选数
CANDIDATES_PER_SLOT = 5

# 通勤约束：替换实体距离原实体不超过 N km
MAX_DISTANCE_KM = 5.0


# ── 核心逻辑 ─────────────────────────────────────────────────────────────────

async def precompute_plan(plan_id: str, db: AsyncSession) -> dict:
    """
    为单个行程方案预计算候选池并写入缓存。
    返回 {plan_id, slots_processed, candidates_written, errors}
    """
    from app.db.models.catalog import ItineraryPlan, PlanSlot

    stats = {"plan_id": plan_id, "slots_processed": 0, "candidates_written": 0, "errors": []}

    # 1. 拉取方案所有 slots
    result = await db.execute(
        sa.text(
            """SELECT ps.slot_id, ps.day_number, ps.slot_index, ps.entity_id,
                      e.city_code, e.category, e.tags, e.geo_lat, e.geo_lng,
                      e.name_zh
               FROM plan_slots ps
               JOIN entities e ON e.entity_id = ps.entity_id
               WHERE ps.plan_id = :plan_id
               ORDER BY ps.day_number, ps.slot_index"""
        ),
        {"plan_id": plan_id},
    )
    slots = result.fetchall()

    if not slots:
        logger.warning(f"[T12] plan {plan_id} 没有 slots，跳过")
        return stats

    expires_at = datetime.utcnow() + timedelta(days=CACHE_TTL_DAYS)

    for slot in slots:
        (slot_id, day_number, slot_index, entity_id,
         city_code, category, tags, geo_lat, geo_lng, name_zh) = slot

        try:
            candidates = await _compute_candidates(
                db=db,
                source_entity_id=entity_id,
                city_code=city_code,
                category=category,
                tags=tags or [],
                geo_lat=geo_lat,
                geo_lng=geo_lng,
                limit=CANDIDATES_PER_SLOT,
            )

            if not candidates:
                stats["errors"].append(f"day{day_number}/slot{slot_index}: 无候选")
                continue

            # 检查或更新缓存
            existing = await db.execute(
                sa.text(
                    "SELECT id FROM candidate_pool_cache WHERE plan_id=:pid AND day_number=:dn AND slot_index=:si"
                ),
                {"pid": plan_id, "dn": day_number, "si": slot_index},
            )
            row = existing.fetchone()

            if row:
                await db.execute(
                    sa.text(
                        """UPDATE candidate_pool_cache
                           SET candidates=:candidates, source_entity_id=:eid,
                               computed_at=now(), expires_at=:exp
                           WHERE id=:id"""
                    ),
                    {
                        "id": row[0],
                        "candidates": json.dumps(candidates, ensure_ascii=False),
                        "eid": str(entity_id),
                        "exp": expires_at,
                    },
                )
            else:
                await db.execute(
                    sa.text(
                        """INSERT INTO candidate_pool_cache
                           (plan_id, day_number, slot_index, source_entity_id,
                            candidates, constraint_summary, expires_at)
                           VALUES (:plan_id, :dn, :si, :eid, :candidates, :constraint, :exp)"""
                    ),
                    {
                        "plan_id": plan_id,
                        "dn": day_number,
                        "si": slot_index,
                        "eid": str(entity_id),
                        "candidates": json.dumps(candidates, ensure_ascii=False),
                        "constraint": json.dumps(
                            {
                                "max_distance_km": MAX_DISTANCE_KM,
                                "category_locked": category,
                                "source_entity": name_zh,
                            },
                            ensure_ascii=False,
                        ),
                        "exp": expires_at,
                    },
                )

            stats["slots_processed"] += 1
            stats["candidates_written"] += len(candidates)
            logger.info(f"  ✓ day{day_number}/slot{slot_index} ({name_zh}) → {len(candidates)} 候选")

        except Exception as exc:
            err_msg = f"day{day_number}/slot{slot_index}: {exc}"
            stats["errors"].append(err_msg)
            logger.error(f"  ✗ {err_msg}")

    await db.commit()
    return stats


async def _compute_candidates(
    db: AsyncSession,
    source_entity_id: UUID,
    city_code: str,
    category: str,
    tags: list[str],
    geo_lat: Optional[float],
    geo_lng: Optional[float],
    limit: int = 5,
) -> list[dict]:
    """
    查询 entity_alternatives 或实时从 entities 表计算候选。
    优先级：entity_alternatives 预计算表 → 实时相似度查询
    """

    # 1. 先查预计算的 entity_alternatives 表
    precomputed = await db.execute(
        sa.text(
            """SELECT ea.alt_entity_id, ea.similarity_score, ea.swap_safe,
                      ea.distance_km, ea.reason_zh, ea.rank,
                      e.name_zh, e.address_zh, e.geo_lat, e.geo_lng,
                      e.google_rating, e.tabelog_score, e.cover_image_url
               FROM entity_alternatives ea
               JOIN entities e ON e.entity_id = ea.alt_entity_id
               WHERE ea.source_entity_id = :src
                 AND (ea.expires_at IS NULL OR ea.expires_at > now())
                 AND ea.swap_safe = true
               ORDER BY ea.rank
               LIMIT :limit"""
        ),
        {"src": str(source_entity_id), "limit": limit},
    )
    rows = precomputed.fetchall()

    if rows:
        return [
            {
                "entity_id": str(r[0]),
                "name_zh": r[6],
                "address_zh": r[7],
                "geo": {"lat": float(r[8]) if r[8] else None, "lng": float(r[9]) if r[9] else None},
                "similarity_score": float(r[1]),
                "swap_safe": r[2],
                "distance_km": float(r[4]) if r[4] else None,
                "reason_zh": r[4],
                "rank": r[5],
                "google_rating": float(r[10]) if r[10] else None,
                "tabelog_score": float(r[11]) if r[11] else None,
                "cover_image_url": r[12],
            }
            for r in rows
        ]

    # 2. Fallback: 实时从 entities 表按标签相似度查询
    if not (geo_lat and geo_lng):
        return []

    # 用 PostGIS 圆心距离过滤 + 标签交集排序
    fallback = await db.execute(
        sa.text(
            """SELECT e.entity_id, e.name_zh, e.address_zh, e.geo_lat, e.geo_lng,
                      e.google_rating, e.tabelog_score, e.cover_image_url, e.tags,
                      ST_Distance(
                          ST_MakePoint(e.geo_lng, e.geo_lat)::geography,
                          ST_MakePoint(:lng, :lat)::geography
                      ) / 1000.0 AS dist_km
               FROM entities e
               WHERE e.city_code = :city
                 AND e.category = :cat
                 AND e.entity_id != :src
                 AND e.is_active = true
                 AND ST_Distance(
                     ST_MakePoint(e.geo_lng, e.geo_lat)::geography,
                     ST_MakePoint(:lng, :lat)::geography
                 ) / 1000.0 <= :max_dist
               ORDER BY dist_km
               LIMIT :limit"""
        ),
        {
            "city": city_code,
            "cat": category,
            "src": str(source_entity_id),
            "lat": geo_lat,
            "lng": geo_lng,
            "max_dist": MAX_DISTANCE_KM,
            "limit": limit * 2,
        },
    )
    fallback_rows = fallback.fetchall()

    results = []
    source_tags_set = set(tags)
    for i, r in enumerate(fallback_rows[:limit]):
        entity_tags = set(r[8] or [])
        shared = source_tags_set & entity_tags
        similarity = len(shared) / max(len(source_tags_set | entity_tags), 1)
        results.append(
            {
                "entity_id": str(r[0]),
                "name_zh": r[1],
                "address_zh": r[2],
                "geo": {"lat": float(r[3]) if r[3] else None, "lng": float(r[4]) if r[4] else None},
                "similarity_score": round(similarity, 3),
                "swap_safe": True,  # 需后续约束校验
                "distance_km": round(float(r[9]), 2),
                "reason_zh": f"距原景点约{round(float(r[9]),1)}km，同类{category}，共享标签：{list(shared)[:3]}",
                "rank": i + 1,
                "google_rating": float(r[5]) if r[5] else None,
                "tabelog_score": float(r[6]) if r[6] else None,
                "cover_image_url": r[7],
            }
        )
    return results


# ── 批量入口 ─────────────────────────────────────────────────────────────────

async def run_precompute(plan_id: Optional[str] = None, city: Optional[str] = None) -> None:
    async with async_session_factory() as db:
        if plan_id:
            stats = await precompute_plan(plan_id, db)
            logger.info(f"[T12] 完成 plan={plan_id}: {stats}")
        else:
            # 批量：查询所有需要计算/更新的方案
            query = sa.text(
                """SELECT DISTINCT plan_id
                   FROM plan_slots ps
                   JOIN entities e ON e.entity_id = ps.entity_id
                   WHERE (:city IS NULL OR e.city_code = :city)
                     AND ps.plan_id NOT IN (
                         SELECT DISTINCT plan_id FROM candidate_pool_cache
                         WHERE expires_at > now()
                     )
                   LIMIT 100"""
            )
            async with async_session_factory() as db2:
                result = await db2.execute(query, {"city": city})
                plan_ids = [str(r[0]) for r in result.fetchall()]

            logger.info(f"[T12] 批量预计算 {len(plan_ids)} 个方案 (city={city})")
            for pid in plan_ids:
                async with async_session_factory() as db3:
                    stats = await precompute_plan(pid, db3)
                    logger.info(f"  plan={pid}: slots={stats['slots_processed']}, candidates={stats['candidates_written']}")


# ── CLI 入口 ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    parser = argparse.ArgumentParser(description="候选池预计算脚本 (T12)")
    parser.add_argument("--plan-id", help="指定方案 ID，优先于 --all")
    parser.add_argument("--all", action="store_true", help="批量计算所有未缓存方案")
    parser.add_argument("--city", help="配合 --all 使用，限定城市 (如 tokyo/osaka/kyoto)")
    args = parser.parse_args()

    if not args.plan_id and not args.all:
        parser.print_help()
        sys.exit(1)

    asyncio.run(run_precompute(plan_id=args.plan_id, city=args.city))

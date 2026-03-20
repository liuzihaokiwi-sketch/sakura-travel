"""
arq 批量评分 Job：score_entities

触发方式：
  - 数据采集后自动入队（由 data pipeline worker 调用）
  - 手动触发：await enqueue_job("score_entities", city_code="tokyo")

行为：
  1. 按 city_code（可选）+ entity_type（可选）查询 is_active=True 的 EntityBase
  2. 对每个实体从 ORM 关联表中提取 EntitySignals
  3. 调用 compute_base_score 计算分数
  4. 写入 entity_scores 表（UPSERT：同 entity_id + score_profile 覆盖）
  5. 返回处理统计摘要
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models.catalog import EntityBase, EntityEditorNote, Hotel, Poi, Restaurant, EntityTag
from app.db.models.derived import EntityScore
from app.db.session import AsyncSessionLocal
from app.domains.catalog.tagger import THEME_DIMENSIONS, get_entity_affinity
from app.domains.ranking.scorer import EntitySignals, ScoreResult, compute_base_score, compute_context_score

logger = logging.getLogger(__name__)

# 每批处理实体数量（避免大查询撑爆内存）
BATCH_SIZE = 100

# 默认评分 profiles（可扩展：family / couple / solo / culture ...）
DEFAULT_PROFILES = ["general"]


# ── 信号提取 ──────────────────────────────────────────────────────────────────

def _extract_signals_from_entity(
    entity: EntityBase,
    editorial_boost: int = 0,
) -> EntitySignals:
    """
    从 ORM 实体关联数据中提取 EntitySignals。
    需要 entity.poi / entity.hotel / entity.restaurant 已被 eager-load 或 lazy-load。
    """
    signals = EntitySignals(
        entity_type=entity.entity_type,
        data_tier=entity.data_tier or "B",
        updated_at=entity.updated_at,
        editorial_boost=editorial_boost,
    )

    if entity.entity_type == "poi" and entity.poi is not None:
        poi: Poi = entity.poi
        signals.google_rating = float(poi.google_rating) if poi.google_rating is not None else None
        signals.google_review_count = poi.google_review_count
        signals.has_opening_hours = bool(poi.opening_hours_json)
        signals.best_season = poi.best_season
        # crowd_level → homogeneity hint（high 意味着潜在同质化风险更高）
        signals.homogeneity_count = 3 if poi.crowd_level_typical == "high" else 0

    elif entity.entity_type == "hotel" and entity.hotel is not None:
        hotel: Hotel = entity.hotel
        signals.google_rating = float(hotel.google_rating) if hotel.google_rating is not None else None
        signals.booking_score = float(hotel.booking_score) if hotel.booking_score is not None else None
        signals.walking_distance_station_min = (
            entity.hotel.area_guide.walking_distance_station_min
            if entity.hotel.area_guide is not None
            else None
        )
        # 初步价值估算：有价格信息且星级存在则给中等分，否则默认 50
        if hotel.typical_price_min_jpy and hotel.star_rating:
            # 简单价值分：星级 × 20，再减去价格压力
            value_raw = min(100.0, float(hotel.star_rating) * 20.0)
            signals.value_for_money_score = value_raw
        # 设施覆盖度：amenities 列表长度 → 归一化（满分 = 10 项）
        amenities = hotel.amenities or []
        signals.amenity_coverage_score = min(100.0, len(amenities) * 10.0)
        # 家庭友好 → 加分信号（transport_convenience 默认 50，这里不覆盖）

    elif entity.entity_type == "restaurant" and entity.restaurant is not None:
        rest: Restaurant = entity.restaurant
        signals.google_rating = float(rest.tabelog_score) if rest.tabelog_score is not None else None
        # tabelog 5 分制，已放到 google_rating，scorer 内部 _platform_rating_norm 会统一处理
        signals.tabelog_score = float(rest.tabelog_score) if rest.tabelog_score is not None else None
        signals.has_opening_hours = bool(rest.opening_hours_json)
        # 预约可执行性：impossible → 差，easy → 好
        difficulty_map = {"easy": 90.0, "medium": 70.0, "hard": 40.0, "impossible": 10.0}
        signals.reservation_feasibility_score = difficulty_map.get(
            rest.reservation_difficulty or "medium", 70.0
        )
        signals.has_extreme_queue = rest.reservation_difficulty == "impossible"

    return signals


def _get_editorial_boost(entity: EntityBase) -> int:
    """
    从 entity.editor_notes 中取最新的 editorial_boost 类型记录。
    多条时取最近创建的，无记录时返回 0。
    有效期（valid_until）过期的记录跳过。
    """
    now = datetime.now(tz=timezone.utc)
    best_boost = 0
    latest_ts: datetime | None = None

    for note in (entity.editor_notes or []):
        if note.note_type != "editorial_boost":
            continue
        if note.boost_value is None:
            continue
        # 检查有效期
        if note.valid_until is not None:
            valid_until = note.valid_until
            if valid_until.tzinfo is None:
                valid_until = valid_until.replace(tzinfo=timezone.utc)
            if valid_until < now:
                continue
        if latest_ts is None or note.created_at > latest_ts:
            best_boost = note.boost_value
            latest_ts = note.created_at

    return best_boost


# ── 核心 Job ──────────────────────────────────────────────────────────────────

async def score_entities(
    ctx: dict,
    city_code: str | None = None,
    entity_type: str | None = None,
    score_profile: str = "general",
    batch_size: int = BATCH_SIZE,
) -> dict[str, Any]:
    """
    arq Job：批量计算实体评分并写入 entity_scores 表。

    Args:
        ctx: arq context（包含 redis、job_id 等）
        city_code: 按城市过滤（None = 全量）
        entity_type: 按类型过滤 poi/hotel/restaurant（None = 全部）
        score_profile: 评分 profile（默认 "general"）
        batch_size: 每批处理数量

    Returns:
        {
            "processed": int,
            "upserted": int,
            "skipped": int,
            "errors": int,
            "city_code": city_code,
            "entity_type": entity_type,
            "score_profile": score_profile,
        }
    """
    job_id = ctx.get("job_id", "manual")
    logger.info(
        "score_entities START | job_id=%s city=%s entity_type=%s profile=%s",
        job_id, city_code, entity_type, score_profile,
    )

    processed = 0
    upserted = 0
    skipped = 0
    errors = 0
    offset = 0

    while True:
        async with AsyncSessionLocal() as session:
            # ── 分批查询实体 ───────────────────────────────────────────────────
            stmt = (
                select(EntityBase)
                .where(EntityBase.is_active == True)  # noqa: E712
                .order_by(EntityBase.entity_id)
                .offset(offset)
                .limit(batch_size)
            )
            if city_code:
                stmt = stmt.where(EntityBase.city_code == city_code)
            if entity_type:
                stmt = stmt.where(EntityBase.entity_type == entity_type)

            result = await session.execute(stmt)
            entities = result.scalars().all()

            if not entities:
                break  # 全部处理完毕

            for entity in entities:
                processed += 1
                try:
                    # 手动加载关联（避免 lazy-load 在 async 下失效）
                    await session.refresh(entity, ["poi", "hotel", "restaurant", "editor_notes"])
                    if entity.entity_type == "hotel" and entity.hotel is not None:
                        await session.refresh(entity.hotel, ["area_guide"])

                    # 提取编辑 boost
                    boost = _get_editorial_boost(entity)

                    # 提取信号并计算 system_score（base_score）
                    signals = _extract_signals_from_entity(entity, editorial_boost=boost)
                    result_score: ScoreResult = compute_base_score(signals, score_profile=score_profile)

                    # 计算 context_score：从 entity_tags 获取 9 维亲和度，用均匀权重
                    entity_affinity = await get_entity_affinity(session, str(entity.entity_id))
                    uniform_weights = {k: 1.0 / len(THEME_DIMENSIONS) for k in THEME_DIMENSIONS}
                    context_score, context_breakdown = compute_context_score(
                        user_weights=uniform_weights,
                        entity_affinity=entity_affinity,
                    )

                    # 将 context_score 写入 breakdown（用于可解释性展示）
                    score_breakdown = dict(result_score.score_breakdown)
                    score_breakdown["context_score"] = round(context_score, 2)
                    score_breakdown["context_breakdown"] = context_breakdown

                    # UPSERT：先删同 entity_id + score_profile，再插入
                    await session.execute(
                        delete(EntityScore).where(
                            EntityScore.entity_id == entity.entity_id,
                            EntityScore.score_profile == score_profile,
                        )
                    )

                    score_row = EntityScore(
                        entity_id=entity.entity_id,
                        score_profile=result_score.score_profile,
                        base_score=result_score.base_score,
                        editorial_boost=result_score.editorial_boost,
                        final_score=result_score.final_score,
                        score_breakdown=score_breakdown,
                        computed_at=datetime.now(tz=timezone.utc),
                    )
                    session.add(score_row)
                    upserted += 1

                except Exception as exc:
                    logger.warning(
                        "score_entities ENTITY ERROR | entity_id=%s error=%s",
                        entity.entity_id, exc,
                    )
                    errors += 1

            await session.commit()

        offset += batch_size

    summary = {
        "processed": processed,
        "upserted": upserted,
        "skipped": skipped,
        "errors": errors,
        "city_code": city_code,
        "entity_type": entity_type,
        "score_profile": score_profile,
    }
    logger.info("score_entities DONE | %s", summary)
    return summary

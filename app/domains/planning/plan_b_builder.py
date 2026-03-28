"""
app/domains/planning/plan_b_builder.py

Plan B 备用方案生成器（D3）

规则：
  雨天替代（weather）：将户外景点替换为同区域室内场所
  体力不足替代（low_energy）：替换高强度景点为低强度版本
  满员/预约失败替代（booking_fail）：同区域同类型备选实体

替代规则优先级：
  1. 相同区域（area_name）
  2. 相同城市（city_code）
  3. entity_type 相同（或食物→食物，景点→景点）
  4. budget_tier 兼容
  5. 雨天替代：优先 indoor=True 或 poi_category IN (museum, indoor_attraction)

输出：list[PlanBOption]，写入 DaySection.plan_b
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 户外景点类别（雨天替代时被替换）
_OUTDOOR_CATEGORIES = frozenset([
    "park", "garden", "shrine", "temple", "castle",
    "waterfall", "lake", "scenic_spot", "beach",
])

# 室内替代类别（雨天优先）
_INDOOR_CATEGORIES = frozenset([
    "museum", "art_gallery", "aquarium", "shopping_mall",
    "indoor_market", "theater", "hot_spring",
])

# 体力消耗高的类别（体力不足时替换）
_HIGH_INTENSITY_CATEGORIES = frozenset([
    "mountain", "hiking", "theme_park", "cycling", "water_sport",
])


async def build_plan_b_for_day(
    session: Any,
    day_slots: list[Any],   # list[DaySlot]
    day_city_code: str,
    budget_level: str = "mid",
) -> list[dict]:
    """
    为某天的 slot 列表生成 Plan B 备用方案。

    Args:
        session: AsyncSession
        day_slots: 该天的 DaySlot 列表
        day_city_code: 该天主城市代码
        budget_level: 用户预算档次

    Returns:
        list of PlanBOption dicts
    """
    from sqlalchemy import select
    from app.db.models.catalog import EntityBase, Poi

    plan_b_options: list[dict] = []

    for slot in day_slots:
        if slot.kind not in ("poi", "activity"):
            continue
        if not slot.entity_id:
            continue

        ent = await session.get(EntityBase, slot.entity_id)
        if not ent:
            continue

        poi = await session.get(Poi, ent.entity_id) if ent.entity_type == "poi" else None
        category = (poi.poi_category or "") if poi else ""
        area = ent.area_name or ""

        # ── 雨天替代规则 ──────────────────────────────────────────────────────
        if category in _OUTDOOR_CATEGORIES or _is_weather_sensitive(ent, poi):
            indoor_alt = await _find_indoor_alternative(
                session, ent.entity_id, ent.city_code, area, budget_level
            )
            if indoor_alt:
                plan_b_options.append({
                    "trigger": "下雨",
                    "alternative": f"{slot.title}受天气影响，推荐改去{indoor_alt['name_zh']}（室内，同区域）",
                    "entity_ids": [slot.entity_id, str(indoor_alt["entity_id"])],
                    "original_entity_id": slot.entity_id,
                    "replacement_entity_id": str(indoor_alt["entity_id"]),
                })

        # ── 体力不足替代规则 ──────────────────────────────────────────────────
        if category in _HIGH_INTENSITY_CATEGORIES or _is_high_intensity(ent, poi):
            easy_alt = await _find_easy_alternative(
                session, ent.entity_id, ent.city_code, area, budget_level
            )
            if easy_alt:
                plan_b_options.append({
                    "trigger": "体力不足",
                    "alternative": f"改为{easy_alt['name_zh']}（节奏轻松，同区域步行可达）",
                    "entity_ids": [slot.entity_id, str(easy_alt["entity_id"])],
                    "original_entity_id": slot.entity_id,
                    "replacement_entity_id": str(easy_alt["entity_id"]),
                })

    return plan_b_options


def _is_weather_sensitive(ent: Any, poi: Any) -> bool:
    """判断实体是否受天气影响（从 risk_flags 中读取）。"""
    risk_flags = getattr(ent, "risk_flags", None) or []
    return "weather_sensitive" in risk_flags or "outdoor_only" in risk_flags


def _is_high_intensity(ent: Any, poi: Any) -> bool:
    """判断实体是否体力消耗高。"""
    risk_flags = getattr(ent, "risk_flags", None) or []
    if "high_physical_demand" in risk_flags:
        return True
    if poi:
        dur = poi.typical_duration_min or 0
        return dur > 180  # 超过3小时通常体力消耗较大
    return False


async def _find_indoor_alternative(
    session: Any,
    exclude_id: Any,
    city_code: str,
    area: str,
    budget_level: str,
) -> dict | None:
    """在同区域/城市内找室内替代景点。"""
    from sqlalchemy import select, text
    try:
        # 优先同区域室内
        result = await session.execute(
            text("""
                SELECT eb.entity_id, eb.name_zh, eb.area_name
                FROM entity_base eb
                JOIN pois p ON p.entity_id = eb.entity_id
                WHERE eb.city_code = :city_code
                  AND eb.entity_id != :exclude_id
                  AND eb.is_active = true
                  AND eb.quality_tier IN ('S', 'A', 'B')
                  AND p.poi_category IN ('museum', 'art_gallery', 'aquarium',
                                         'shopping_mall', 'indoor_market', 'theater')
                  AND (:area = '' OR eb.area_name = :area OR eb.area_name IS NULL)
                ORDER BY
                  CASE WHEN eb.area_name = :area THEN 0 ELSE 1 END,
                  eb.quality_tier
                LIMIT 1
            """),
            {"city_code": city_code, "exclude_id": exclude_id, "area": area or ""},
        )
        row = result.mappings().first()
        return dict(row) if row else None
    except Exception as e:
        logger.debug("室内替代查询失败: %s", e)
        return None


async def _find_easy_alternative(
    session: Any,
    exclude_id: Any,
    city_code: str,
    area: str,
    budget_level: str,
) -> dict | None:
    """在同区域/城市内找低强度替代景点。"""
    from sqlalchemy import text
    try:
        result = await session.execute(
            text("""
                SELECT eb.entity_id, eb.name_zh, eb.area_name
                FROM entity_base eb
                JOIN pois p ON p.entity_id = eb.entity_id
                WHERE eb.city_code = :city_code
                  AND eb.entity_id != :exclude_id
                  AND eb.is_active = true
                  AND eb.quality_tier IN ('S', 'A', 'B')
                  AND p.poi_category NOT IN ('mountain', 'hiking', 'theme_park',
                                              'cycling', 'water_sport')
                  AND (p.typical_duration_min IS NULL OR p.typical_duration_min <= 120)
                  AND (:area = '' OR eb.area_name = :area OR eb.area_name IS NULL)
                ORDER BY
                  CASE WHEN eb.area_name = :area THEN 0 ELSE 1 END,
                  eb.quality_tier
                LIMIT 1
            """),
            {"city_code": city_code, "exclude_id": exclude_id, "area": area or ""},
        )
        row = result.mappings().first()
        return dict(row) if row else None
    except Exception as e:
        logger.debug("低强度替代查询失败: %s", e)
        return None

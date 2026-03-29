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
    travel_date: str | None = None,
) -> list[dict]:
    """
    为某天的 slot 列表生成 Plan B 备用方案。

    Args:
        session: AsyncSession
        day_slots: 该天的 DaySlot 列表
        day_city_code: 该天主城市代码
        budget_level: 用户预算档次
        travel_date: 旅行日期 YYYY-MM-DD（可选，用于查天气快照）

    Returns:
        list of PlanBOption dicts
    """
    from sqlalchemy import select
    from app.db.models.catalog import EntityBase, Poi

    plan_b_options: list[dict] = []

    # 查询天气快照（有数据则用于触发雨天替代，无数据不影响）
    weather_is_rainy = False
    if travel_date and day_city_code:
        try:
            from app.db.models.snapshots import WeatherSnapshot
            ws_q = await session.execute(
                select(WeatherSnapshot).where(
                    WeatherSnapshot.city_code == day_city_code,
                    WeatherSnapshot.forecast_date == travel_date,
                ).order_by(WeatherSnapshot.fetched_at.desc()).limit(1)
            )
            ws = ws_q.scalar_one_or_none()
            if ws and ws.condition in ("rainy", "snowy"):
                weather_is_rainy = True
                logger.info("天气快照: %s %s condition=%s，触发全天雨天替代", day_city_code, travel_date, ws.condition)
        except Exception as _exc:
            logger.warning("weather snapshot lookup failed for %s %s: %s", day_city_code, travel_date, _exc)

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

        # ── 雨天替代规则（天气快照 or 户外类别 or risk_flags） ────────────────
        if weather_is_rainy or category in _OUTDOOR_CATEGORIES or _is_weather_sensitive(ent, poi):
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

        # ── 预约失败替代规则 ──────────────────────────────────────────────────
        if _needs_booking(ent, poi):
            booking_alt = await _find_booking_alternative(
                session, ent.entity_id, ent.entity_type,
                ent.city_code, area, category, budget_level
            )
            if booking_alt:
                plan_b_options.append({
                    "trigger": "预约失败",
                    "alternative": f"{slot.title}约不到，改去{booking_alt['name_zh']}（同类型，无需预约或更易约）",
                    "entity_ids": [slot.entity_id, str(booking_alt["entity_id"])],
                    "original_entity_id": slot.entity_id,
                    "replacement_entity_id": str(booking_alt["entity_id"]),
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


def _needs_booking(ent: Any, poi: Any) -> bool:
    """判断实体是否需要预约（预约失败时需要替代方案）。"""
    booking = getattr(ent, "booking_method", None) or ""
    if booking in ("online_advance", "phone", "impossible"):
        return True
    risk_flags = getattr(ent, "risk_flags", None) or []
    if "requires_reservation" in risk_flags:
        return True
    if poi and getattr(poi, "requires_advance_booking", False):
        return True
    return False


def _budget_compatible_tiers(budget_level: str) -> list[str]:
    """返回与用户预算兼容的 budget_tier 列表（允许同级或更低一级）。"""
    tiers_map = {
        "budget":  ["budget"],
        "mid":     ["budget", "mid"],
        "premium": ["mid", "premium"],
        "luxury":  ["mid", "premium", "luxury"],
    }
    return tiers_map.get(budget_level, ["budget", "mid", "premium"])


async def _find_booking_alternative(
    session: Any,
    exclude_id: Any,
    entity_type: str,
    city_code: str,
    area: str,
    category: str,
    budget_level: str,
) -> dict | None:
    """找一个同类型但不需要预约的替代，budget_tier 兼容。"""
    from sqlalchemy import text
    allowed_tiers = _budget_compatible_tiers(budget_level)
    try:
        # 对 POI：同类别优先，退而求其次同区域
        # 对 Restaurant：同城同区域，booking_method = walk_in 优先
        if entity_type == "restaurant":
            result = await session.execute(
                text("""
                    SELECT eb.entity_id, eb.name_zh, eb.area_name
                    FROM entity_base eb
                    JOIN restaurants r ON r.entity_id = eb.entity_id
                    WHERE eb.city_code = :city_code
                      AND eb.entity_id != :exclude_id
                      AND eb.is_active = true
                      AND eb.quality_tier IN ('S', 'A', 'B')
                      AND (r.requires_reservation = false
                           OR eb.booking_method = 'walk_in'
                           OR eb.booking_method IS NULL)
                      AND (:area = '' OR eb.area_name = :area OR eb.area_name IS NULL)
                      AND (eb.budget_tier IS NULL OR eb.budget_tier = ANY(:tiers))
                    ORDER BY
                      CASE WHEN eb.area_name = :area THEN 0 ELSE 1 END,
                      eb.quality_tier
                    LIMIT 1
                """),
                {"city_code": city_code, "exclude_id": exclude_id, "area": area or "",
                 "tiers": allowed_tiers},
            )
        else:
            result = await session.execute(
                text("""
                    SELECT eb.entity_id, eb.name_zh, eb.area_name
                    FROM entity_base eb
                    LEFT JOIN pois p ON p.entity_id = eb.entity_id
                    WHERE eb.city_code = :city_code
                      AND eb.entity_id != :exclude_id
                      AND eb.entity_type = :entity_type
                      AND eb.is_active = true
                      AND eb.quality_tier IN ('S', 'A', 'B')
                      AND (eb.booking_method IS NULL
                           OR eb.booking_method = 'walk_in')
                      AND (p.requires_advance_booking = false
                           OR p.requires_advance_booking IS NULL)
                      AND (:category = '' OR p.poi_category = :category OR p.poi_category IS NULL)
                      AND (:area = '' OR eb.area_name = :area OR eb.area_name IS NULL)
                      AND (eb.budget_tier IS NULL OR eb.budget_tier = ANY(:tiers))
                    ORDER BY
                      CASE WHEN eb.area_name = :area THEN 0 ELSE 1 END,
                      CASE WHEN p.poi_category = :category THEN 0 ELSE 1 END,
                      eb.quality_tier
                    LIMIT 1
                """),
                {
                    "city_code": city_code, "exclude_id": exclude_id,
                    "entity_type": entity_type, "area": area or "",
                    "category": category or "", "tiers": allowed_tiers,
                },
            )
        row = result.mappings().first()
        return dict(row) if row else None
    except Exception as e:
        logger.debug("预约替代查询失败: %s", e)
        return None


async def _find_indoor_alternative(
    session: Any,
    exclude_id: Any,
    city_code: str,
    area: str,
    budget_level: str,
) -> dict | None:
    """在同区域/城市内找室内替代景点，budget_tier 兼容。"""
    from sqlalchemy import text
    allowed_tiers = _budget_compatible_tiers(budget_level)
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
                  AND p.poi_category IN ('museum', 'art_gallery', 'aquarium',
                                         'shopping_mall', 'indoor_market', 'theater')
                  AND (:area = '' OR eb.area_name = :area OR eb.area_name IS NULL)
                  AND (eb.budget_tier IS NULL OR eb.budget_tier = ANY(:tiers))
                ORDER BY
                  CASE WHEN eb.area_name = :area THEN 0 ELSE 1 END,
                  eb.quality_tier
                LIMIT 1
            """),
            {"city_code": city_code, "exclude_id": exclude_id, "area": area or "",
             "tiers": allowed_tiers},
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
    """在同区域/城市内找低强度替代景点，budget_tier 兼容。"""
    from sqlalchemy import text
    allowed_tiers = _budget_compatible_tiers(budget_level)
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
                  AND (eb.budget_tier IS NULL OR eb.budget_tier = ANY(:tiers))
                ORDER BY
                  CASE WHEN eb.area_name = :area THEN 0 ELSE 1 END,
                  eb.quality_tier
                LIMIT 1
            """),
            {"city_code": city_code, "exclude_id": exclude_id, "area": area or "",
             "tiers": allowed_tiers},
        )
        row = result.mappings().first()
        return dict(row) if row else None
    except Exception as e:
        logger.debug("低强度替代查询失败: %s", e)
        return None

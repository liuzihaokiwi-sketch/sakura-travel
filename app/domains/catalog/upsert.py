from __future__ import annotations

"""
幂等写入工具：upsert_entity
所有数据采集脚本都通过此函数写入 entity_base 及子表，保证不重复插入。
"""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase, Hotel, Poi, Restaurant


# ── 支持的子表映射 ─────────────────────────────────────────────────────────────
_SUBTYPE_MODEL = {
    "poi": Poi,
    "hotel": Hotel,
    "restaurant": Restaurant,
}

# entity_base 字段白名单（防止传入脏 key）
_BASE_FIELDS = {
    "name_zh", "name_ja", "name_en",
    "city_code", "prefecture", "area_name",
    "address_ja", "address_en", "lat", "lng",
    "data_tier", "is_active",
    "google_place_id", "tabelog_id",
}

# 各子表字段白名单
_POI_FIELDS = {
    "poi_category", "sub_category", "typical_duration_min",
    "opening_hours_json", "admission_fee_jpy", "admission_free",
    "best_season", "crowd_level_typical", "requires_advance_booking",
    "google_rating", "google_review_count",
}

_HOTEL_FIELDS = {
    "hotel_type", "star_rating", "chain_name",
    "room_count", "check_in_time", "check_out_time",
    "amenities", "is_family_friendly", "is_pet_friendly",
    "price_tier", "typical_price_min_jpy",
    "booking_hotel_id", "agoda_hotel_id",
    "google_rating", "booking_score",
}

_RESTAURANT_FIELDS = {
    "cuisine_type", "sub_cuisine", "michelin_star", "tabelog_score",
    "opening_hours_json", "seating_count",
    "requires_reservation", "reservation_difficulty",
    "price_range_min_jpy", "price_range_max_jpy",
    "budget_lunch_jpy", "budget_dinner_jpy",
    "has_english_menu", "is_vegetarian_friendly", "is_halal",
}

_SUBTYPE_FIELDS: Dict[str, set] = {
    "poi": _POI_FIELDS,
    "hotel": _HOTEL_FIELDS,
    "restaurant": _RESTAURANT_FIELDS,
}


def _filter(data: Dict[str, Any], allowed: set) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if k in allowed}


def _sanitize_subtype_data(entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(data)

    # AI 生成有时会把单值枚举字段返回成 list，这里收敛成单值，避免写库失败。
    if entity_type == "poi":
        best_season = cleaned.get("best_season")
        if isinstance(best_season, list):
            cleaned["best_season"] = next((x for x in best_season if x), None)

    return cleaned


async def upsert_entity(
    session: AsyncSession,
    entity_type: str,
    data: Dict[str, Any],
    google_place_id: Optional[str] = None,
    tabelog_id: Optional[str] = None,
) -> EntityBase:
    """
    幂等写入 entity_base + 子表。

    匹配优先级：
      1. google_place_id（唯一索引）
      2. tabelog_id + entity_type
      3. 均无则新建

    Args:
        session:         AsyncSession（调用方不需要 commit，此函数会 flush）
        entity_type:     "poi" | "hotel" | "restaurant"
        data:            字段字典，base 字段与子表字段混在一起传入即可
        google_place_id: 可覆盖 data 中的值
        tabelog_id:      可覆盖 data 中的值

    Returns:
        已 flush 的 EntityBase 实例
    """
    if entity_type not in _SUBTYPE_MODEL:
        raise ValueError(f"Unsupported entity_type: {entity_type!r}")

    # 允许从 data 里读，也允许参数覆盖
    gid = google_place_id or data.get("google_place_id")
    tid = tabelog_id or data.get("tabelog_id")

    entity: Optional[EntityBase] = None

    # ── 1. 按 google_place_id 查找 ────────────────────────────────────────────
    if gid:
        result = await session.execute(
            select(EntityBase).where(EntityBase.google_place_id == gid)
        )
        entity = result.scalar_one_or_none()

    # ── 2. 按 tabelog_id + type 查找 ──────────────────────────────────────────
    if entity is None and tid:
        result = await session.execute(
            select(EntityBase).where(
                EntityBase.tabelog_id == tid,
                EntityBase.entity_type == entity_type,
            )
        )
        entity = result.scalar_one_or_none()

    base_data = _filter(data, _BASE_FIELDS)
    if gid:
        base_data["google_place_id"] = gid
    if tid:
        base_data["tabelog_id"] = tid

    # ── 3. 创建或更新 entity_base ─────────────────────────────────────────────
    if entity is None:
        entity = EntityBase(
            entity_type=entity_type,
            **base_data,
        )
        session.add(entity)
        await session.flush()  # 获取 entity_id
        is_new = True
    else:
        for k, v in base_data.items():
            setattr(entity, k, v)
        is_new = False

    # ── 4. 创建或更新子表 ─────────────────────────────────────────────────────
    SubModel = _SUBTYPE_MODEL[entity_type]
    sub_data = _sanitize_subtype_data(entity_type, _filter(data, _SUBTYPE_FIELDS[entity_type]))

    if is_new:
        sub = SubModel(entity_id=entity.entity_id, **sub_data)
        session.add(sub)
    else:
        result = await session.execute(
            select(SubModel).where(SubModel.entity_id == entity.entity_id)
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            sub = SubModel(entity_id=entity.entity_id, **sub_data)
            session.add(sub)
        else:
            for k, v in sub_data.items():
                setattr(sub, k, v)

    await session.flush()
    return entity

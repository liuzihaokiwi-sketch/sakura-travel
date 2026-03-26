"""
secondary_filler.py — S2: 次要活动填充器

输入：
  - frames: list[DayFrame]         来自 route_skeleton_builder
  - candidate_pool: list[dict]     来自 candidate_pool_precompute 或实时查询
  - trip_profile: dict             TripProfile 字段

输出：
  - list[dict]  每天已填充次要活动的 day_dict（含 items 列表）

规则：
  1. 每天容量 = frame.day_capacity_units（1.0 = 一天满载）
  2. 主活动（main_driver）已占用 0.6 单位，每个次要活动占 0.25 单位
  3. 优先选 same_corridor 的实体，其次 fallback_corridor
  4. 过滤已在 must_keep_ids 或 cut_order 中的实体（避免重复）
  5. 按 final_score DESC 排序，选满容量
  6. 凡标记 requires_advance_booking 的，追加到 booking_alerts

E5 改造: 接入 CorridorResolver 做标准化 corridor 匹配（替代原字符串包含判断）。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.domains.planning.corridor_resolver import CorridorResolver

logger = logging.getLogger(__name__)

# 容量常量
MAIN_DRIVER_CAPACITY = 0.6      # 主活动占用
SECONDARY_UNIT_CAPACITY = 0.25  # 每个次要活动占用
MIN_SECONDARY = 1               # 每天至少插入 1 个次要活动
MAX_SECONDARY = 3               # 每天最多 3 个次要活动（避免过满）


@dataclass
class FilledDay:
    """单天填充结果"""
    day_index: int
    primary_corridor: str
    secondary_corridor: Optional[str]
    main_driver_id: Optional[str]       # cluster_id
    secondary_items: list[dict] = field(default_factory=list)
    booking_alerts: list[dict] = field(default_factory=list)
    remaining_capacity: float = 0.0


def _score_entity(
    entity: dict,
    corridor: str,
    fallback_corridor: Optional[str],
    resolver: Optional["CorridorResolver"] = None,
) -> float:
    """给候选实体打调度优先级分（不是最终分）。

    E5: 优先用 CorridorResolver 做标准化走廊匹配。
    如果没有 resolver（向后兼容），降级为字符串包含判断。

    逻辑：
      base = entity.final_score (0-100)
      + 20 if 在主走廊（or 相邻走廊 +12）
      + 10 if 在副走廊
      - 15 if data_tier == "B"
    """
    base = float(entity.get("final_score") or entity.get("base_score") or 50.0)

    # E5: corridor 匹配
    corridor_bonus = 0.0
    entity_area = entity.get("area_name", "") or ""
    entity_corridor_tags = entity.get("corridor_tags") or []

    if resolver and corridor:
        # 标准化解析：实体的 corridor_tags 或 area_name → corridor_ids
        entity_corridors = set(entity_corridor_tags)
        if not entity_corridors and entity_area:
            entity_corridors = set(resolver.resolve(entity_area))

        # primary corridor 解析
        primary_ids = set(resolver.resolve(corridor))

        if entity_corridors & primary_ids:
            corridor_bonus = 20.0
        elif any(
            resolver.is_same_or_adjacent(ec, pc)
            for ec in entity_corridors for pc in primary_ids
        ):
            corridor_bonus = 12.0  # 相邻走廊
        elif fallback_corridor:
            fallback_ids = set(resolver.resolve(fallback_corridor))
            if entity_corridors & fallback_ids:
                corridor_bonus = 10.0
    else:
        # 向后兼容: 字符串包含
        if corridor and entity_area and corridor.lower() in entity_area.lower():
            corridor_bonus = 20.0
        elif fallback_corridor and entity_area and fallback_corridor.lower() in entity_area.lower():
            corridor_bonus = 10.0

    base += corridor_bonus

    if entity.get("data_tier") == "B":
        base -= 15
    return base


def _entity_already_used(entity: dict, used_ids: set[str]) -> bool:
    eid = str(entity.get("entity_id") or "")
    name = entity.get("name_zh", "") or entity.get("name", "") or ""
    return eid in used_ids or name in used_ids


def fill_secondary_activities(
    frames: list,
    candidate_pool: list[dict],
    trip_profile: dict,
    already_used_ids: Optional[set[str]] = None,
    corridor_resolver: Optional["CorridorResolver"] = None,
    override_resolver: Optional["OverrideResolver"] = None,
    constraints=None,
) -> list[FilledDay]:
    """
    核心入口：为每天的骨架插入次要活动。

    Args:
        frames:             DayFrame 列表（来自 route_skeleton_builder）
        candidate_pool:     实体候选池，每项至少含 entity_id, entity_type,
                            area_name, final_score, name_zh, data_tier 字段
        trip_profile:       TripProfile dict（用于 avoid_list 过滤）
        already_used_ids:   跨天已用实体 ID 集合（防重复）
        override_resolver:  运营干预解析器，用于过滤 block 实体（L4-02）

    Returns:
        list[FilledDay]
    """
    used_ids: set[str] = already_used_ids or set()
    avoid_list: set[str] = set(trip_profile.get("avoid_list", []))

    # 从 constraints 补充 blocked_tags 到 avoid_list（如有）
    _blocked_tags: set[str] = set()
    if constraints is not None:
        _blocked_tags = getattr(constraints, "blocked_tags", set()) or set()

    # L4-02: 从 OverrideResolver 获取被 block 的实体 ID 集合
    operator_blocked: set[str] = set()
    if override_resolver is not None:
        try:
            operator_blocked = override_resolver.get_all_blocked_entity_ids()
        except Exception:
            pass

    # 只选 POI 类型作为次要活动（餐厅由 meal_flex_filler 单独处理）
    poi_pool = [
        e for e in candidate_pool
        if e.get("entity_type") in ("poi", None)
        and e.get("is_active", True)
        and e.get("entity_id", "") not in operator_blocked   # L4-02: 过滤 block 实体
    ]

    results: list[FilledDay] = []

    for frame in frames:
        # 兼容 dataclass 和 dict
        day_idx = frame.day_index if hasattr(frame, "day_index") else frame["day_index"]
        corridor = frame.primary_corridor if hasattr(frame, "primary_corridor") else frame.get("primary_corridor", "")
        fallback = frame.fallback_corridor if hasattr(frame, "fallback_corridor") else frame.get("fallback_corridor")
        capacity = frame.day_capacity_units if hasattr(frame, "day_capacity_units") else frame.get("day_capacity_units", 1.0)
        must_keep = set(frame.must_keep_ids if hasattr(frame, "must_keep_ids") else frame.get("must_keep_ids", []))
        cut_order = set(frame.cut_order if hasattr(frame, "cut_order") else frame.get("cut_order", []))
        main_driver = frame.main_driver if hasattr(frame, "main_driver") else frame.get("main_driver")
        day_type = frame.day_type if hasattr(frame, "day_type") else frame.get("day_type", "normal")

        # 到达/离开日容量收缩，不加次要活动
        if day_type in ("arrival", "departure"):
            results.append(FilledDay(
                day_index=day_idx,
                primary_corridor=corridor,
                secondary_corridor=fallback,
                main_driver_id=main_driver,
                remaining_capacity=capacity,
            ))
            continue

        # 已用容量 = 主活动
        used_capacity = MAIN_DRIVER_CAPACITY if main_driver else 0.0
        remaining = capacity - used_capacity

        # 候选过滤
        candidates = []
        for ent in poi_pool:
            eid = str(ent.get("entity_id") or "")
            name = ent.get("name_zh", "") or ent.get("name", "") or ""
            # 跳过：已使用、主活动 must_keep、回避列表、名称含避坑词
            if _entity_already_used(ent, used_ids):
                continue
            if eid in must_keep or eid in cut_order:
                continue
            if name in avoid_list or any(av in name for av in avoid_list):
                continue
            # constraints.blocked_tags: 检查实体的 sub_category / corridor_tags
            if _blocked_tags:
                ent_tags = set(ent.get("corridor_tags") or [])
                sub_cat = ent.get("sub_category") or ""
                if sub_cat:
                    ent_tags.add(sub_cat.lower())
                if ent_tags & _blocked_tags:
                    continue
            score = _score_entity(ent, corridor, fallback, corridor_resolver)
            candidates.append((score, ent))

        # 按调度分排序
        candidates.sort(key=lambda x: x[0], reverse=True)

        filled_items = []
        booking_alerts = []
        count = 0

        for score, ent in candidates:
            if count >= MAX_SECONDARY:
                break
            if remaining < SECONDARY_UNIT_CAPACITY:
                break

            filled_items.append({
                "entity_id": str(ent.get("entity_id") or ""),
                "name": ent.get("name_zh") or ent.get("name", ""),
                "entity_type": ent.get("entity_type", "poi"),
                "area_name": ent.get("area_name", ""),
                "data_tier": ent.get("data_tier", "B"),
                "final_score": score,
                "duration_min": ent.get("typical_duration_min", 90),
                "is_optional": True,
                "source": "secondary_filler",
            })

            if ent.get("requires_advance_booking"):
                booking_alerts.append({
                    "entity_id": str(ent.get("entity_id") or ""),
                    "label": ent.get("name_zh") or ent.get("name", ""),
                    "booking_level": "should_book",
                    "deadline_hint": "建议提前 3-7 天预约",
                })

            used_ids.add(str(ent.get("entity_id") or ""))
            remaining -= SECONDARY_UNIT_CAPACITY
            count += 1

        # 如果完全没填到，降低标准再试一次（忽略走廊限制）
        if not filled_items and candidates:
            best_score, best_ent = candidates[0]
            filled_items.append({
                "entity_id": str(best_ent.get("entity_id") or ""),
                "name": best_ent.get("name_zh") or best_ent.get("name", ""),
                "entity_type": best_ent.get("entity_type", "poi"),
                "area_name": best_ent.get("area_name", ""),
                "data_tier": best_ent.get("data_tier", "B"),
                "final_score": best_score,
                "duration_min": best_ent.get("typical_duration_min", 90),
                "is_optional": True,
                "source": "secondary_filler_fallback",
            })
            used_ids.add(str(best_ent.get("entity_id") or ""))
            remaining -= SECONDARY_UNIT_CAPACITY

        results.append(FilledDay(
            day_index=day_idx,
            primary_corridor=corridor,
            secondary_corridor=fallback,
            main_driver_id=main_driver,
            secondary_items=filled_items,
            booking_alerts=booking_alerts,
            remaining_capacity=max(0.0, remaining),
        ))

        logger.debug(
            "Day %d: filled %d secondary items (corridor=%s, remaining_cap=%.2f)",
            day_idx, len(filled_items), corridor, remaining,
        )

    return results


def merge_into_day_dicts(
    day_dicts: list[dict],
    filled_days: list[FilledDay],
) -> list[dict]:
    """
    将 FilledDay 的次要活动合并回 day_dicts（in-place 追加到 items）。

    Args:
        day_dicts:    原始 day_dict 列表（来自 _collect_plan_data）
        filled_days:  fill_secondary_activities 的输出

    Returns:
        合并后的 day_dicts（同一列表，已 in-place 修改）
    """
    filled_map = {fd.day_index: fd for fd in filled_days}

    for dd in day_dicts:
        day_idx = dd.get("day_number") or dd.get("day_index", 0)
        fd = filled_map.get(day_idx)
        if not fd:
            continue
        existing = dd.setdefault("items", [])
        existing.extend(fd.secondary_items)
        # 追加预约提醒
        alerts = dd.setdefault("booking_alerts", [])
        alerts.extend(fd.booking_alerts)

    return day_dicts

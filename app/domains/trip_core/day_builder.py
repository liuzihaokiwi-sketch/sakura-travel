from __future__ import annotations

"""
day_builder: 把候选实体列表组装成一天的 ItineraryItem 列表。

时间槽分配：
  09:00  上午景点 1（poi）
  10:45  上午景点 2（可选，相距 <8km）
  12:00  午餐（restaurant）
  14:00  下午景点（poi）
  17:00  自由活动（optional）
  18:30  晚餐（restaurant）
  20:30  酒店 check-in（hotel）
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ── 数据结构（纯 Python，不依赖 ORM） ────────────────────────────────────────

@dataclass
class EntityCandidate:
    """规划时用的候选实体（从 DB 查出后映射）"""
    entity_id: str
    entity_type: str
    name_zh: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    poi_category: Optional[str] = None
    cuisine_type: Optional[str] = None
    typical_duration_min: Optional[int] = None
    admission_fee_jpy: Optional[int] = None
    budget_lunch_jpy: Optional[int] = None
    budget_dinner_jpy: Optional[int] = None
    google_rating: Optional[float] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class PlannedItem:
    """组装好的行程条目（写入 ItineraryItem 前的中间结构）"""
    sort_order: int
    item_type: str
    entity_id: Optional[str]
    start_time: str
    end_time: str
    duration_min: int
    notes_zh: Optional[str] = None
    estimated_cost_jpy: Optional[int] = None
    is_optional: bool = False


# ── 时间槽定义 ─────────────────────────────────────────────────────────────────
_SLOTS: List[Tuple[str, str, int, str, bool]] = [
    ("morning_poi_1", "09:00", 90,  "poi",        False),
    ("morning_poi_2", "10:45", 60,  "poi",        True),
    ("lunch",         "12:00", 60,  "restaurant", False),
    ("afternoon_poi", "14:00", 120, "poi",        False),
    ("free_time",     "17:00", 60,  "free_time",  True),
    ("dinner",        "18:30", 90,  "restaurant", False),
    ("hotel",         "20:30", 30,  "hotel",      False),
]


def _add_minutes(time_str: str, minutes: int) -> str:
    h, m = map(int, time_str.split(":"))
    total = h * 60 + m + minutes
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _distance_km(a: EntityCandidate, b: EntityCandidate) -> float:
    if a.lat and a.lng and b.lat and b.lng:
        return _haversine_km(a.lat, a.lng, b.lat, b.lng)
    return 999.0


def _poi_note(c: EntityCandidate) -> str:
    parts = [c.name_zh]
    if c.poi_category:
        cat_zh = {
            "shrine": "神社", "temple": "寺院", "park": "公园",
            "museum": "博物馆", "castle": "城堡", "landmark": "地标",
            "shopping": "购物", "onsen": "温泉", "theme_park": "主题乐园",
        }.get(c.poi_category, c.poi_category)
        parts.append(f"[{cat_zh}]")
    if c.google_rating:
        parts.append(f"⭐{c.google_rating}")
    return "  ".join(parts)


def build_day(
    pois: List[EntityCandidate],
    restaurants: List[EntityCandidate],
    hotel: Optional[EntityCandidate] = None,
    max_poi_distance_km: float = 8.0,
) -> List[PlannedItem]:
    """
    把候选实体组装成一天的行程。

    Args:
        pois:                按 final_score DESC 排序的 POI 列表
        restaurants:         按 final_score DESC 排序的餐厅列表
        hotel:               当天住宿酒店（可 None）
        max_poi_distance_km: 上午两个 POI 的最大允许距离

    Returns:
        PlannedItem 列表
    """
    items: List[PlannedItem] = []
    poi_queue = list(pois)
    rest_queue = list(restaurants)
    sort_order = 0
    last_poi: Optional[EntityCandidate] = None

    for slot_name, start_time, default_dur, item_type, is_optional in _SLOTS:

        if item_type == "free_time":
            items.append(PlannedItem(
                sort_order=sort_order, item_type="free_time", entity_id=None,
                start_time=start_time, end_time=_add_minutes(start_time, default_dur),
                duration_min=default_dur, notes_zh="自由活动 / 购物", is_optional=True,
            ))
            sort_order += 1
            continue

        if item_type == "hotel":
            if hotel:
                items.append(PlannedItem(
                    sort_order=sort_order, item_type="hotel",
                    entity_id=hotel.entity_id,
                    start_time=start_time, end_time=_add_minutes(start_time, 30),
                    duration_min=30, notes_zh=f"入住 {hotel.name_zh}",
                ))
                sort_order += 1
            continue

        if item_type == "poi":
            if not poi_queue:
                continue
            candidate = poi_queue[0]
            # morning_poi_2：距离过远则跳过
            if slot_name == "morning_poi_2" and last_poi:
                if _distance_km(last_poi, candidate) > max_poi_distance_km:
                    continue
            poi_queue.pop(0)
            dur = candidate.typical_duration_min or default_dur
            items.append(PlannedItem(
                sort_order=sort_order, item_type="poi",
                entity_id=candidate.entity_id,
                start_time=start_time, end_time=_add_minutes(start_time, dur),
                duration_min=dur, notes_zh=_poi_note(candidate),
                estimated_cost_jpy=candidate.admission_fee_jpy,
                is_optional=is_optional,
            ))
            last_poi = candidate
            sort_order += 1
            continue

        if item_type == "restaurant":
            is_lunch = "lunch" in slot_name
            meal_label = "午餐" if is_lunch else "晚餐"
            if not rest_queue:
                items.append(PlannedItem(
                    sort_order=sort_order, item_type="note", entity_id=None,
                    start_time=start_time, end_time=_add_minutes(start_time, 60),
                    duration_min=60, notes_zh=f"{meal_label}（自行安排）",
                ))
                sort_order += 1
                continue
            rest = rest_queue.pop(0)
            cost = rest.budget_lunch_jpy if is_lunch else rest.budget_dinner_jpy
            items.append(PlannedItem(
                sort_order=sort_order, item_type="restaurant",
                entity_id=rest.entity_id,
                start_time=start_time, end_time=_add_minutes(start_time, 60),
                duration_min=60,
                notes_zh=f"{meal_label}：{rest.name_zh}"
                         + (f"（{rest.cuisine_type}）" if rest.cuisine_type else ""),
                estimated_cost_jpy=cost,
            ))
            sort_order += 1

    return items


def estimate_day_cost_jpy(items: List[PlannedItem]) -> int:
    return sum(i.estimated_cost_jpy for i in items if i.estimated_cost_jpy)

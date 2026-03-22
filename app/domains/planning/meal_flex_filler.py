"""
meal_flex_filler.py — S3: 弹性餐厅填充器

输入：
  - frames: list[DayFrame]       来自 route_skeleton_builder（含 meal_windows）
  - restaurant_pool: list[dict]  候选餐厅（entity_type=restaurant）
  - trip_profile: dict           TripProfile 字段（budget, avoid_list, party_type）

输出：
  - list[MealFillResult]  每天的餐厅填充结果

规则：
  1. 每天按 meal_windows（breakfast / lunch / dinner）各最多填 1 家
  2. lunch 优先选与 primary_corridor 一致的 route_meal 风格
  3. dinner 优先选 destination_meal（目的地餐厅），评分高于 4.0 的
  4. 有 michelin_star 的餐厅只在 dinner 推荐
  5. requires_reservation=True 的餐厅追加 booking_alert（must_book）
  6. budget 过滤：budget 用户跳过 price_range_min_jpy > 5000 的餐厅
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# 预算门槛（日元/人）
BUDGET_PRICE_MAX = 5_000        # budget 用户的餐厅人均上限
MID_PRICE_MAX = 15_000          # mid 用户的餐厅人均上限
HIGH_RATING_THRESHOLD = 4.0     # dinner 优先选高评分

# 餐食风格 → 适合时间段
MEAL_STYLE_TIMING = {
    "quick": ["breakfast", "lunch"],
    "route_meal": ["lunch"],
    "destination_meal": ["lunch", "dinner"],
}


@dataclass
class MealSlot:
    meal_type: str          # breakfast / lunch / dinner
    restaurant: dict        # 填充的餐厅实体
    style: str = ""         # quick / route_meal / destination_meal
    booking_required: bool = False


@dataclass
class MealFillResult:
    """单天餐厅填充结果"""
    day_index: int
    meals: list[MealSlot] = field(default_factory=list)
    booking_alerts: list[dict] = field(default_factory=list)
    unfilled_slots: list[str] = field(default_factory=list)  # 未能填充的 meal_type


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _budget_level(trip_profile: dict) -> str:
    """标准化预算等级"""
    raw = trip_profile.get("budget_level") or trip_profile.get("budget_bias") or "mid"
    raw = raw.lower()
    if "budget" in raw or "economy" in raw or "经济" in raw:
        return "budget"
    if "premium" in raw or "luxury" in raw or "高" in raw:
        return "premium"
    return "mid"


def _price_ok(restaurant: dict, budget: str) -> bool:
    """根据预算过滤价格"""
    min_price = restaurant.get("price_range_min_jpy") or 0
    if budget == "budget" and min_price > BUDGET_PRICE_MAX:
        return False
    if budget == "mid" and min_price > MID_PRICE_MAX:
        return False
    return True


def _cuisine_ok(restaurant: dict, avoid_list: set[str]) -> bool:
    """检查菜系是否在避免列表里"""
    cuisine = restaurant.get("cuisine_type", "") or ""
    name = restaurant.get("name_zh", "") or restaurant.get("name", "") or ""
    for av in avoid_list:
        if av in cuisine or av in name:
            return False
    return True


def _is_breakfast_suitable(restaurant: dict) -> bool:
    cuisine = (restaurant.get("cuisine_type") or "").lower()
    name = (restaurant.get("name_zh") or restaurant.get("name") or "").lower()
    keywords = ("咖啡", "早餐", "breakfast", "cafe", "bakery", "パン", "コーヒー")
    return any(kw in cuisine or kw in name for kw in keywords)


def _is_michelin(restaurant: dict) -> bool:
    return bool(restaurant.get("michelin_star") and restaurant.get("michelin_star", 0) >= 1)


def _score_restaurant(
    restaurant: dict,
    meal_type: str,
    corridor: str,
    resolver=None,
) -> float:
    """餐厅调度评分。E5: 支持 CorridorResolver。"""
    base = float(restaurant.get("final_score") or restaurant.get("tabelog_score", 3.5) or 50.0)
    # tabelog 分是 0-5 制，换算到 0-100
    if base <= 5.0:
        base = base * 20.0

    area = (restaurant.get("area_name") or "").lower()
    corridor_tags = restaurant.get("corridor_tags") or []

    if resolver and corridor:
        entity_corridors = set(corridor_tags)
        if not entity_corridors and area:
            entity_corridors = set(resolver.resolve(area))
        primary_ids = set(resolver.resolve(corridor))
        if entity_corridors & primary_ids:
            base += 15
        elif any(resolver.is_same_or_adjacent(ec, pc) for ec in entity_corridors for pc in primary_ids):
            base += 8
    elif corridor and corridor.lower() in area:
        base += 15    # 同走廊加分（向后兼容）

    if meal_type == "dinner":
        if _is_michelin(restaurant):
            base += 25
        r = restaurant.get("google_rating") or restaurant.get("tabelog_score", 0) or 0
        if float(r) >= HIGH_RATING_THRESHOLD:
            base += 10

    if restaurant.get("data_tier") == "S":
        base += 10
    elif restaurant.get("data_tier") == "B":
        base -= 10

    return base


# ── 核心入口 ──────────────────────────────────────────────────────────────────

def fill_meals(
    frames: list,
    restaurant_pool: list[dict],
    trip_profile: dict,
    already_used_ids: Optional[set[str]] = None,
    corridor_resolver=None,
) -> list[MealFillResult]:
    """
    为每天的骨架填充餐厅。

    Args:
        frames:            DayFrame 列表
        restaurant_pool:   候选餐厅列表，每项含 entity_id, name_zh,
                           cuisine_type, price_range_min_jpy, michelin_star,
                           tabelog_score, google_rating, requires_reservation,
                           area_name, data_tier 等字段
        trip_profile:      TripProfile dict
        already_used_ids:  跨天已用餐厅 ID（防重复）

    Returns:
        list[MealFillResult]
    """
    used_ids: set[str] = already_used_ids or set()
    avoid_list: set[str] = set(trip_profile.get("avoid_list", []))
    budget = _budget_level(trip_profile)
    party_type = trip_profile.get("party_type", "couple")

    # 过滤餐厅池：只要 restaurant 类型
    rest_pool = [
        r for r in restaurant_pool
        if r.get("entity_type") == "restaurant"
        and r.get("is_active", True)
        and _price_ok(r, budget)
        and _cuisine_ok(r, avoid_list)
    ]

    results: list[MealFillResult] = []

    for frame in frames:
        day_idx = frame.day_index if hasattr(frame, "day_index") else frame["day_index"]
        corridor = frame.primary_corridor if hasattr(frame, "primary_corridor") else frame.get("primary_corridor", "")
        day_type = frame.day_type if hasattr(frame, "day_type") else frame.get("day_type", "normal")
        meal_windows = frame.meal_windows if hasattr(frame, "meal_windows") else frame.get("meal_windows", [])

        # 确定今日需要填充的餐次
        if not meal_windows:
            # 无窗口定义时用默认值
            meal_types_needed = ["lunch", "dinner"]
            if day_type == "arrival":
                meal_types_needed = ["dinner"]
            elif day_type == "departure":
                meal_types_needed = ["breakfast", "lunch"]
        else:
            meal_types_needed = [
                (mw.meal_type if hasattr(mw, "meal_type") else mw.get("meal_type", ""))
                for mw in meal_windows
            ]

        meals: list[MealSlot] = []
        booking_alerts: list[dict] = []
        unfilled: list[str] = []

        for meal_type in meal_types_needed:
            # 过滤适合该餐次的餐厅
            candidates = []
            for r in rest_pool:
                eid = str(r.get("entity_id") or "")
                if eid in used_ids:
                    continue
                # 早餐特殊过滤
                if meal_type == "breakfast" and not _is_breakfast_suitable(r):
                    continue
                # 米其林仅推荐 dinner
                if _is_michelin(r) and meal_type != "dinner":
                    continue
                score = _score_restaurant(r, meal_type, corridor, corridor_resolver)
                candidates.append((score, r))

            candidates.sort(key=lambda x: x[0], reverse=True)

            if not candidates:
                unfilled.append(meal_type)
                logger.debug("Day %d: no candidate for %s", day_idx, meal_type)
                continue

            best_score, best_r = candidates[0]
            style = "destination_meal" if meal_type == "dinner" else "route_meal"
            if meal_type == "breakfast":
                style = "quick"

            slot = MealSlot(
                meal_type=meal_type,
                restaurant={
                    "entity_id": str(best_r.get("entity_id") or ""),
                    "name": best_r.get("name_zh") or best_r.get("name", ""),
                    "entity_type": "restaurant",
                    "area_name": best_r.get("area_name", ""),
                    "cuisine_type": best_r.get("cuisine_type", ""),
                    "michelin_star": best_r.get("michelin_star"),
                    "tabelog_score": best_r.get("tabelog_score"),
                    "price_range_min_jpy": best_r.get("price_range_min_jpy"),
                    "price_range_max_jpy": best_r.get("price_range_max_jpy"),
                    "requires_reservation": best_r.get("requires_reservation", False),
                    "data_tier": best_r.get("data_tier", "B"),
                    "final_score": best_score,
                    "duration_min": 60,
                    "is_optional": False,
                    "source": "meal_flex_filler",
                },
                style=style,
                booking_required=bool(best_r.get("requires_reservation")),
            )
            meals.append(slot)
            used_ids.add(str(best_r.get("entity_id") or ""))

            if best_r.get("requires_reservation"):
                level = "must_book" if _is_michelin(best_r) else "should_book"
                booking_alerts.append({
                    "entity_id": str(best_r.get("entity_id") or ""),
                    "label": best_r.get("name_zh") or best_r.get("name", ""),
                    "booking_level": level,
                    "deadline_hint": "建议出发前 2-4 周预约" if _is_michelin(best_r) else "建议提前 3-7 天预约",
                    "impact_if_missed": "米其林餐厅很难当天订到" if _is_michelin(best_r) else "热门餐厅可能需等位",
                })

        results.append(MealFillResult(
            day_index=day_idx,
            meals=meals,
            booking_alerts=booking_alerts,
            unfilled_slots=unfilled,
        ))

        logger.debug(
            "Day %d: filled %d meals, unfilled=%s",
            day_idx, len(meals), unfilled,
        )

    return results


def merge_meals_into_day_dicts(
    day_dicts: list[dict],
    meal_results: list[MealFillResult],
) -> list[dict]:
    """
    将餐厅填充结果合并回 day_dicts（追加到 items）。

    Args:
        day_dicts:    原始 day_dict 列表
        meal_results: fill_meals 的输出

    Returns:
        合并后的 day_dicts（in-place 修改）
    """
    meal_map = {mr.day_index: mr for mr in meal_results}

    for dd in day_dicts:
        day_idx = dd.get("day_number") or dd.get("day_index", 0)
        mr = meal_map.get(day_idx)
        if not mr:
            continue

        existing = dd.setdefault("items", [])
        for slot in mr.meals:
            item = dict(slot.restaurant)
            item["item_type"] = "restaurant"
            item["meal_type"] = slot.meal_type
            item["meal_style"] = slot.style
            existing.append(item)

        alerts = dd.setdefault("booking_alerts", [])
        alerts.extend(mr.booking_alerts)

        if mr.unfilled_slots:
            dd.setdefault("warnings", []).append(
                f"未能填充餐次：{', '.join(mr.unfilled_slots)}"
            )

    return day_dicts

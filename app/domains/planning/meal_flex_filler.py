"""
meal_flex_filler.py — S3: 弹性餐厅填充器（v3 — 走廊感知 + day-type 规则 + 去重）

输入：
  - frames: list[DayFrame]       来自 route_skeleton_builder（含 meal_windows）
  - restaurant_pool: list[dict]  候选餐厅（entity_type=restaurant）
  - trip_profile: dict           TripProfile 字段（budget, avoid_list, party_type）

输出：
  - list[MealFillResult]  每天的餐厅填充结果

规则：
  1. 每天按 meal_windows（breakfast / lunch / dinner）各最多填 1 家
  2. lunch/dinner 优先选与 primary_corridor 一致的走廊沿线餐厅
  3. breakfast 优先选 sleep_base（住宿周边）
  4. day_type=arrival 只在 到达走廊+住宿周边 选餐
  5. day_type=departure 只给 breakfast+lunch（住宿周边）
  6. day_type=theme_park — lunch 放宽（园区内/住宿周边均可），dinner 住宿周边
  7. 同日菜系不重复；跨日寿司/拉面最多出现 2 次
  8. michelin_star 餐厅只在 dinner 推荐
  9. requires_reservation=True 追加 booking_alert
  10. budget 过滤
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


# avoid 关键词的中英文映射
_AVOID_ZH_MAP = {
    "sushi": ["寿司", "鮨", "すし"],
    "sashimi": ["刺身", "さしみ", "生鱼片"],
    "raw": ["生鱼", "刺身"],
    "yakiniku": ["烧肉", "焼肉", "やきにく"],
    "ramen": ["拉面", "ラーメン", "らーめん"],
}

def _cuisine_ok(restaurant: dict, avoid_list: set[str]) -> bool:
    """检查菜系是否在避免列表里（同时检查中英文关键词）"""
    cuisine = (restaurant.get("cuisine_type", "") or "").lower()
    name = (restaurant.get("name_zh", "") or restaurant.get("name", "") or "").lower()
    for av in avoid_list:
        av_l = av.lower()
        # 英文关键词匹配
        if av_l in cuisine or av_l in name:
            return False
        # 中文关键词匹配
        for zh_kw in _AVOID_ZH_MAP.get(av_l, []):
            if zh_kw in name or zh_kw in cuisine:
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


# ── 走廊关联判断辅助 ──────────────────────────────────────────────────────────

def _corridor_tags_of(restaurant: dict) -> set[str]:
    """提取餐厅关联的走廊标签集合。"""
    tags = set(restaurant.get("corridor_tags") or [])
    area = (restaurant.get("area_name") or "").lower()
    if area:
        tags.add(area)
    return tags


# 走廊→城市映射（authority bare keys + 旧前缀别名，用于同城兜底匹配）
_CORRIDOR_TO_CITY = {
    # 京都
    "arashiyama": "kyoto", "daigo": "kyoto", "fushimi": "kyoto",
    "gion": "kyoto", "gosho": "kyoto", "higashiyama": "kyoto",
    "kawaramachi": "kyoto", "kinugasa": "kyoto", "kita_ku": "kyoto",
    "nijo": "kyoto", "nishikyo": "kyoto", "okazaki": "kyoto",
    "philosopher_path": "kyoto", "zen_garden": "kyoto", "uji": "kyoto",
    # 大阪
    "namba": "osaka", "osakajo": "osaka", "sakurajima": "osaka",
    "shinsekai": "osaka", "osa_nakanoshima": "osaka", "tsuruhashi": "osaka",
    "umeda": "osaka",
    # 奈良 / 神户 / 滋贺
    "nara_park": "nara",
    "kobe_kitano": "kobe", "arima": "kobe",
    "shiga": "shiga",
    # 旧前缀别名兜底
    "kyo_fushimi": "kyoto", "kyo_arashiyama": "kyoto", "kyo_higashiyama": "kyoto",
    "kyo_gion": "kyoto", "kyo_kawaramachi": "kyoto", "kyo_okazaki": "kyoto",
    "kyo_nijo": "kyoto", "kyo_zen_garden": "kyoto",
    "kyo_nishikyo": "kyoto", "kyo_kinugasa": "kyoto",
    "osa_namba": "osaka", "osa_osakajo": "osaka",
    "osa_sakurajima": "osaka", "osa_shinsekai": "osaka",
}


def _is_in_corridor(restaurant: dict, corridor: str, resolver=None, allow_same_city: bool = False) -> bool:
    """判断餐厅是否属于指定走廊（或其邻近走廊）。
    
    allow_same_city: 当 True 时，同城市但不同走廊也返回 True（作为宽松兜底）。
    """
    if not corridor:
        return True  # 无走廊约束时放行
    tags = _corridor_tags_of(restaurant)
    corr_lower = corridor.lower()
    # 直接匹配
    if corr_lower in tags or any(corr_lower in t for t in tags):
        return True
    # 通过 resolver 判断邻近
    if resolver:
        resolved = set(resolver.resolve(corridor))
        for t in tags:
            for r in resolved:
                if resolver.is_same_or_adjacent(t, r):
                    return True
    # 同城兜底
    if allow_same_city:
        corr_city = _CORRIDOR_TO_CITY.get(corr_lower, "")
        rest_city = (restaurant.get("city_code") or "").lower()
        if corr_city and rest_city == corr_city:
            return True
    return False


def _pick_serving_corridor(
    frame, meal_type: str,
) -> str:
    """根据 day_type + meal_type 决定该餐次优先从哪个走廊选。

    规则：
      arrival  — 所有餐都从 primary_corridor（到达走廊）或 sleep_base 选
      departure — breakfast/lunch 从 sleep_base 选
      theme_park — lunch 放宽（不限走廊），breakfast/dinner 从 sleep_base 选
      normal — breakfast 从 sleep_base，lunch/dinner 从 primary_corridor
    """
    day_type = frame.day_type if hasattr(frame, "day_type") else frame.get("day_type", "normal")
    primary = frame.primary_corridor if hasattr(frame, "primary_corridor") else frame.get("primary_corridor", "")
    sleep = frame.sleep_base if hasattr(frame, "sleep_base") else frame.get("sleep_base", "")

    if day_type == "departure":
        # 返程日：lunch 跟着当日走廊（如大阪城），breakfast 在住宿周边
        if meal_type == "breakfast":
            return sleep or primary
        return primary or sleep
    if day_type == "arrival":
        if meal_type == "breakfast":
            return sleep or primary
        # 到达日的 lunch/dinner 优先到达走廊，次选住宿周边
        return primary or sleep
    if day_type == "theme_park":
        # 主题公园日：lunch/dinner 都优先 primary_corridor（即园区走廊），
        # 而非 sleep_base（住宿区），让餐饮贴着园区安排
        return primary or sleep
    # normal
    if meal_type == "breakfast":
        return sleep or primary
    return primary or sleep


# ── 核心入口 ──────────────────────────────────────────────────────────────────

def fill_meals(
    frames: list,
    restaurant_pool: list[dict],
    trip_profile: dict,
    already_used_ids: Optional[set[str]] = None,
    corridor_resolver=None,
    constraints=None,
) -> list[MealFillResult]:
    """
    为每天的骨架填充餐厅（v3 — 走廊感知 + day-type + cuisine 去重）。

    Args:
        frames:            DayFrame 列表
        restaurant_pool:   候选餐厅列表
        trip_profile:      TripProfile dict
        already_used_ids:  跨天已用餐厅 ID（防重复）
        corridor_resolver: CorridorResolver（可选）
        constraints:       PlanningConstraints（可选，优先于 trip_profile.avoid_list）

    Returns:
        list[MealFillResult]
    """
    used_ids: set[str] = already_used_ids or set()
    # constraints-aware: 优先从 constraints 读 avoid_cuisines
    if constraints and constraints.avoid_cuisines:
        avoid_list: set[str] = constraints.avoid_cuisines
        logger.info("fill_meals: using constraints.avoid_cuisines=%s", sorted(avoid_list))
    else:
        avoid_list: set[str] = set(trip_profile.get("avoid_list", []))
    budget = _budget_level(trip_profile)
    party_type = trip_profile.get("party_type", "couple")

    # 跨日菜系计数（寿司/拉面等高频菜系最多出现 2 次）
    global_cuisine_count: dict[str, int] = {}
    _HIGH_FREQ_LIMIT = 2  # 同一菜系全程最多出现次数

    # 过滤餐厅池
    rest_pool = [
        r for r in restaurant_pool
        if r.get("entity_type") == "restaurant"
        and r.get("is_active", True)
        and _price_ok(r, budget)
        and _cuisine_ok(r, avoid_list)
    ]

    # 推导本次行程涉及的城市集合（用于城市级过滤，防止东京餐厅出现在关西行程里）
    _trip_cities: set[str] = set()
    for frame in frames:
        sb = frame.sleep_base if hasattr(frame, "sleep_base") else frame.get("sleep_base", "")
        if sb:
            _trip_cities.add(sb)
    # sleep_base 可能是 area key（如 kawaramachi, namba），需要映射到 city_code
    _AREA_TO_CITY = {
        "kawaramachi": "kyoto", "gion": "kyoto", "kyoto_station": "kyoto",
        "namba": "osaka", "shinsaibashi": "osaka", "umeda": "osaka",
        "nara": "nara", "kobe": "kobe",
    }
    trip_city_codes: set[str] = set()
    for sb in _trip_cities:
        trip_city_codes.add(_AREA_TO_CITY.get(sb, sb))
    # 关西行程额外包含关联城市
    if trip_city_codes & {"kyoto", "osaka"}:
        trip_city_codes |= {"kyoto", "osaka", "nara", "kobe"}

    if trip_city_codes:
        before = len(rest_pool)
        rest_pool = [
            r for r in rest_pool
            if (r.get("city_code") or "") in trip_city_codes
        ]
        logger.info("城市过滤: %d → %d（保留城市: %s）", before, len(rest_pool), trip_city_codes)

    results: list[MealFillResult] = []

    for frame in frames:
        day_idx = frame.day_index if hasattr(frame, "day_index") else frame["day_index"]
        corridor = frame.primary_corridor if hasattr(frame, "primary_corridor") else frame.get("primary_corridor", "")
        secondary = (frame.secondary_corridor if hasattr(frame, "secondary_corridor") else frame.get("secondary_corridor")) or ""
        day_type = frame.day_type if hasattr(frame, "day_type") else frame.get("day_type", "normal")
        sleep_base = frame.sleep_base if hasattr(frame, "sleep_base") else frame.get("sleep_base", "")
        meal_windows = frame.meal_windows if hasattr(frame, "meal_windows") else frame.get("meal_windows", [])

        # 确定今日需要填充的餐次
        if not meal_windows:
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
        day_cuisines: set[str] = set()  # 当日已用菜系（去重）

        # ── day_type 城市约束（constraints-aware）──────────────────────────
        # theme_park / arrival / departure 日：硬性限制餐厅只能来自当日走廊城市
        # 防止 USJ 日出现京都咖啡店、返程日出现大阪城餐厅等问题
        _city_strict_types = constraints.city_strict_day_types if constraints else {"theme_park", "arrival", "departure"}
        _day_required_city: str = ""
        _day_city_strict: bool = False
        if day_type == "theme_park":
            # USJ 日：必须在大阪城市圈内（sakurajima / namba / osakajo 周边）
            _day_required_city = _CORRIDOR_TO_CITY.get(corridor, "")
            _day_city_strict = day_type in _city_strict_types
        elif day_type == "arrival":
            # 到达日：只允许住宿所在城市
            _day_required_city = _CORRIDOR_TO_CITY.get(sleep_base, "")
            _day_city_strict = day_type in _city_strict_types
        elif day_type == "departure":
            # 返程日：只允许住宿/当日走廊所在城市
            _day_required_city = _CORRIDOR_TO_CITY.get(sleep_base or corridor, "")
            _day_city_strict = day_type in _city_strict_types

        for meal_type in meal_types_needed:
            # 确定该餐次的服务走廊
            serving_corridor = _pick_serving_corridor(frame, meal_type)
            # 备选走廊列表：primary + secondary + sleep_base
            fallback_corridors = [c for c in [corridor, secondary, sleep_base] if c and c != serving_corridor]

            # 第 1 轮：严格走廊匹配
            # 第 2 轮：放宽到备选走廊
            # 第 3 轮：同城市兜底（不同走廊但同一城市）
            # 第 4 轮：全部（最终兜底，theme_park/arrival/departure 仍限城市）
            chosen = None
            chosen_score = -1
            for round_idx in range(4):
                candidates = []
                for r in rest_pool:
                    eid = str(r.get("entity_id") or "")
                    if eid in used_ids:
                        continue
                    if meal_type == "breakfast" and not _is_breakfast_suitable(r):
                        continue
                    if _is_michelin(r) and meal_type != "dinner":
                        continue

                    # 城市硬约束（theme_park / arrival / departure）
                    # round 0-2 严格；round 3 也保留城市约束（只有 normal 日才完全放开）
                    if _day_city_strict and _day_required_city:
                        rest_city = (r.get("city_code") or "").lower()
                        if rest_city and rest_city != _day_required_city:
                            continue

                    # 走廊过滤
                    if round_idx == 0 and serving_corridor:
                        if not _is_in_corridor(r, serving_corridor, corridor_resolver):
                            continue
                    elif round_idx == 1:
                        in_any = False
                        for fc in fallback_corridors:
                            if _is_in_corridor(r, fc, corridor_resolver):
                                in_any = True
                                break
                        if not in_any:
                            continue
                    elif round_idx == 2:
                        # 同城兜底：走廊对应的城市内的餐厅
                        target_corr = serving_corridor or corridor
                        if not _is_in_corridor(r, target_corr, corridor_resolver, allow_same_city=True):
                            continue
                    # round_idx == 3: no filter

                    # 菜系去重（同日 + 跨日）
                    cuisine = (r.get("cuisine_type") or "").lower()
                    if cuisine and cuisine != "other":
                        if cuisine in day_cuisines:
                            continue  # 同日不重复
                        if global_cuisine_count.get(cuisine, 0) >= _HIGH_FREQ_LIMIT:
                            continue  # 全程限频

                    score = _score_restaurant(r, meal_type, serving_corridor or corridor, corridor_resolver)
                    candidates.append((score, r))

                if candidates:
                    candidates.sort(key=lambda x: x[0], reverse=True)
                    chosen_score, chosen = candidates[0]
                    break  # 找到就不进下一轮

            if not chosen:
                unfilled.append(meal_type)
                logger.debug("Day %d: no candidate for %s (corridor=%s)", day_idx, meal_type, serving_corridor)
                continue

            best_r = chosen
            cuisine = (best_r.get("cuisine_type") or "").lower()
            if cuisine and cuisine != "other":
                day_cuisines.add(cuisine)
                global_cuisine_count[cuisine] = global_cuisine_count.get(cuisine, 0) + 1

            style = "destination_meal" if meal_type == "dinner" else "route_meal"
            if meal_type == "breakfast":
                style = "quick"

            # 生成 why_here 理由（全中文，不含 raw key）
            # 走廊/区域中文映射
            _WHY_CORRIDOR_ZH = {
                # bare keys
                "arashiyama": "岚山", "daigo": "醍醐", "fushimi": "伏见",
                "gion": "祇园", "gosho": "御所·西阵", "higashiyama": "东山",
                "kawaramachi": "河原町", "kinugasa": "衣笠", "kita_ku": "北区",
                "nijo": "二条城", "nishikyo": "西京", "okazaki": "冈崎",
                "philosopher_path": "哲学之道", "zen_garden": "枯山水庭园",
                "uji": "宇治",
                "namba": "难波", "osakajo": "大阪城", "sakurajima": "环球影城",
                "shinsekai": "新世界", "osa_nakanoshima": "中之岛",
                "tsuruhashi": "鹤桥", "nara_park": "奈良公园",
                "kobe_kitano": "神户北野", "arima": "有马温泉",
                "shiga": "滋贺",
                # 旧前缀别名
                "kyo_fushimi": "伏见", "kyo_arashiyama": "岚山",
                "kyo_higashiyama": "东山", "kyo_gion": "祇园",
                "kyo_kawaramachi": "河原町", "kyo_okazaki": "冈崎",
                "osa_namba": "难波", "osa_osakajo": "大阪城",
                "osa_sakurajima": "环球影城", "osa_shinsekai": "新世界",
            }
            _WHY_CUISINE_ZH = {
                "sushi": "寿司", "ramen": "拉面", "yakiniku": "烧肉",
                "tempura": "天妇罗", "kushikatsu": "串炸", "yakitori": "烧鸟",
                "takoyaki": "章鱼烧", "okonomiyaki": "大阪烧", "kaiseki": "怀石",
                "cafe": "咖啡轻食", "udon": "乌冬", "tonkatsu": "炸猪排",
            }
            why_parts = []
            area_name = best_r.get("area_name", "")
            if area_name:
                # 净化 area_name：如果是 raw key，转中文
                area_zh = _WHY_CORRIDOR_ZH.get(area_name.lower(), area_name)
                why_parts.append(f"位于{area_zh}")
            cuisine_zh = _WHY_CUISINE_ZH.get(cuisine, cuisine) if cuisine and cuisine != "other" else ""
            if cuisine_zh:
                why_parts.append(cuisine_zh)
            if serving_corridor:
                corr_zh = _WHY_CORRIDOR_ZH.get(serving_corridor, serving_corridor)
                why_parts.append(f"{corr_zh}沿线")
            elif sleep_base:
                why_parts.append("住宿周边")
            why_here = "，".join(why_parts)

            slot = MealSlot(
                meal_type=meal_type,
                restaurant={
                    "entity_id": str(best_r.get("entity_id") or ""),
                    "name": best_r.get("name_zh") or best_r.get("name", ""),
                    "entity_type": "restaurant",
                    "area_name": area_name,
                    "cuisine_type": best_r.get("cuisine_type", ""),
                    "corridor_tags": best_r.get("corridor_tags", []),
                    "michelin_star": best_r.get("michelin_star"),
                    "tabelog_score": best_r.get("tabelog_score"),
                    "price_range_min_jpy": best_r.get("price_range_min_jpy"),
                    "price_range_max_jpy": best_r.get("price_range_max_jpy"),
                    "requires_reservation": best_r.get("requires_reservation", False),
                    "data_tier": best_r.get("data_tier", "B"),
                    "final_score": chosen_score,
                    "duration_min": 60,
                    "is_optional": False,
                    "source": "meal_flex_filler_v3",
                    "why_here": why_here,
                    "serving_corridor": serving_corridor,
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
            "Day %d: filled %d meals, unfilled=%s, cuisines=%s",
            day_idx, len(meals), unfilled, day_cuisines,
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

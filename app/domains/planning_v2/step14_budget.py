"""
step14_budget.py -- 预算核算（纯计算，无 DB 依赖）

基于 CircleProfile.budget_config 和 Step 9 的每日活动序列、
酒店方案和餐厅选择计算旅行总预算。

所有预算常量从 CircleProfile.budget_config 读取（不同圈不同货币不同数值）。
向后兼容：无 circle 时从 budget_estimator.py 读取 v1 常量。
"""

import logging

from app.domains.planning_v2.models import CircleProfile

logger = logging.getLogger(__name__)


def _get_admission_fee(item: dict, default_admission: dict) -> int:
    """提取单个活动项目的门票费用。

    Args:
        item: 活动项目字典
        default_admission: 各类别默认门票（从 circle.budget_config 获取）

    Returns:
        门票费用（本地货币）
    """
    # 优先使用明确的门票费（兼容 admission_fee_jpy 和 cost_local 两种字段名）
    for key in ("admission_fee_jpy", "cost_local", "cost_jpy"):
        if item.get(key) is not None:
            return int(item[key])

    if item.get("admission_free", False):
        return 0

    category = item.get("poi_category", "")
    return default_admission.get(category, 300)


def _get_meal_cost(
    meal_type: str,
    day_meal_data: dict,
    hotel_includes_meal: bool,
    meal_defaults: dict,
    poi_cost_map: dict | None = None,
) -> int:
    """计算单餐费用。

    Args:
        meal_type: "breakfast" / "lunch" / "dinner"
        day_meal_data: 当天的餐食选择数据
        hotel_includes_meal: 酒店是否包含该餐
        meal_defaults: 各餐默认费用（从 food_floor 按比例拆分）
        poi_cost_map: entity_id -> cost 的映射（可选）

    Returns:
        餐费（本地货币）
    """
    if hotel_includes_meal:
        return 0

    # 格式 1：Step 13.5 输出（直接用 meal_type 作为 key）
    selection = day_meal_data.get(meal_type)
    if selection and isinstance(selection, dict):
        for key in ("cost_local", "cost_jpy"):
            if selection.get(key) is not None:
                return int(selection[key])
        eid = selection.get("entity_id")
        if eid and poi_cost_map and eid in poi_cost_map:
            return poi_cost_map[eid]

    # 格式 2：Legacy format（{meal_type}_selection）
    legacy_key = f"{meal_type}_selection"
    legacy_sel = day_meal_data.get(legacy_key)
    if legacy_sel and isinstance(legacy_sel, dict):
        for key in ("cost_local", "cost_jpy", "budget_jpy"):
            if legacy_sel.get(key) is not None:
                return int(legacy_sel[key])

    return meal_defaults.get(meal_type, 1000)


def estimate_budget(
    daily_sequences: list[dict],
    hotel_plan: dict,
    restaurant_selections: dict,
    budget_tier: str,
    circle: CircleProfile,
) -> dict:
    """计算旅行预算。所有预算常量从 circle.budget_config 读取。"""
    if not daily_sequences:
        logger.warning("[预算] daily_sequences 为空")
        return _empty_budget(budget_tier, circle)

    bc = circle.budget_config
    currency = circle.currency
    cny_rate = circle.cny_rate

    transport_config = bc.get("transport_per_day", {})
    hotel_config = bc.get("hotel_per_night", {})
    default_admission = bc.get("default_admission", {})
    food_floor_config = bc.get("food_floor_per_day", {})
    misc_rate = bc.get("misc_buffer_rate", 0.10)

    transport_daily = transport_config.get(budget_tier, 1200)
    hotel_nightly = hotel_plan.get("cost_per_night_jpy") or hotel_config.get(budget_tier, 10000)

    # 餐费默认值：从 food_floor 按比例拆分（早20% 午30% 晚50%）
    food_floor = food_floor_config.get(budget_tier, 3500)
    meal_defaults = {
        "breakfast": int(food_floor * 0.20),
        "lunch": int(food_floor * 0.30),
        "dinner": int(food_floor * 0.50),
    }

    meals_included = hotel_plan.get("meals_included", {})
    global_breakfast_included = meals_included.get("breakfast", False)
    global_dinner_included = meals_included.get("dinner", False)

    # 兼容两种 restaurant_selections 格式
    meal_by_day: dict[int, dict] = {}
    meal_by_date: dict[str, dict] = {}
    if "meal_selections" in restaurant_selections:
        for ms in restaurant_selections["meal_selections"]:
            if isinstance(ms, dict):
                meal_by_day[ms.get("day", 0)] = ms
    elif "by_date" in restaurant_selections:
        meal_by_date = restaurant_selections.get("by_date", {})

    # ── 逐日计算 ─────────────────────────────────────────────────────
    daily_breakdown: list[dict] = []
    totals = {"hotel": 0, "activities": 0, "meals": 0, "transport": 0, "misc": 0}
    total_days = len(daily_sequences)

    for day_idx, day_seq in enumerate(daily_sequences):
        day_date = day_seq.get("date", f"day_{day_idx + 1}")
        items = day_seq.get("activities", day_seq.get("items", []))

        is_last_day = day_idx == total_days - 1
        hotel_cost = 0 if is_last_day else hotel_nightly

        # ── 门票费 ───────────────────────────────────────────────
        activities_cost = 0
        for item in items:
            if item.get("entity_type") == "poi":
                activities_cost += _get_admission_fee(item, default_admission)

        # ── 餐费 ─────────────────────────────────────────────────
        day_breakfast_included = day_seq.get("hotel_breakfast_included", global_breakfast_included)
        day_dinner_included = day_seq.get("hotel_dinner_included", global_dinner_included)
        day_rest_selections = meal_by_day.get(day_idx + 1, {}) or meal_by_date.get(day_date, {})

        breakfast_cost = _get_meal_cost(
            "breakfast",
            day_rest_selections,
            day_breakfast_included,
            meal_defaults,
        )
        lunch_cost = _get_meal_cost(
            "lunch",
            day_rest_selections,
            False,
            meal_defaults,
        )
        dinner_cost = _get_meal_cost(
            "dinner",
            day_rest_selections,
            day_dinner_included,
            meal_defaults,
        )
        meals_cost = breakfast_cost + lunch_cost + dinner_cost

        transport_cost = transport_daily

        subtotal = hotel_cost + activities_cost + meals_cost + transport_cost
        misc_cost = int(subtotal * misc_rate)
        total_cost = subtotal + misc_cost

        daily_breakdown.append(
            {
                "date": day_date,
                "hotel": hotel_cost,
                "activities": activities_cost,
                "meals": meals_cost,
                "transport": transport_cost,
                "misc": misc_cost,
                "total": total_cost,
            }
        )

        totals["hotel"] += hotel_cost
        totals["activities"] += activities_cost
        totals["meals"] += meals_cost
        totals["transport"] += transport_cost
        totals["misc"] += misc_cost

    # ── 全程汇总 ─────────────────────────────────────────────────────
    trip_total_local = sum(d["total"] for d in daily_breakdown)
    trip_total_cny = round(trip_total_local * cny_rate)

    # within_budget：从 budget_config 获取上限，无则估算
    hotel_cap = hotel_config.get(budget_tier, 10000)
    transport_cap = transport_config.get(budget_tier, 1200)
    food_cap = food_floor_config.get(budget_tier, 3500)
    daily_cap = int((hotel_cap + transport_cap + food_cap) * 2)  # 2x 作为宽松上限
    cap = daily_cap * total_days
    within_budget = trip_total_local <= cap

    result = {
        "daily_breakdown": daily_breakdown,
        "trip_total_local": trip_total_local,
        "currency": currency,
        "trip_total_cny": trip_total_cny,
        "budget_tier": budget_tier,
        "within_budget": within_budget,
        "breakdown_by_category": totals,
    }

    logger.info(
        "[预算] 完成: %d 天, total=%d %s (%.0f CNY), tier=%s, within=%s",
        total_days,
        trip_total_local,
        currency,
        trip_total_cny,
        budget_tier,
        within_budget,
    )

    return result


def _empty_budget(budget_tier: str, circle: CircleProfile) -> dict:
    """返回空的预算结构。"""
    return {
        "daily_breakdown": [],
        "trip_total_local": 0,
        "currency": circle.currency,
        "trip_total_cny": 0,
        "budget_tier": budget_tier,
        "within_budget": True,
        "breakdown_by_category": {
            "hotel": 0,
            "activities": 0,
            "meals": 0,
            "transport": 0,
            "misc": 0,
        },
    }

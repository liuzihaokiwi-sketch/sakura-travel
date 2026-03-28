"""
app/domains/planning/budget_estimator.py

每日预算估算器（D5）

从行程 items + entity 字段计算每日参考花费：
  门票费（poi.admission_fee_jpy）
  餐饮费（restaurant.budget_lunch_jpy + budget_dinner_jpy）
  交通费（entity.budget_tier 推导）

输出：DayBudgetEstimate 列表，写入 plan_metadata.day_budgets

汇率参考：1 JPY ≈ 0.047 CNY（常量，运营可在 config 覆盖）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 默认汇率（日元 → 人民币）
JPY_TO_CNY = 0.047

# budget_tier → 每天交通费估算（日元）
TRANSPORT_BUDGET_BY_TIER: dict[str, int] = {
    "budget":  800,
    "mid":    1200,
    "premium": 2000,
    "luxury":  3000,
}

# 无 admission_fee_jpy 时按景点类型的默认门票（日元）
DEFAULT_ADMISSION_BY_POI_CATEGORY: dict[str, int] = {
    "temple":      500,
    "shrine":        0,
    "museum":     1000,
    "theme_park": 7000,
    "park":          0,
    "castle":      600,
    "garden":      500,
}


@dataclass
class DayBudgetEstimate:
    day_index: int
    admission_jpy: int = 0
    food_jpy: int = 0
    transport_jpy: int = 0
    misc_jpy: int = 0        # 小费/零食/纪念品估算（总额5%）

    @property
    def total_jpy(self) -> int:
        base = self.admission_jpy + self.food_jpy + self.transport_jpy
        self.misc_jpy = int(base * 0.05)
        return base + self.misc_jpy

    @property
    def total_cny(self) -> float:
        return round(self.total_jpy * JPY_TO_CNY, 0)

    def to_dict(self) -> dict:
        return {
            "day_index": self.day_index,
            "admission_jpy": self.admission_jpy,
            "food_jpy": self.food_jpy,
            "transport_jpy": self.transport_jpy,
            "misc_jpy": self.misc_jpy,
            "total_jpy": self.total_jpy,
            "total_cny": self.total_cny,
        }


async def estimate_day_budgets(
    session: Any,
    plan_id: Any,
    budget_level: str = "mid",
) -> list[DayBudgetEstimate]:
    """
    从 ItineraryPlan + ItineraryDay/Item + EntityBase 计算每日预算估算。

    Args:
        session:      AsyncSession
        plan_id:      UUID
        budget_level: "budget" / "mid" / "premium" / "luxury"

    Returns:
        list[DayBudgetEstimate]（按 day_index 升序）
    """
    from sqlalchemy import select
    from app.db.models.derived import ItineraryDay, ItineraryItem
    from app.db.models.catalog import EntityBase, Poi, Restaurant

    days_q = await session.execute(
        select(ItineraryDay)
        .where(ItineraryDay.plan_id == plan_id)
        .order_by(ItineraryDay.day_number)
    )
    db_days = days_q.scalars().all()

    transport_base = TRANSPORT_BUDGET_BY_TIER.get(budget_level, 1200)
    results: list[DayBudgetEstimate] = []

    for day in db_days:
        estimate = DayBudgetEstimate(
            day_index=day.day_number,
            transport_jpy=transport_base,
        )

        items_q = await session.execute(
            select(ItineraryItem)
            .where(ItineraryItem.day_id == day.day_id)
            .order_by(ItineraryItem.sort_order)
        )
        items = items_q.scalars().all()

        for item in items:
            if not item.entity_id:
                continue
            ent = await session.get(EntityBase, item.entity_id)
            if not ent:
                continue

            if ent.entity_type == "poi":
                poi = await session.get(Poi, ent.entity_id)
                if poi:
                    if poi.admission_free:
                        pass  # 免费
                    elif poi.admission_fee_jpy is not None:
                        estimate.admission_jpy += poi.admission_fee_jpy
                    else:
                        # 按类别估算默认门票
                        cat = poi.poi_category or ""
                        estimate.admission_jpy += DEFAULT_ADMISSION_BY_POI_CATEGORY.get(cat, 300)

            elif ent.entity_type == "restaurant":
                rest = await session.get(Restaurant, ent.entity_id)
                if rest:
                    # 根据 item 的时段选午/晚餐预算
                    time_hint = item.start_time or ""
                    try:
                        hour = int(time_hint.split(":")[0]) if ":" in time_hint else 12
                    except (ValueError, IndexError):
                        hour = 12

                    if hour < 15 and rest.budget_lunch_jpy:
                        estimate.food_jpy += rest.budget_lunch_jpy
                    elif rest.budget_dinner_jpy:
                        estimate.food_jpy += rest.budget_dinner_jpy
                    elif rest.price_range_min_jpy:
                        # fallback：使用最低价格
                        estimate.food_jpy += rest.price_range_min_jpy

        # 餐饮最低保底（没有餐厅 entity 时按 budget_level 估算）
        if estimate.food_jpy == 0:
            food_floor = {"budget": 2000, "mid": 3500, "premium": 6000, "luxury": 10000}
            estimate.food_jpy = food_floor.get(budget_level, 3500)

        results.append(estimate)

    return results


async def attach_budget_to_plan(
    session: Any,
    plan_id: Any,
    budget_level: str = "mid",
) -> list[dict]:
    """
    计算并写入 plan_metadata.day_budgets。
    返回 day_budgets 列表（供调用方记录日志）。
    """
    from sqlalchemy import select
    from app.db.models.derived import ItineraryPlan

    estimates = await estimate_day_budgets(session, plan_id, budget_level)
    budget_dicts = [e.to_dict() for e in estimates]

    plan = await session.get(ItineraryPlan, plan_id)
    if plan is not None:
        meta = dict(plan.plan_metadata or {})
        meta["day_budgets"] = budget_dicts
        total_jpy = sum(e.total_jpy for e in estimates)
        meta["total_budget_jpy"] = total_jpy
        meta["total_budget_cny"] = round(total_jpy * JPY_TO_CNY, 0)
        plan.plan_metadata = meta
        logger.info(
            "每日预算已写入 plan=%s 总计 ¥%.0f CNY",
            plan_id, meta["total_budget_cny"],
        )

    return budget_dicts

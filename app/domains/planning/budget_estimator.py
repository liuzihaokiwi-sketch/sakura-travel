"""
app/domains/planning/budget_estimator.py

每日预算估算器（D5）

从行程 items + entity 字段计算每日参考花费：
  门票费（poi.admission_fee_jpy）
  餐饮费（restaurant.budget_lunch_jpy + budget_dinner_jpy）
  交通费（budget_level 推导）
  住宿费（hotel.typical_price_min_jpy 或 budget_level 默认值）
  杂费（总额 10% buffer）

输出：DayBudgetEstimate 列表 + TripBudgetEstimate 汇总，写入 plan_metadata

汇率参考：1 JPY ≈ 0.047 CNY（常量，运营可在 config 覆盖）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 默认汇率（日元 → 人民币）
JPY_TO_CNY = 0.047

# budget_level → 每天交通费估算（日元）
TRANSPORT_BUDGET_BY_TIER: dict[str, int] = {
    "budget":  800,
    "mid":    1200,
    "premium": 2000,
    "luxury":  3000,
}

# budget_level → 每晚住宿费默认值（日元，无酒店 entity 时使用）
HOTEL_BUDGET_BY_TIER: dict[str, int] = {
    "budget":  5000,
    "mid":    10000,
    "premium": 20000,
    "luxury":  40000,
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

# 餐饮保底（无餐厅 entity 时）
FOOD_FLOOR_BY_TIER: dict[str, int] = {
    "budget": 2000,
    "mid":    3500,
    "premium": 6000,
    "luxury": 10000,
}

# misc buffer 比例
MISC_BUFFER_RATE = 0.10


@dataclass
class DayBudgetEstimate:
    day_index: int
    admission_jpy: int = 0
    food_jpy: int = 0
    transport_jpy: int = 0
    hotel_jpy: int = 0
    misc_jpy: int = 0

    @property
    def subtotal_jpy(self) -> int:
        """门票 + 餐饮 + 交通 + 住宿（不含杂费）"""
        return self.admission_jpy + self.food_jpy + self.transport_jpy + self.hotel_jpy

    @property
    def total_jpy(self) -> int:
        self.misc_jpy = int(self.subtotal_jpy * MISC_BUFFER_RATE)
        return self.subtotal_jpy + self.misc_jpy

    @property
    def total_cny(self) -> float:
        return round(self.total_jpy * JPY_TO_CNY, 0)

    def to_dict(self) -> dict:
        return {
            "day_index": self.day_index,
            "admission_jpy": self.admission_jpy,
            "food_jpy": self.food_jpy,
            "transport_jpy": self.transport_jpy,
            "hotel_jpy": self.hotel_jpy,
            "misc_jpy": self.misc_jpy,
            "total_jpy": self.total_jpy,
            "total_cny": self.total_cny,
        }


@dataclass
class TripBudgetEstimate:
    """全程预算汇总"""
    total_days: int
    day_budgets: list[DayBudgetEstimate]
    total_admission_jpy: int = 0
    total_food_jpy: int = 0
    total_transport_jpy: int = 0
    total_hotel_jpy: int = 0
    total_misc_jpy: int = 0
    total_jpy: int = 0
    total_cny: float = 0.0
    avg_daily_jpy: int = 0
    avg_daily_cny: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_days": self.total_days,
            "total_admission_jpy": self.total_admission_jpy,
            "total_food_jpy": self.total_food_jpy,
            "total_transport_jpy": self.total_transport_jpy,
            "total_hotel_jpy": self.total_hotel_jpy,
            "total_misc_jpy": self.total_misc_jpy,
            "total_jpy": self.total_jpy,
            "total_cny": self.total_cny,
            "avg_daily_jpy": self.avg_daily_jpy,
            "avg_daily_cny": self.avg_daily_cny,
            "day_budgets": [d.to_dict() for d in self.day_budgets],
        }


def estimate_trip_budget(
    day_budgets: list[DayBudgetEstimate],
) -> TripBudgetEstimate:
    """
    从已计算的 day_budgets 聚合全程预算。

    纯计算函数，无 DB 访问。
    """
    n = len(day_budgets)
    total_admission = sum(d.admission_jpy for d in day_budgets)
    total_food = sum(d.food_jpy for d in day_budgets)
    total_transport = sum(d.transport_jpy for d in day_budgets)
    total_hotel = sum(d.hotel_jpy for d in day_budgets)
    total_misc = sum(d.misc_jpy for d in day_budgets)
    total = sum(d.total_jpy for d in day_budgets)
    total_cny = round(total * JPY_TO_CNY, 0)

    return TripBudgetEstimate(
        total_days=n,
        day_budgets=day_budgets,
        total_admission_jpy=total_admission,
        total_food_jpy=total_food,
        total_transport_jpy=total_transport,
        total_hotel_jpy=total_hotel,
        total_misc_jpy=total_misc,
        total_jpy=total,
        total_cny=total_cny,
        avg_daily_jpy=total // max(n, 1),
        avg_daily_cny=round(total_cny / max(n, 1), 0),
    )


async def estimate_day_budgets(
    session: Any,
    plan_id: Any,
    budget_level: str = "mid",
) -> list[DayBudgetEstimate]:
    """
    从 ItineraryPlan + ItineraryDay/Item + EntityBase 计算每日预算估算。

    包含：门票、餐饮、交通、住宿、杂费五项。

    Args:
        session:      AsyncSession
        plan_id:      UUID
        budget_level: "budget" / "mid" / "premium" / "luxury"

    Returns:
        list[DayBudgetEstimate]（按 day_index 升序）
    """
    from sqlalchemy import select
    from app.db.models.derived import ItineraryDay, ItineraryItem, ItineraryPlan
    from app.db.models.catalog import EntityBase, Poi, Restaurant, Hotel

    days_q = await session.execute(
        select(ItineraryDay)
        .where(ItineraryDay.plan_id == plan_id)
        .order_by(ItineraryDay.day_number)
    )
    db_days = days_q.scalars().all()

    transport_base = TRANSPORT_BUDGET_BY_TIER.get(budget_level, 1200)
    hotel_default = HOTEL_BUDGET_BY_TIER.get(budget_level, 10000)

    # ── 从 plan_metadata 取住宿策略，找到每晚酒店 entity ──
    hotel_price_by_day: dict[int, int] = {}
    try:
        plan = await session.get(ItineraryPlan, plan_id)
        if plan and plan.plan_metadata:
            evidence = plan.plan_metadata.get("evidence_bundle", {})
            # hotel bases 在 design_brief.hotel_base.bases
            # 也可从 plan_metadata 直接读
        # 查找 hotel items（itinerary_items 中 item_type='hotel'）
        hotel_items_q = await session.execute(
            select(ItineraryItem, ItineraryDay)
            .join(ItineraryDay, ItineraryItem.day_id == ItineraryDay.day_id)
            .where(
                ItineraryDay.plan_id == plan_id,
                ItineraryItem.item_type == "hotel",
            )
        )
        for h_item, h_day in hotel_items_q.all():
            if not h_item.entity_id:
                continue
            hotel = await session.get(Hotel, h_item.entity_id)
            if hotel and hotel.typical_price_min_jpy:
                hotel_price_by_day[h_day.day_number] = hotel.typical_price_min_jpy
    except Exception as exc:
        logger.debug("hotel price lookup skipped: %s", exc)

    results: list[DayBudgetEstimate] = []
    total_days = len(db_days)

    for idx, day in enumerate(db_days):
        # 最后一天通常不需要住宿
        is_last_day = (idx == total_days - 1)

        estimate = DayBudgetEstimate(
            day_index=day.day_number,
            transport_jpy=transport_base,
            hotel_jpy=0 if is_last_day else hotel_price_by_day.get(day.day_number, hotel_default),
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
            estimate.food_jpy = FOOD_FLOOR_BY_TIER.get(budget_level, 3500)

        results.append(estimate)

    return results


async def attach_budget_to_plan(
    session: Any,
    plan_id: Any,
    budget_level: str = "mid",
) -> dict:
    """
    计算每日预算 + 全程汇总，写入 plan_metadata。

    写入字段：
      - day_budgets: list[dict]        每日明细
      - trip_budget: dict               全程汇总
      - total_budget_jpy: int           全程总额（日元）
      - total_budget_cny: float         全程总额（人民币）

    返回 trip_budget dict。
    """
    from app.db.models.derived import ItineraryPlan

    estimates = await estimate_day_budgets(session, plan_id, budget_level)
    trip = estimate_trip_budget(estimates)
    trip_dict = trip.to_dict()

    plan = await session.get(ItineraryPlan, plan_id)
    if plan is not None:
        meta = dict(plan.plan_metadata or {})
        meta["day_budgets"] = trip_dict["day_budgets"]
        meta["trip_budget"] = {
            k: v for k, v in trip_dict.items() if k != "day_budgets"
        }
        meta["total_budget_jpy"] = trip.total_jpy
        meta["total_budget_cny"] = trip.total_cny
        plan.plan_metadata = meta
        logger.info(
            "预算估算完成 plan=%s days=%d total=¥%d JPY (≈¥%.0f CNY) avg=¥%d/day",
            plan_id, trip.total_days, trip.total_jpy, trip.total_cny,
            trip.avg_daily_jpy,
        )

    return trip_dict

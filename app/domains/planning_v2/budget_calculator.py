"""
Budget Calculator — 根据方案 + 吃住档位计算费用预估。

数据来源：
- policy.json 的 budget_mix_ratios（升降档混搭比例）
- live_facts/prices.json（门票、交通固定费用）
- 方案中的城市和景点列表（决定门票费用）
"""
from __future__ import annotations

import math
from typing import Any

from app.domains.templates.loader import get_template_loader


def calculate_budget(
    plan: dict[str, Any],
    dining_tier: str,
    hotel_tier: str,
    party: dict[str, Any],
    comfort_addons: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """
    计算费用预估。

    Args:
        plan: plan_version 对象（含 city_allocation, daily_plans）
        dining_tier: street / local_good / fine / top
        hotel_tier: budget / comfort / premium / luxury
        party: {"adults": 2, "children": 0, "elderly": 0}
        comfort_addons: {"luggage_delivery": true, "occasional_taxi": false}

    Returns:
        BudgetEstimate 字典
    """
    loader = get_template_loader()
    policy = loader.load_policy()
    prices = loader.load_live_prices()
    mix = policy.get("budget_mix_ratios", {})

    total_days = plan.get("total_days", 7)
    total_nights = max(1, total_days - 1)
    total_meals = total_days * 2  # 午餐 + 晚餐
    party_size = party.get("adults", 2) + party.get("children", 0) + party.get("elderly", 0)
    room_count = max(1, math.ceil(party_size / 2))

    # ── 餐饮 ──

    dining_prices = mix.get("dining_price_ranges_cny", {}).get(dining_tier, {"low": 80, "high": 150})
    dining_mix = mix.get("dining", {}).get(dining_tier, {"base_pct": 0.70, "upgrade_pct": 0.15, "downgrade_pct": 0.15})

    base_meals = int(total_meals * dining_mix["base_pct"])
    upgrade_meals = int(total_meals * dining_mix["upgrade_pct"])
    downgrade_meals = total_meals - base_meals - upgrade_meals

    # 升档价格约为当前档位的1.5-2倍
    upgrade_price = dining_prices["high"] * 1.8
    # 降档价格约为当前档位的0.4-0.5
    downgrade_price = max(30, dining_prices["low"] * 0.5)

    base_avg = (dining_prices["low"] + dining_prices["high"]) / 2
    dining_per_person = (
        base_meals * base_avg
        + upgrade_meals * upgrade_price
        + downgrade_meals * downgrade_price
    )
    dining_total = int(dining_per_person)

    # ── 住宿 ──

    hotel_prices = mix.get("hotel_price_ranges_cny", {}).get(hotel_tier, {"low": 500, "high": 900})
    hotel_mix_cfg = mix.get("hotel", {}).get(hotel_tier, {"upgrade_nights_per_7": 0})

    upgrade_nights = 0
    if total_nights >= 5:
        upgrade_per_7 = hotel_mix_cfg.get("upgrade_nights_per_7", 0)
        upgrade_nights = max(0, int(total_nights / 7 * upgrade_per_7))

    base_nights = total_nights - upgrade_nights
    base_avg_hotel = (hotel_prices["low"] + hotel_prices["high"]) / 2
    upgrade_avg_hotel = base_avg_hotel * 1.8  # 升级档价格约1.8倍

    hotel_total_room = base_nights * base_avg_hotel + upgrade_nights * upgrade_avg_hotel
    hotel_per_person = int(hotel_total_room * room_count / party_size)

    # ── 交通 ──

    transport_total = _estimate_transport(plan, prices)

    # ── 门票 ──

    tickets_total = _estimate_tickets(plan, prices)

    # ── 舒适加购 ──

    addons_total = 0
    if comfort_addons:
        # 城市间转移次数
        cities = [a["city"] for a in plan.get("city_allocation", []) if a.get("role") == "primary"]
        transfers = max(0, len(cities) - 1)

        if comfort_addons.get("luggage_delivery"):
            addons_total += transfers * 125  # 约100-150元/次取中间值
        if comfort_addons.get("occasional_taxi"):
            addons_total += int(total_days * 50)  # 约300-500/全程，按天均摊

    return {
        "dining_total": dining_total,
        "hotel_total": hotel_per_person,
        "transport": transport_total,
        "tickets": tickets_total,
        "addons": addons_total,
        "total_per_person": dining_total + hotel_per_person + transport_total + tickets_total + addons_total,
        "currency": "CNY",
        "breakdown": {
            "dining": {
                "tier": dining_tier,
                "total_meals": total_meals,
                "base_meals": base_meals,
                "upgrade_meals": upgrade_meals,
                "downgrade_meals": downgrade_meals,
            },
            "hotel": {
                "tier": hotel_tier,
                "total_nights": total_nights,
                "base_nights": base_nights,
                "upgrade_nights": upgrade_nights,
                "rooms": room_count,
            },
        },
    }


def _estimate_transport(plan: dict[str, Any], prices: dict[str, Any]) -> int:
    """估算交通费用（每人）。"""
    total_days = plan.get("total_days", 7)
    transport_prices = prices.get("transport", {})

    # 机场往返
    airport_one_way = 75  # 南海Rapi:t ~1450JPY ≈ 75CNY
    airport_cost = airport_one_way * 2

    # 市内交通：ICOCA日均
    daily_transport = 60  # ~1000-1500JPY/天 ≈ 50-75CNY
    city_transport = daily_transport * total_days

    # 城市间交通
    cities = [a["city"] for a in plan.get("city_allocation", []) if a.get("role") == "primary"]
    intercity_cost = max(0, len(cities) - 1) * 50  # 大阪→京都 ~580JPY ≈ 30CNY，取宽松值

    return int(airport_cost + city_transport + intercity_cost)


def _estimate_tickets(plan: dict[str, Any], prices: dict[str, Any]) -> int:
    """估算门票费用（每人）。"""
    total = 0
    poi_prices = prices.get("poi", {})

    daily_plans = plan.get("daily_plans", [])
    for dp in daily_plans:
        tmpl_id = dp.get("day_template_id", "")

        # USJ
        if "usj" in tmpl_id:
            usj = poi_prices.get("usj", {})
            # 取中间值
            total += 500  # ~10000JPY ≈ 500CNY

        # 一般景点（寺庙/城堡等）：每天约30-50CNY
        elif dp.get("city") in ("osaka", "kyoto"):
            total += 40  # 平均每天门票

    return int(total)

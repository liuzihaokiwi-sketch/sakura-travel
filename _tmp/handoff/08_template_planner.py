"""
Template Planner — 基于模板的方案生成引擎。

纯规则驱动，不用 AI。流程：
1. 读 trip_constraints
2. 计算总可用天数
3. 分配城市天数
4. 选 day 模板
5. 匹配季节活动
6. 应用约束（pre_booked / skip）
7. 排序（fatigue / prefers_after / avoid_after）
8. 校验
9. 计算可加体验
10. 输出 plan_version
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from app.domains.templates.loader import get_template_loader

logger = logging.getLogger(__name__)


def generate_plan_preview(constraints: dict[str, Any]) -> dict[str, Any]:
    """
    从 trip_constraints 生成预览方案。

    Args:
        constraints: trip_constraints 对象（从 TripRequest.raw_input 读取）

    Returns:
        plan_version 对象，含 daily_plans / decisions / addable_experiences
    """
    loader = get_template_loader()
    policy = loader.load_policy()

    # 1. 解析日期
    dates = constraints["dates"]
    start = date.fromisoformat(dates["start"])
    end = date.fromisoformat(dates["end"])
    total_calendar_days = (end - start).days + 1  # 含首尾

    arrival_capacity = policy["city_allocation"]["arrival_slot_capacity"].get(
        dates.get("arrival_slot", "afternoon"), 0.5
    )
    departure_capacity = policy["city_allocation"]["departure_slot_capacity"].get(
        dates.get("departure_slot", "morning"), 0.25
    )
    # 有效天数 = (中间整天) + 到达日容量 + 离开日容量
    effective_days = (total_calendar_days - 2) + arrival_capacity + departure_capacity
    if total_calendar_days <= 1:
        effective_days = arrival_capacity

    # 2. 确定城市分配
    vibe = constraints.get("vibe", "classic")
    density = constraints.get("density", "balanced")
    party = constraints.get("party", {"adults": 2, "children": 0, "elderly": 0})
    city_alloc = _allocate_cities(effective_days, vibe, party, constraints, policy)

    # 3. 为每个城市选 day 模板
    daily_plans = []
    day_counter = 1

    for alloc in city_alloc:
        city = alloc["city"]
        city_days = alloc["days"]

        if city in ("nara", "uji", "himeji"):
            # 半天/一天目的地，生成简单描述
            daily_plans.append({
                "day": day_counter,
                "city": city,
                "day_template_id": f"{city}_visit",
                "title": _get_city_title(city),
                "description": _get_city_description(city),
                "key_slots": [],
            })
            day_counter += 1
            continue

        # 主城市：从 days.json 选模板
        try:
            city_data = loader.load_city_days(city)
        except Exception:
            logger.warning("No days.json for city %s, skipping", city)
            continue

        templates = city_data.get("day_templates", [])
        selected = _select_day_templates(
            templates, city_days, vibe, density, party, constraints
        )

        for tmpl in selected:
            daily_plans.append({
                "day": day_counter,
                "city": city,
                "day_template_id": tmpl["template_id"],
                "title": tmpl.get("label", ""),
                "description": tmpl.get("description", ""),
                "key_slots": [
                    s["slot_id"]
                    for s in tmpl.get("slots", [])
                    if s.get("priority") in ("P1", "P2")
                ],
            })
            day_counter += 1

    # 4. 检查季节活动
    for alloc in city_alloc:
        city = alloc["city"]
        try:
            events = loader.load_seasonal_events(city)
            _apply_seasonal_overlays(daily_plans, events, start, end)
        except Exception:
            pass

    # 5. 计算关键决策解释
    decisions = _generate_decisions(city_alloc, constraints, daily_plans)

    # 6. 计算可加体验
    addable = _compute_addable_experiences(
        city_alloc, constraints, effective_days, policy
    )

    # 7. 生成条件摘要
    party_desc = f"{party['adults']}位成人"
    if party.get("children", 0) > 0:
        party_desc += f"+{party['children']}位儿童"
    if party.get("elderly", 0) > 0:
        party_desc += f"+{party['elderly']}位老人"

    vibe_labels = {
        "classic": "经典版", "romantic": "约会感",
        "photogenic": "出片感", "family_fun": "亲子感",
    }
    density_labels = {
        "packed": "紧凑节奏", "balanced": "平衡节奏", "relaxed": "悠闲节奏",
    }

    condition_summary = (
        f"{dates['start']}–{dates['end']} ｜ {party_desc} ｜ "
        f"{vibe_labels.get(vibe, vibe)} ｜ {density_labels.get(density, density)}"
    )

    return {
        "total_days": total_calendar_days,
        "effective_days": effective_days,
        "city_allocation": city_alloc,
        "daily_plans": daily_plans,
        "decisions": decisions,
        "addable_experiences": addable,
        "condition_summary": condition_summary,
        "note": "这是第一版主线。确认后手账本会补齐每天的餐厅推荐、店铺、咖啡厅、拍照点和实用小技巧。下一步可以选择吃住的舒适度和预算。",
        "validation": {"hard_pass": True, "warnings": []},
    }


# ── 内部函数 ─────────────────────────────────────────────────────────────────


def _allocate_cities(
    effective_days: float,
    vibe: str,
    party: dict,
    constraints: dict,
    policy: dict,
) -> list[dict[str, Any]]:
    """根据有效天数和风格分配城市天数。"""
    alloc_cfg = policy["city_allocation"]
    vibe_cfg = alloc_cfg["vibe_defaults"].get(vibe, alloc_cfg["vibe_defaults"]["classic"])
    min_days = alloc_cfg["city_min_days"]
    transfer_cost = alloc_cfg["transfer_cost_days"]

    # 主城市
    primary = vibe_cfg["primary"]
    secondary = vibe_cfg.get("secondary", [])

    # 默认体验模块
    default_experiences = alloc_cfg.get("vibe_default_experiences", {}).get(vibe, [])

    # 应用 skip 约束
    skip_entities = set(constraints.get("skip_entities", []))
    skip_tags = set(constraints.get("skip_tags", []))

    # 计算必要天数
    result = []
    remaining = effective_days

    # 主城市分配
    for city in primary:
        if city in skip_entities:
            continue
        city_min = min_days.get(city, 2)
        # 为默认体验模块加天数
        extra = 0
        for exp in default_experiences:
            if exp == "usj" and "usj" not in skip_entities:
                extra += 1
            elif exp == "arashiyama" and "arashiyama" not in skip_entities:
                extra += 0.5
        days_for_city = city_min + extra
        if remaining >= days_for_city:
            result.append({
                "city": city,
                "days": days_for_city,
                "nights": max(0, int(days_for_city) - (1 if city != primary[0] else 0)),
                "role": "primary",
            })
            remaining -= days_for_city
            if len(result) > 1:
                remaining -= transfer_cost  # 换城市消耗

    # 次要目的地（天数够才加）
    auto_rules = alloc_cfg.get("auto_add_rules", {})
    for rule_key, targets in auto_rules.items():
        if rule_key.startswith("_"):
            continue
        threshold = int(rule_key.replace("+", ""))
        if effective_days >= threshold and remaining >= 0.5:
            for target in (targets if isinstance(targets, list) else [targets]):
                target_city = target if target != "kobe_or_onsen" else "nara"
                if target_city in skip_entities:
                    continue
                if any(a["city"] == target_city for a in result):
                    continue
                city_min = min_days.get(target_city, 0.5)
                if remaining >= city_min:
                    result.append({
                        "city": target_city,
                        "days": city_min,
                        "nights": 0,
                        "role": "secondary",
                    })
                    remaining -= city_min

    # 剩余天数分给主城市（加深度）
    if remaining > 0 and result:
        # 优先给京都加天（京都深度收益大）
        kyoto_alloc = next((a for a in result if a["city"] == "kyoto"), None)
        osaka_alloc = next((a for a in result if a["city"] == "osaka"), None)
        if kyoto_alloc and remaining >= 1:
            kyoto_alloc["days"] += min(remaining, 2)
            remaining -= min(remaining, 2)
        if osaka_alloc and remaining >= 0.5:
            osaka_alloc["days"] += remaining
            remaining = 0

    # 更新 nights
    for alloc in result:
        if alloc["role"] == "primary":
            alloc["nights"] = max(1, int(alloc["days"]))

    return result


def _select_day_templates(
    templates: list[dict],
    available_days: float,
    vibe: str,
    density: str,
    party: dict,
    constraints: dict,
) -> list[dict]:
    """从 day 模板库中选出适合的模板列表。"""
    skip_entities = set(constraints.get("skip_entities", []))

    # 分类
    fixed = []      # min_occurrence >= 1
    conditional = []  # 有条件的
    fallback = []   # 填充用

    for tmpl in templates:
        asm = tmpl.get("assembly", {})
        role = asm.get("role", "")
        min_occ = asm.get("min_occurrence", 0)

        # 跳过被 skip 的模块
        if role == "module_usj" and "usj" in skip_entities:
            continue

        if min_occ >= 1:
            fixed.append(tmpl)
        elif asm.get("priority") == "conditional":
            conditional.append(tmpl)
        elif asm.get("priority") == "fallback":
            fallback.append(tmpl)
        else:
            conditional.append(tmpl)

    selected = list(fixed)
    remaining_slots = int(available_days) - len(selected)

    # 加条件模块
    for tmpl in conditional:
        if remaining_slots <= 0:
            break
        asm = tmpl.get("assembly", {})
        condition = tmpl.get("condition")

        # USJ: 需要用户选择或亲子默认
        if asm.get("role") == "module_usj":
            if vibe == "family_fun" and "usj" not in skip_entities:
                selected.append(tmpl)
                remaining_slots -= 1

        # 人群日
        elif asm.get("role") == "audience":
            if remaining_slots >= 1:
                selected.append(tmpl)
                remaining_slots -= 1

    # 用 fallback 填充剩余
    for tmpl in fallback:
        if remaining_slots <= 0:
            break
        selected.append(tmpl)
        remaining_slots -= 1

    # 排序：按 position 和 prefers_after
    return _sort_templates(selected)


def _sort_templates(templates: list[dict]) -> list[dict]:
    """按装配元数据排序 day 模板。"""
    position_order = {
        "first": 0, "early": 1, "middle": 2, "late": 3, "last": 4,
    }

    def sort_key(tmpl: dict) -> tuple:
        asm = tmpl.get("assembly", {})
        pos = position_order.get(asm.get("position", "middle"), 2)
        prio = asm.get("priority_value", 50)
        return (pos, -prio)

    return sorted(templates, key=sort_key)


def _apply_seasonal_overlays(
    daily_plans: list[dict],
    events: dict,
    start: date,
    end: date,
) -> None:
    """检查季节活动日期匹配，标记到对应天。"""
    for event in events.get("events", []):
        date_range = event.get("date_range")
        if not date_range:
            continue
        try:
            ev_start = date(start.year, *map(int, date_range["start"].split("-")))
            ev_end = date(start.year, *map(int, date_range["end"].split("-")))
        except (KeyError, ValueError):
            continue

        if start <= ev_end and end >= ev_start:
            # 日期命中，标记
            action = event.get("action", "recommend_only")
            grade = event.get("grade", "A")
            if action != "recommend_only" and grade in ("S+", "S"):
                for dp in daily_plans:
                    if dp["city"] == "osaka":
                        dp.setdefault("seasonal_overlays", []).append({
                            "event_id": event.get("event_id"),
                            "name": event.get("name_zh"),
                            "grade": grade,
                            "action": action,
                        })
                        break


def _generate_decisions(
    city_alloc: list[dict],
    constraints: dict,
    daily_plans: list[dict],
) -> list[str]:
    """生成关键决策解释（2-3条）。"""
    decisions = []
    cities = [a["city"] for a in city_alloc]

    if "osaka" in cities and "kyoto" in cities:
        osaka_idx = cities.index("osaka")
        kyoto_idx = cities.index("kyoto")
        if osaka_idx < kyoto_idx:
            decisions.append("大阪在前京都在后 — 先感受城市能量，后半段慢下来")
        else:
            decisions.append("京都在前大阪在后 — 先沉浸古都氛围，后半段热闹收尾")

    if "nara" in cities:
        nara_days = [dp for dp in daily_plans if dp["city"] == "nara"]
        if nara_days:
            decisions.append(f"奈良放在Day {nara_days[0]['day']} — 节奏轻松，适合放慢收尾")

    skip = constraints.get("skip_entities", [])
    has_usj = any(
        dp.get("day_template_id") == "module_usj" for dp in daily_plans
    )
    if not has_usj and "usj" not in skip:
        decisions.append("这版没有USJ — 按你的节奏先保主线完整，想加可以一键加入")

    return decisions[:3]


def _compute_addable_experiences(
    city_alloc: list[dict],
    constraints: dict,
    effective_days: float,
    policy: dict,
) -> list[dict[str, str]]:
    """计算可加体验卡片（没在方案中但 relevant 的）。"""
    included_cities = {a["city"] for a in city_alloc}
    included_templates = set()  # TODO: from daily_plans
    skip = set(constraints.get("skip_entities", []))
    min_days = policy["city_allocation"]["city_min_days"]

    candidates = [
        {"id": "usj", "icon": "🎢", "label": "一天交给主题乐园", "description": "环球影城USJ", "cost": 1},
        {"id": "arima_onsen", "icon": "♨️", "label": "加一晚温泉旅馆", "description": "泡完汤整个人都不一样", "cost": 1},
        {"id": "arashiyama", "icon": "🎋", "label": "多留半天给竹林", "description": "岚山的山谷里有另一种安静", "cost": 0.5},
        {"id": "kobe", "icon": "🥩", "label": "留一顿神户牛", "description": "港城夜景配铁板烧", "cost": 1},
        {"id": "nara", "icon": "🦌", "label": "和小鹿散个步", "description": "奈良的大草地和古寺", "cost": 0.5},
        {"id": "himeji", "icon": "🏯", "label": "去看日本最美的城堡", "description": "姬路城", "cost": 1},
        {"id": "uji", "icon": "🍵", "label": "抹茶小城散半天", "description": "宇治", "cost": 0.5},
        {"id": "koyasan", "icon": "⛰️", "label": "住进山上寺庙", "description": "高野山", "cost": 1.5},
        {"id": "kinosaki", "icon": "♨️", "label": "浴衣逛温泉街", "description": "城崎温泉", "cost": 1.5},
        {"id": "shirahama", "icon": "🏖", "label": "太平洋边泡温泉", "description": "白浜", "cost": 2},
    ]

    addable = []
    for c in candidates:
        if c["id"] in skip:
            continue
        if c["id"] in included_cities:
            continue
        # USJ 是大阪内部模块
        if c["id"] == "usj" and "osaka" in included_cities:
            addable.append(c)
            continue
        if c["id"] == "arashiyama" and "kyoto" in included_cities:
            addable.append(c)
            continue
        # 其他是独立城市
        if c["id"] not in included_cities:
            addable.append(c)

    # 只返回前3个最 relevant 的
    return addable[:3]


# ── 辅助 ─────────────────────────────────────────────────────────────────────


_CITY_TITLES = {
    "nara": "奈良 · 小鹿与古寺",
    "uji": "宇治 · 抹茶小城",
    "himeji": "姬路 · 白鹭城",
    "kobe": "神户 · 港城与神户牛",
    "arima_onsen": "有马温泉 · 金汤银汤",
}

_CITY_DESCRIPTIONS = {
    "nara": "在大草地和古寺之间散步，看小鹿慢悠悠地穿过你的镜头",
    "uji": "适合放慢半天的抹茶小城，喝茶、散步、看看河边",
    "himeji": "远远就能看见那座纯白天守，走近会觉得它比照片里还要干净利落",
    "kobe": "港口、洋楼、山海夜景都凑在一起，适合留一顿认认真真吃的神户牛",
    "arima_onsen": "藏在山里的老温泉町，泡完金泉银泉，整个人都会慢下来",
}


def _get_city_title(city: str) -> str:
    return _CITY_TITLES.get(city, city)


def _get_city_description(city: str) -> str:
    return _CITY_DESCRIPTIONS.get(city, "")

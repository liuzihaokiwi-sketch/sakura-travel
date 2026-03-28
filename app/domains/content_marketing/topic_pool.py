"""
topic_pool.py — 选题库管理

支持从 YAML 文件加载选题列表，同时内置季节/数据驱动的自动建议。
"""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ── 内置默认选题模板 ────────────────────────────────────────────────────────────
DEFAULT_TOPICS: list[dict[str, Any]] = [
    {
        "id": "city_guide_7d",
        "template": "city_guide",
        "title_tpl": "{circle_name}{days}天怎么玩？这{n}个安排决定了你的体验",
        "platform": ["xhs", "wechat"],
        "priority": 8,
        "tags": ["攻略", "路线"],
    },
    {
        "id": "food_ranking_local",
        "template": "food_ranking",
        "title_tpl": "{city}本地人也排队的{n}家{food_type}",
        "platform": ["xhs"],
        "priority": 9,
        "tags": ["美食", "排行"],
    },
    {
        "id": "budget_breakdown",
        "template": "budget_breakdown",
        "title_tpl": "{days}天{circle_name}旅行到底花多少钱？逐天拆给你看",
        "platform": ["xhs", "douyin"],
        "priority": 7,
        "tags": ["预算", "费用"],
    },
    {
        "id": "sakura_special",
        "template": "seasonal_special",
        "title_tpl": "2026{city}赏樱最佳时间+路线，一篇搞定",
        "platform": ["xhs", "douyin", "wechat"],
        "priority": 10,
        "season": "spring",
        "tags": ["樱花", "季节"],
    },
    {
        "id": "koyo_special",
        "template": "seasonal_special",
        "title_tpl": "{city}红叶见顷攻略，这几个地方千万不要错过",
        "platform": ["xhs", "douyin"],
        "priority": 10,
        "season": "autumn",
        "tags": ["红叶", "季节"],
    },
    {
        "id": "avoid_traps",
        "template": "avoid_traps",
        "title_tpl": "去{city}千万别踩的{n}个坑，踩过一次就够了",
        "platform": ["xhs"],
        "priority": 8,
        "tags": ["避雷", "注意事项"],
    },
    {
        "id": "hotel_vs",
        "template": "comparison",
        "title_tpl": "住{area_a} vs {area_b}，到底哪个方便？",
        "platform": ["xhs"],
        "priority": 6,
        "tags": ["住宿", "对比"],
    },
    {
        "id": "itinerary_reveal",
        "template": "city_guide",
        "title_tpl": "我帮客户做的{circle_name}{days}天手账长什么样",
        "platform": ["douyin"],
        "priority": 7,
        "tags": ["产品展示", "手账"],
    },
]

# 月份 → 季节映射
_MONTH_TO_SEASON: dict[int, str] = {
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
    12: "winter", 1: "winter", 2: "winter",
}


def load_topics(yaml_path: str | Path | None = None) -> list[dict[str, Any]]:
    """
    加载选题列表。
    - 如果提供 yaml_path，从文件加载（合并到默认列表）
    - 否则返回内置默认列表
    """
    topics = list(DEFAULT_TOPICS)
    if yaml_path and HAS_YAML:
        p = Path(yaml_path)
        if p.exists():
            with open(p, encoding="utf-8") as f:
                extra = yaml.safe_load(f) or []
            topics.extend(extra)
    return topics


def suggest_topics(
    current_date: datetime.date | None = None,
    entity_stats: dict[str, int] | None = None,
    platform: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    根据当前日期和实体库统计，自动建议优先级最高的选题。

    Args:
        current_date: 当前日期，默认 today
        entity_stats: {circle_name: entity_count} 各圈实体数量
        platform: 筛选平台，如 'xhs' / 'douyin' / None（不筛）
        limit: 返回条数

    Returns:
        推荐选题列表（含 reason 字段解释原因）
    """
    if current_date is None:
        current_date = datetime.date.today()

    season = _MONTH_TO_SEASON.get(current_date.month, "spring")
    # 赏樱季：2-4月，提前一个月建议
    boost_sakura = current_date.month in (2, 3, 4)
    # 红叶季：9-11月
    boost_koyo = current_date.month in (9, 10, 11)

    # 数据最丰富的城市圈
    richest_circle = None
    if entity_stats:
        richest_circle = max(entity_stats, key=lambda k: entity_stats[k])

    topics = load_topics()
    scored: list[tuple[float, dict[str, Any], str]] = []

    for t in topics:
        score = float(t.get("priority", 5))
        reason_parts: list[str] = []

        # 季节加权
        if t.get("season") == "spring" and boost_sakura:
            score += 3
            reason_parts.append("当前为赏樱旺季（2-4月），季节匹配度高")
        elif t.get("season") == "autumn" and boost_koyo:
            score += 3
            reason_parts.append("当前为红叶旺季（9-11月），季节匹配度高")
        elif t.get("season") and t["season"] != season:
            score -= 2  # 季节不匹配降权

        # 数据驱动：最丰富圈优先
        if richest_circle and richest_circle in t.get("title_tpl", ""):
            score += 1
            reason_parts.append(f"{richest_circle}圈实体数据最丰富，内容质量有保障")

        # 平台筛选
        if platform and platform not in t.get("platform", []):
            continue

        reason = "；".join(reason_parts) if reason_parts else "常规优先级"
        scored.append((score, t, reason))

    scored.sort(key=lambda x: -x[0])
    result = []
    for score, topic, reason in scored[:limit]:
        result.append({**topic, "score": score, "reason": reason})
    return result

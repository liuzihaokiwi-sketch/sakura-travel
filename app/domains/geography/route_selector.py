"""
线路选择器（Route Selector）

根据用户类型、天数、季节，从 P0 线路中筛选最合适的路线。
数据来源：data/route_region_binding_v1.json
设计原则：纯函数，无 I/O，可单测
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── P0 线路绑定数据 ─────────────────────────────────────────────────────────────

ROUTE_BINDING: list[dict[str, Any]] = [
    {
        "route_id": "T01", "route_name": "东京第一次城市线",
        "primary_regions": ["R01"], "extendable_regions": ["R02", "R03"],
        "suitable_user_types": ["first_time_couple", "first_time_family"],
        "min_days": 4, "max_days": 7, "best_seasons": ["spring", "autumn"],
    },
    {
        "route_id": "T02", "route_name": "东京购物审美线",
        "primary_regions": ["R01"], "extendable_regions": ["R02", "R03"],
        "suitable_user_types": ["repeat_couple", "repeat_solo"],
        "min_days": 3, "max_days": 5, "best_seasons": ["spring", "autumn", "winter"],
    },
    {
        "route_id": "F01", "route_name": "东京+箱根经典双城线",
        "primary_regions": ["R01", "R03"], "extendable_regions": ["R02", "R04"],
        "suitable_user_types": ["first_time_couple", "first_time_family", "onsen_focused"],
        "min_days": 5, "max_days": 7, "best_seasons": ["spring", "autumn", "winter"],
    },
    {
        "route_id": "F02", "route_name": "富士五湖出片温泉线",
        "primary_regions": ["R03"], "extendable_regions": ["R01", "R09"],
        "suitable_user_types": ["repeat_couple", "repeat_solo", "onsen_focused"],
        "min_days": 4, "max_days": 6, "best_seasons": ["spring", "autumn", "winter"],
    },
    {
        "route_id": "KS01", "route_name": "京都大阪奈良第一次日本线",
        "primary_regions": ["R05"], "extendable_regions": ["R08", "R10"],
        "suitable_user_types": ["first_time_couple", "first_time_family", "culture_deep"],
        "min_days": 5, "max_days": 7, "best_seasons": ["spring", "autumn"],
    },
    {
        "route_id": "KS02", "route_name": "京都慢节奏情侣线",
        "primary_regions": ["R05"], "extendable_regions": ["R08"],
        "suitable_user_types": ["repeat_couple", "culture_deep"],
        "min_days": 4, "max_days": 6, "best_seasons": ["spring", "autumn", "winter"],
    },
    {
        "route_id": "KS03", "route_name": "大阪基底吃喝购物线",
        "primary_regions": ["R05"], "extendable_regions": ["R08", "R10"],
        "suitable_user_types": ["first_time_couple", "repeat_couple", "repeat_solo"],
        "min_days": 4, "max_days": 6, "best_seasons": ["spring", "autumn", "winter"],
    },
    {
        "route_id": "H01", "route_name": "札幌小樽登别经典线",
        "primary_regions": ["R06"], "extendable_regions": [],
        "suitable_user_types": ["first_time_couple", "first_time_family", "onsen_focused"],
        "min_days": 4, "max_days": 6, "best_seasons": ["summer", "winter"],
    },
    {
        "route_id": "HK01", "route_name": "金泽+加贺温泉双人升级线",
        "primary_regions": ["R08"], "extendable_regions": ["R05", "R09"],
        "suitable_user_types": ["repeat_couple", "onsen_focused", "culture_deep"],
        "min_days": 4, "max_days": 6, "best_seasons": ["spring", "autumn", "winter"],
    },
    {
        "route_id": "HK02", "route_name": "金泽工艺茶道深度线",
        "primary_regions": ["R08"], "extendable_regions": ["R05", "R09"],
        "suitable_user_types": ["repeat_couple", "repeat_solo", "culture_deep"],
        "min_days": 3, "max_days": 5, "best_seasons": ["all"],
    },
]

# 区域季节指南（用于季节匹配）
REGION_BEST_SEASONS: dict[str, list[str]] = {
    "R01": ["spring", "autumn"],
    "R02": ["spring", "summer", "autumn"],
    "R03": ["all"],
    "R04": ["summer", "autumn", "winter"],
    "R05": ["spring", "autumn"],
    "R06": ["all"],
    "R07": ["summer", "winter"],
    "R08": ["all"],
    "R09": ["summer", "autumn", "winter"],
    "R10": ["spring", "autumn"],
    "R11": ["all"],
    "R12": ["all"],
}


# ── 输出结构 ──────────────────────────────────────────────────────────────────

@dataclass
class RouteMatch:
    route_id: str
    route_name: str
    primary_regions: list[str]
    extendable_regions: list[str]
    match_score: float          # 0-100，综合匹配得分
    season_match: bool          # 季节是否匹配
    day_fit: str                # "exact" | "within" | "short" | "long"
    reasons: list[str] = field(default_factory=list)


# ── 核心函数 ──────────────────────────────────────────────────────────────────

def _season_matches(route: dict, travel_season: str | None) -> bool:
    """判断线路的最佳季节是否包含用户出行季节。"""
    if not travel_season:
        return True  # 未指定季节，不过滤
    best = route.get("best_seasons", [])
    return "all" in best or travel_season in best


def _day_fit_label(duration_days: int, min_days: int, max_days: int) -> str:
    if duration_days < min_days:
        return "short"
    elif duration_days > max_days:
        return "long"
    elif duration_days == min_days or duration_days == max_days:
        return "exact"
    else:
        return "within"


def select_routes(
    user_type: str,
    duration_days: int,
    travel_season: str | None = None,
    preferred_regions: list[str] | None = None,
    top_n: int = 3,
) -> list[RouteMatch]:
    """
    从 P0 线路中筛选最合适的路线，按匹配分降序返回。

    Args:
        user_type:         用户类型（见 region_router.py）
        duration_days:     行程天数
        travel_season:     出行季节 "spring"|"summer"|"autumn"|"winter"|None
        preferred_regions: 优先匹配的区域列表（来自 region_router 输出）
        top_n:             返回前 N 条

    Returns:
        RouteMatch 列表，按 match_score 降序
    """
    results: list[RouteMatch] = []

    for route in ROUTE_BINDING:
        score = 0.0
        reasons: list[str] = []

        # 1. 用户类型匹配（最重要，40分）
        suitable = route["suitable_user_types"]
        if user_type in suitable:
            score += 40
            reasons.append(f"用户类型 {user_type} 完全匹配")
        else:
            # 部分相似也给分（如 first_time_* 系列互通）
            if user_type.startswith("first_time") and any(u.startswith("first_time") for u in suitable):
                score += 20
                reasons.append("用户类型相近（首次系列）")
            elif user_type.startswith("repeat") and any(u.startswith("repeat") for u in suitable):
                score += 20
                reasons.append("用户类型相近（二刷系列）")

        # 2. 天数适配（30分）
        fit = _day_fit_label(duration_days, route["min_days"], route["max_days"])
        if fit in ("exact", "within"):
            score += 30
            reasons.append(f"天数 {duration_days} 天完美适配（{route['min_days']}-{route['max_days']}天）")
        elif fit == "short":
            diff = route["min_days"] - duration_days
            score += max(0, 20 - diff * 5)
            reasons.append(f"天数偏少 {diff} 天，可压缩行程")
        else:  # long
            diff = duration_days - route["max_days"]
            score += max(0, 20 - diff * 3)
            reasons.append(f"天数偏多 {diff} 天，可补充延伸区域")

        # 3. 区域偏好匹配（20分）
        if preferred_regions:
            all_regions = set(route["primary_regions"] + route["extendable_regions"])
            overlap = set(preferred_regions) & all_regions
            primary_overlap = set(preferred_regions) & set(route["primary_regions"])
            if primary_overlap:
                score += 20
                reasons.append(f"首选区域命中：{', '.join(primary_overlap)}")
            elif overlap:
                score += 10
                reasons.append(f"延伸区域命中：{', '.join(overlap)}")

        # 4. 季节匹配（10分）
        season_ok = _season_matches(route, travel_season)
        if season_ok:
            score += 10
            if travel_season:
                reasons.append(f"{travel_season} 季节匹配")

        results.append(RouteMatch(
            route_id=route["route_id"],
            route_name=route["route_name"],
            primary_regions=route["primary_regions"],
            extendable_regions=route["extendable_regions"],
            match_score=round(score, 1),
            season_match=season_ok,
            day_fit=fit,
            reasons=reasons,
        ))

    results.sort(key=lambda r: r.match_score, reverse=True)
    return results[:top_n]


def recommend_routes_for_profile(
    user_type: str,
    duration_days: int,
    travel_season: str | None = None,
    preferred_regions: list[str] | None = None,
    top_n: int = 3,
) -> dict[str, Any]:
    """一站式接口，返回可直接序列化的字典。"""
    matches = select_routes(user_type, duration_days, travel_season, preferred_regions, top_n)
    return {
        "user_type": user_type,
        "duration_days": duration_days,
        "travel_season": travel_season,
        "routes": [
            {
                "route_id": m.route_id,
                "route_name": m.route_name,
                "match_score": m.match_score,
                "day_fit": m.day_fit,
                "season_match": m.season_match,
                "primary_regions": m.primary_regions,
                "reasons": m.reasons,
            }
            for m in matches
        ],
    }

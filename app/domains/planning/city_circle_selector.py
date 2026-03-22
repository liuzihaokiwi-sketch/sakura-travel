"""
city_circle_selector.py — 城市圈选择器（Phase 2 决策链第 1 步）

输入：TripProfile（标准化画像）
输出：selected_circle + rejected_circles[] + trace

评分维度（8 维）：
  1. must_go_fit      — 用户指定城市/景点与圈覆盖的匹配度
  2. airport_fit      — 到达/离开机场与圈友好机场的匹配
  3. arrival_shape_fit — 开口程/单程/红眼等对圈的适配
  4. season_fit        — 旅行季节与圈季节强度的匹配
  5. pace_fit          — 用户节奏偏好与圈天数区间的匹配
  6. daytrip_tolerance — 日归容忍度与圈扩展节点依赖度的匹配
  7. hotel_switch_tolerance — 换酒店容忍度与圈住法复杂度的匹配
  8. profile_fit       — 用户画像标签与圈适合画像的匹配
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import TripProfile
from app.db.models.city_circles import CityCircle

logger = logging.getLogger(__name__)


# ── 权重配置 ──────────────────────────────────────────────────────────────────

_WEIGHTS = {
    "must_go_fit": 0.25,
    "airport_fit": 0.15,
    "arrival_shape_fit": 0.05,
    "season_fit": 0.15,
    "pace_fit": 0.10,
    "daytrip_tolerance": 0.05,
    "hotel_switch_tolerance": 0.05,
    "profile_fit": 0.20,
}


# ── 输出结构 ──────────────────────────────────────────────────────────────────

@dataclass
class CircleExplain:
    """E4: 结构化 explain — 城市圈选择同步产出。"""
    why_selected: str = ""
    why_not_selected: str = ""
    expected_tradeoff: str = ""
    fallback_hint: str = ""


@dataclass
class CircleCandidate:
    circle_id: str
    name_zh: str
    total_score: float = 0.0
    breakdown: dict[str, float] = field(default_factory=dict)
    reject_reason: Optional[str] = None
    explain: CircleExplain = field(default_factory=CircleExplain)

    @property
    def rejected(self) -> bool:
        return self.reject_reason is not None


@dataclass
class CircleSelectionResult:
    selected: Optional[CircleCandidate] = None
    candidates: list[CircleCandidate] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)

    @property
    def selected_circle_id(self) -> Optional[str]:
        return self.selected.circle_id if self.selected else None


# ── 主入口 ────────────────────────────────────────────────────────────────────

async def select_city_circle(
    session: AsyncSession,
    profile: TripProfile,
) -> CircleSelectionResult:
    """
    根据用户画像从所有活跃城市圈中选择最优圈。

    硬约束先过滤（天数不在区间内 → 直接淘汰），
    然后 8 维加权打分，取最高分。
    """
    result = CircleSelectionResult()

    # 1. 加载所有活跃城市圈
    q = await session.execute(
        select(CityCircle).where(CityCircle.is_active == True)
    )
    circles = q.scalars().all()

    if not circles:
        result.trace.append("无可用城市圈")
        return result

    # 2. 提取画像信号
    signals = _extract_signals(profile)
    result.trace.append(f"signals: {signals}")

    # 3. 逐圈评分
    for circle in circles:
        candidate = _score_circle(circle, signals)
        result.candidates.append(candidate)

    # 4. 排序，选最高分
    valid = [c for c in result.candidates if not c.rejected]
    valid.sort(key=lambda c: c.total_score, reverse=True)

    if valid:
        result.selected = valid[0]
        result.trace.append(
            f"selected: {result.selected.circle_id} "
            f"(score={result.selected.total_score:.2f})"
        )
        # E4: explain for selected
        top_dims = sorted(result.selected.breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
        result.selected.explain = CircleExplain(
            why_selected=f"综合得分最高 ({result.selected.total_score:.2f})，"
                         f"优势: {', '.join(f'{k}={v:.2f}' for k,v in top_dims)}",
            expected_tradeoff="" if len(valid) == 1 else
                f"次选: {valid[1].name_zh} (score={valid[1].total_score:.2f})"
                if len(valid) > 1 else "",
        )
        # E4: explain for rejected
        for c in result.candidates:
            if c.rejected:
                c.explain = CircleExplain(
                    why_not_selected=c.reject_reason or "硬约束不满足",
                )
            elif c.circle_id != result.selected.circle_id:
                c.explain = CircleExplain(
                    why_not_selected=f"得分 {c.total_score:.2f} 低于选中圈",
                )
    else:
        result.trace.append("所有城市圈均被淘汰")

    return result


# ── 信号提取 ──────────────────────────────────────────────────────────────────

@dataclass
class _Signals:
    duration_days: int = 5
    city_codes: list[str] = field(default_factory=list)  # 用户指定的城市
    must_have_tags: list[str] = field(default_factory=list)
    avoid_tags: list[str] = field(default_factory=list)
    party_type: str = "couple"
    budget_level: str = "mid"
    arrival_airport: str = ""
    departure_airport: str = ""
    arrival_shape: str = "same_city"
    travel_month: Optional[int] = None
    pace: str = "moderate"
    daytrip_tolerance: str = "medium"
    hotel_switch_tolerance: str = "medium"


def _extract_signals(profile: TripProfile) -> _Signals:
    """从 TripProfile 提取选圈所需信号。"""
    s = _Signals()
    s.duration_days = profile.duration_days or 5
    s.city_codes = [c.get("city_code", "") for c in (profile.cities or []) if isinstance(c, dict)]
    s.must_have_tags = profile.must_have_tags or []
    s.avoid_tags = profile.avoid_tags or []
    s.party_type = profile.party_type or "couple"
    s.budget_level = profile.budget_level or "mid"
    s.arrival_airport = profile.arrival_airport or ""
    s.departure_airport = profile.departure_airport or ""
    s.arrival_shape = profile.arrival_shape or "same_city"
    s.pace = profile.pace or "moderate"
    s.daytrip_tolerance = profile.daytrip_tolerance or "medium"
    s.hotel_switch_tolerance = profile.hotel_switch_tolerance or "medium"

    # 从旅行日期推断月份
    dates = profile.travel_dates or {}
    start_str = dates.get("start", "")
    if start_str and len(start_str) >= 7:
        try:
            s.travel_month = int(start_str[5:7])
        except ValueError:
            pass

    return s


# ── 评分逻辑 ──────────────────────────────────────────────────────────────────

def _score_circle(circle: CityCircle, signals: _Signals) -> CircleCandidate:
    """对单个城市圈打分。"""
    candidate = CircleCandidate(circle_id=circle.circle_id, name_zh=circle.name_zh)

    # 硬约束：天数不在区间内
    if signals.duration_days < circle.min_days:
        candidate.reject_reason = f"天数 {signals.duration_days} < 最小 {circle.min_days}"
        return candidate
    if signals.duration_days > circle.max_days:
        candidate.reject_reason = f"天数 {signals.duration_days} > 最大 {circle.max_days}"
        return candidate

    bd = {}
    all_circle_cities = set(circle.base_city_codes or []) | set(circle.extension_city_codes or [])

    # 1. must_go_fit: 用户指定城市是否在圈内
    if signals.city_codes:
        matched = sum(1 for c in signals.city_codes if c in all_circle_cities)
        bd["must_go_fit"] = matched / len(signals.city_codes) if signals.city_codes else 0.5
    else:
        bd["must_go_fit"] = 0.5  # 没指定城市，中性分

    # 2. airport_fit: 机场匹配
    friendly = set(circle.friendly_airports or [])
    airport_score = 0.5
    if signals.arrival_airport or signals.departure_airport:
        matches = 0
        checks = 0
        if signals.arrival_airport:
            checks += 1
            if signals.arrival_airport.upper() in friendly:
                matches += 1
        if signals.departure_airport:
            checks += 1
            if signals.departure_airport.upper() in friendly:
                matches += 1
        airport_score = matches / checks if checks else 0.5
    bd["airport_fit"] = airport_score

    # 3. arrival_shape_fit: 开口程适配
    shape_score = 0.7  # 默认中性偏好
    if signals.arrival_shape == "open_jaw":
        # 开口程需要至少有两个不同城市作为 base
        if len(circle.base_city_codes or []) >= 2:
            shape_score = 1.0
        else:
            shape_score = 0.3
    elif signals.arrival_shape == "same_city":
        shape_score = 0.8
    bd["arrival_shape_fit"] = shape_score

    # 4. season_fit: 季节匹配
    season_score = 0.6  # 默认
    if signals.travel_month and circle.season_strength:
        month_to_season = {
            1: "winter", 2: "winter", 3: "spring", 4: "spring",
            5: "spring", 6: "summer", 7: "summer", 8: "summer",
            9: "autumn", 10: "autumn", 11: "autumn", 12: "winter",
        }
        season = month_to_season.get(signals.travel_month, "")
        season_score = circle.season_strength.get(season, 0.5)
    bd["season_fit"] = season_score

    # 5. pace_fit: 节奏与天数区间的匹配
    days = signals.duration_days
    rec = circle.recommended_days_range or ""
    pace_score = 0.6
    if rec and "-" in rec:
        try:
            lo, hi = int(rec.split("-")[0]), int(rec.split("-")[1])
            if lo <= days <= hi:
                pace_score = 1.0
            elif days < lo:
                pace_score = max(0.2, 1.0 - (lo - days) * 0.2)
            else:
                pace_score = max(0.2, 1.0 - (days - hi) * 0.15)
        except ValueError:
            pass

    # pace 偏好修正
    if signals.pace == "relaxed" and days < (circle.min_days + 1):
        pace_score *= 0.7
    elif signals.pace == "packed" and days > (circle.max_days - 1):
        pace_score *= 0.8
    bd["pace_fit"] = min(1.0, pace_score)

    # 6. daytrip_tolerance
    ext_count = len(circle.extension_city_codes or [])
    dt_score = 0.7
    if signals.daytrip_tolerance == "low" and ext_count > 2:
        dt_score = 0.4  # 低容忍度 + 很多扩展节点 = 不太适合
    elif signals.daytrip_tolerance == "high":
        dt_score = 0.9
    bd["daytrip_tolerance"] = dt_score

    # 7. hotel_switch_tolerance
    # 圈的 base_city_codes 数量暗示换酒店需求
    base_count = len(circle.base_city_codes or [])
    hs_score = 0.7
    if signals.hotel_switch_tolerance == "low" and base_count > 1:
        hs_score = 0.4
    elif signals.hotel_switch_tolerance == "high" and base_count > 1:
        hs_score = 0.9
    elif base_count == 1:
        hs_score = 0.85  # 单基点对任何容忍度都友好
    bd["hotel_switch_tolerance"] = hs_score

    # 8. profile_fit: 画像标签匹配
    fit = circle.fit_profiles or {}
    fit_party_types = fit.get("party_types", [])
    fit_themes = [t.lower() for t in fit.get("themes", [])]

    profile_score = 0.5
    party_match = 1.0 if signals.party_type in fit_party_types else 0.4
    # 标签匹配
    user_tags = set(t.lower() for t in signals.must_have_tags)
    theme_match = 0.5
    if user_tags and fit_themes:
        overlap = len(user_tags & set(fit_themes))
        theme_match = min(1.0, overlap / max(1, len(user_tags)) + 0.3)
    elif not user_tags:
        theme_match = 0.5
    profile_score = party_match * 0.5 + theme_match * 0.5
    bd["profile_fit"] = profile_score

    # 加权总分
    total = sum(bd[k] * _WEIGHTS[k] for k in _WEIGHTS)
    candidate.total_score = round(total, 4)
    candidate.breakdown = bd

    return candidate

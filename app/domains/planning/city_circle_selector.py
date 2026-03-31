from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import TripProfile
from app.db.models.city_circles import CityCircle
from app.domains.planning.config_resolver import ResolvedConfig
from app.domains.planning.policy_resolver import ResolvedPolicySet, resolve_policy_set

logger = logging.getLogger(__name__)


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


@dataclass
class CircleExplain:
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
    policy_summary: dict[str, str] = field(default_factory=dict)
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


@dataclass
class _Signals:
    duration_days: int = 5
    city_codes: list[str] = field(default_factory=list)
    requested_city_circle: str = ""
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


async def select_city_circle(
    session: AsyncSession,
    profile: TripProfile,
    resolved_config: ResolvedConfig | None = None,
) -> CircleSelectionResult:
    result = CircleSelectionResult()
    q = await session.execute(select(CityCircle).where(CityCircle.is_active == True))
    circles = q.scalars().all()

    if not circles:
        result.trace.append("no_active_city_circles")
        return result

    signals = _extract_signals(profile)
    result.trace.append(f"signals: {signals}")

    # 批量检查每个圈的数据完整性（entity_roles + clusters 数量）
    # 空壳圈（无绑定实体/簇）不应被选中，否则下游 pipeline 全部失败
    from app.db.models.city_circles import CircleEntityRole, ActivityCluster
    from sqlalchemy import func
    _role_counts: dict[str, int] = {}
    _cluster_counts: dict[str, int] = {}
    try:
        _rc_q = await session.execute(
            select(CircleEntityRole.circle_id, func.count())
            .group_by(CircleEntityRole.circle_id)
        )
        for cid, cnt in _rc_q.all():
            _role_counts[cid] = cnt
        _cc_q = await session.execute(
            select(ActivityCluster.circle_id, func.count())
            .where(ActivityCluster.is_active == True)
            .group_by(ActivityCluster.circle_id)
        )
        for cid, cnt in _cc_q.all():
            _cluster_counts[cid] = cnt
    except Exception as exc:
        logger.warning("circle data integrity check failed: %s", exc)

    for circle in circles:
        circle_cfg = resolved_config or ResolvedConfig()
        policy = resolve_policy_set(circle.circle_id, circle=circle, resolved_config=circle_cfg)
        candidate = _score_circle(circle, signals, policy)

        # 数据完整性门控：无 entity_roles 或无 clusters 的圈直接拒绝
        role_count = _role_counts.get(circle.circle_id, 0)
        cluster_count = _cluster_counts.get(circle.circle_id, 0)
        if role_count == 0 or cluster_count == 0:
            candidate.reject_reason = (
                f"empty_circle: roles={role_count}, clusters={cluster_count}"
            )
            candidate.total_score = 0.0
            result.trace.append(
                f"REJECT {circle.circle_id}: no data (roles={role_count}, clusters={cluster_count})"
            )

        result.candidates.append(candidate)
        result.trace.append(
            "candidate: "
            f"{candidate.circle_id} score={candidate.total_score:.3f} "
            f"routing={candidate.policy_summary.get('routing_mode')} "
            f"mobility={candidate.policy_summary.get('primary_mode')}"
        )

    valid = [c for c in result.candidates if not c.rejected]
    valid.sort(key=lambda c: c.total_score, reverse=True)

    if signals.requested_city_circle:
        requested = next((c for c in valid if c.circle_id == signals.requested_city_circle), None)
        if requested:
            result.selected = requested
            result.trace.append(f"requested_city_circle respected: {requested.circle_id}")
        else:
            result.trace.append(f"requested_city_circle unavailable: {signals.requested_city_circle}")

    if valid and result.selected is None:
        result.selected = valid[0]

    if result.selected:
        result.trace.append(
            f"selected: {result.selected.circle_id} (score={result.selected.total_score:.2f})"
        )
        top_dims = sorted(result.selected.breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
        selected_policy = (
            f"{result.selected.policy_summary.get('routing_mode', 'default')}/"
            f"{result.selected.policy_summary.get('primary_mode', 'default')}"
        )
        result.selected.explain = CircleExplain(
            why_selected=(
                f"score={result.selected.total_score:.2f}; "
                f"top={', '.join(f'{k}={v:.2f}' for k, v in top_dims)}; "
                f"policy={selected_policy}"
            ),
            expected_tradeoff=(
                ""
                if len(valid) <= 1
                else f"runner_up={valid[1].name_zh}({valid[1].total_score:.2f})"
            ),
        )
        for c in result.candidates:
            if c.rejected:
                c.explain = CircleExplain(why_not_selected=c.reject_reason or "rejected")
            elif c.circle_id != result.selected.circle_id:
                rejected_policy = (
                    f"{c.policy_summary.get('routing_mode', 'default')}/"
                    f"{c.policy_summary.get('primary_mode', 'default')}"
                )
                c.explain = CircleExplain(
                    why_not_selected=f"score={c.total_score:.2f}; policy={rejected_policy}"
                )
    else:
        result.trace.append("all_city_circles_rejected")

    return result


def _extract_signals(profile: TripProfile) -> _Signals:
    s = _Signals()
    s.duration_days = profile.duration_days or 5
    s.city_codes = [c.get("city_code", "") for c in (profile.cities or []) if isinstance(c, dict)]
    s.requested_city_circle = getattr(profile, "requested_city_circle", None) or ""
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

    dates = profile.travel_dates or {}
    start_str = dates.get("start", "")
    if start_str and len(start_str) >= 7:
        try:
            s.travel_month = int(start_str[5:7])
        except ValueError:
            pass

    return s


def _score_circle(circle: CityCircle, signals: _Signals, policy: ResolvedPolicySet) -> CircleCandidate:
    candidate = CircleCandidate(circle_id=circle.circle_id, name_zh=circle.name_zh)
    candidate.policy_summary = {
        "primary_mode": policy.mobility_policy.primary_mode,
        "routing_mode": policy.routing_style_policy.routing_mode,
        "seasonality_mode": policy.climate_and_season_policy.seasonality_mode,
    }

    # 天数偏离推荐范围的 penalty（在评分计算完成后应用）
    _days_penalty = 0.0
    _days_tradeoff = ""
    if signals.duration_days < circle.min_days:
        _days_penalty = min(0.5, (circle.min_days - signals.duration_days) * 0.15)
        _days_tradeoff = f"行程偏短({signals.duration_days}天)，建议 {circle.min_days}+ 天更充裕"
    elif signals.duration_days > circle.max_days:
        _days_penalty = min(0.5, (signals.duration_days - circle.max_days) * 0.15)
        _days_tradeoff = f"行程偏长({signals.duration_days}天)，{circle.max_days} 天可覆盖核心"

    bd: dict[str, float] = {}
    all_circle_cities = set(circle.base_city_codes or []) | set(circle.extension_city_codes or [])

    if signals.city_codes:
        matched = sum(1 for city_code in signals.city_codes if city_code in all_circle_cities)
        bd["must_go_fit"] = matched / len(signals.city_codes)
    else:
        bd["must_go_fit"] = 0.5

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
    if policy.mobility_policy.airport_access_style == "airport_buffer_first":
        airport_score = min(1.0, airport_score + 0.10)
    elif policy.mobility_policy.airport_access_style == "multi_gateway":
        airport_score = min(1.0, airport_score + 0.05)
    bd["airport_fit"] = airport_score

    shape_score = 0.7
    if signals.arrival_shape == "open_jaw":
        shape_score = 1.0 if len(circle.base_city_codes or []) >= 2 else 0.3
    elif signals.arrival_shape == "same_city":
        shape_score = 0.8
    bd["arrival_shape_fit"] = shape_score

    season_score = 0.6
    if signals.travel_month and circle.season_strength:
        month_to_season = {
            1: "winter", 2: "winter", 3: "spring", 4: "spring",
            5: "spring", 6: "summer", 7: "summer", 8: "summer",
            9: "autumn", 10: "autumn", 11: "autumn", 12: "winter",
        }
        season = month_to_season.get(signals.travel_month, "")
        season_score = circle.season_strength.get(season, 0.5)
    if signals.travel_month in policy.climate_and_season_policy.high_risk_months:
        season_score = max(0.2, season_score + policy.climate_and_season_policy.season_fit_bias - 0.05)
    else:
        season_score = min(1.0, season_score + policy.climate_and_season_policy.season_fit_bias)
    bd["season_fit"] = season_score

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
    if signals.pace == "relaxed" and days < (circle.min_days + 1):
        pace_score *= 0.7
    elif signals.pace == "packed" and days > (circle.max_days - 1):
        pace_score *= 0.8
    if policy.routing_style_policy.prefer_single_base and len(circle.base_city_codes or []) <= 1:
        pace_score = min(1.0, pace_score + 0.08)
    if policy.routing_style_policy.routing_mode in {"linear_road_trip", "low_density_blocks"} and days <= max(circle.min_days + 1, 4):
        pace_score = max(0.2, pace_score - 0.08)
    bd["pace_fit"] = min(1.0, pace_score)

    ext_count = len(circle.extension_city_codes or [])
    dt_score = 0.7
    if signals.daytrip_tolerance == "low" and ext_count > 2:
        dt_score = 0.4
    elif signals.daytrip_tolerance == "high":
        dt_score = 0.9
    if policy.mobility_policy.cross_city_tolerance == "low" and ext_count > 1:
        dt_score = max(0.2, dt_score - 0.2)
    elif policy.mobility_policy.cross_city_tolerance in {"medium_high", "high"}:
        dt_score = min(1.0, dt_score + 0.08)
    bd["daytrip_tolerance"] = dt_score

    base_count = len(circle.base_city_codes or [])
    hs_score = 0.7
    if signals.hotel_switch_tolerance == "low" and base_count > 1:
        hs_score = 0.4
    elif signals.hotel_switch_tolerance == "high" and base_count > 1:
        hs_score = 0.9
    elif base_count == 1:
        hs_score = 0.85
    bd["hotel_switch_tolerance"] = hs_score

    fit = circle.fit_profiles or {}
    fit_party_types = fit.get("party_types", [])
    fit_themes = [theme.lower() for theme in fit.get("themes", [])]
    party_match = 1.0 if signals.party_type in fit_party_types else 0.4
    user_tags = set(tag.lower() for tag in signals.must_have_tags)
    theme_match = 0.5
    if user_tags and fit_themes:
        overlap = len(user_tags & set(fit_themes))
        theme_match = min(1.0, overlap / max(1, len(user_tags)) + 0.3)
    profile_score = party_match * 0.5 + theme_match * 0.5
    bd["profile_fit"] = profile_score

    total = sum(bd[key] * _WEIGHTS[key] for key in _WEIGHTS)
    total += policy.city_circle_profile.selection_bias
    total -= policy.routing_style_policy.backtrack_penalty_bias * max(0, ext_count - 1)
    candidate.total_score = round(total, 4)
    candidate.breakdown = bd

    # 天数偏离推荐范围：降分但不拒绝
    # 3天去北海道有3天的玩法，周末也可以去 — 天数是推荐不是限制
    if _days_penalty > 0:
        candidate.total_score = round(candidate.total_score * (1.0 - _days_penalty), 4)
        candidate.explain = CircleExplain(expected_tradeoff=_days_tradeoff)

    return candidate

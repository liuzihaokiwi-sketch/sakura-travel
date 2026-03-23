"""
hotel_base_builder.py — 酒店基点策略生成器（Phase 2 决策链第 3 步）

输入：
  - selected_majors（已选主要活动列表）
  - circle_id
  - TripProfile（含 flight_info, hotel_switch_tolerance, last_flight_time）
  - HotelStrategyPreset[]（圈级住法预设）

输出：
  - 选中的住法策略
  - 每个 base 的明细（base_city, nights, served_majors, switch_cost）
  - last_night_safe 检查结果
  - trace
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import TripProfile
from app.db.models.city_circles import HotelStrategyPreset

logger = logging.getLogger(__name__)


# ── 输出结构 ──────────────────────────────────────────────────────────────────

@dataclass
class HotelBase:
    base_city: str
    area: str = ""
    nights: int = 1
    served_cluster_ids: list[str] = field(default_factory=list)
    switch_cost_minutes: int = 0
    switch_reason_code: str = ""


@dataclass
class HotelExplain:
    """E4: 结构化 explain — 酒店策略同步产出。"""
    why_selected: str = ""
    expected_tradeoff: str = ""
    fallback_hint: str = ""
    coverage_detail: str = ""


@dataclass
class HotelStrategyResult:
    preset_id: Optional[int] = None
    preset_name: str = ""
    bases: list[HotelBase] = field(default_factory=list)
    total_nights: int = 0
    switch_count: int = 0
    last_night_safe: bool = True
    last_night_airport_minutes: Optional[int] = None
    override_allowed: bool = True
    trace: list[str] = field(default_factory=list)
    explain: HotelExplain = field(default_factory=HotelExplain)


# ── 主入口 ────────────────────────────────────────────────────────────────────

async def build_hotel_strategy(
    session: AsyncSession,
    circle_id: str,
    profile: TripProfile,
    selected_cluster_ids: list[str],
) -> HotelStrategyResult:
    """
    从圈级酒店预设中选择最优住法。

    评分逻辑：
    1. 天数匹配 — preset 的 min/max_days 必须包含 duration_days
    2. 画像匹配 — party_type + budget_level
    3. 主要活动覆盖 — preset 的 bases 能覆盖多少已选主要活动
    4. 换酒店容忍度 — 与 switch_count 的匹配
    5. 最后一晚安全 — last_night_airport_minutes vs last_flight_time
    """
    result = HotelStrategyResult()
    days = profile.duration_days or 5

    # 1. 加载圈级住法预设
    q = await session.execute(
        select(HotelStrategyPreset).where(
            and_(
                HotelStrategyPreset.circle_id == circle_id,
                HotelStrategyPreset.is_active == True,
            )
        ).order_by(HotelStrategyPreset.priority)
    )
    presets = q.scalars().all()

    if not presets:
        result.trace.append(f"circle={circle_id} 无酒店住法预设，使用默认单基点")
        return _build_default_strategy(profile, result)

    # 2. 评分选优
    best_score = -1.0
    best_preset: Optional[HotelStrategyPreset] = None

    for preset in presets:
        score = _score_preset(preset, profile, selected_cluster_ids, days)
        result.trace.append(
            f"preset={preset.name_zh} score={score:.2f} "
            f"days={preset.min_days}-{preset.max_days} switches={preset.switch_count}"
        )
        if score > best_score:
            best_score = score
            best_preset = preset

    if best_preset is None:
        result.trace.append("无匹配预设，使用默认策略")
        return _build_default_strategy(profile, result)

    # 3. 构建结果
    result.preset_id = best_preset.preset_id
    result.preset_name = best_preset.name_zh
    result.switch_count = best_preset.switch_count
    result.last_night_airport_minutes = best_preset.last_night_airport_minutes

    # ── 解析 nights_range 并根据实际天数分配 ──
    total_avail = days - 1  # 总夜数 = 天数 - 1
    raw_bases = best_preset.bases or []
    base_ranges = []
    for base_data in raw_bases:
        nr = base_data.get("nights_range", "")
        n_fixed = base_data.get("nights")
        if nr and isinstance(nr, str) and "-" in nr:
            lo, hi = nr.split("-", 1)
            base_ranges.append((base_data, int(lo), int(hi)))
        elif n_fixed:
            base_ranges.append((base_data, int(n_fixed), int(n_fixed)))
        else:
            base_ranges.append((base_data, 1, total_avail))

    # 按比例分配 nights（min 优先占位，剩余按 max 上限分配）
    min_total = sum(lo for _, lo, _ in base_ranges)
    remainder = max(0, total_avail - min_total)
    for base_data, lo, hi in base_ranges:
        extra = min(hi - lo, remainder) if remainder > 0 else 0
        nights = lo + extra
        remainder -= extra
        base = HotelBase(
            base_city=base_data.get("base_city", ""),
            area=base_data.get("area", ""),
            nights=nights,
            served_cluster_ids=base_data.get("served_cluster_ids", []),
        )
        result.bases.append(base)
        result.total_nights += base.nights

    # 兜底：如果仍不足，补给最后一个 base
    if result.total_nights < total_avail:
        diff = total_avail - result.total_nights
        if result.bases:
            result.bases[-1].nights += diff
            result.total_nights += diff

    # 4. 最后一晚安全检查
    result.last_night_safe = _check_last_night_safety(
        best_preset.last_night_airport_minutes,
        profile.last_flight_time,
    )
    if not result.last_night_safe:
        result.trace.append(
            f"WARNING: 最后一晚到机场 {best_preset.last_night_airport_minutes}min, "
            f"航班 {profile.last_flight_time} — 安全余量不足"
        )

    # 5. 标记 switch reason
    for i, base in enumerate(result.bases):
        if i > 0:
            base.switch_reason_code = "area_change"
            base.switch_cost_minutes = best_preset.switch_cost_minutes // max(1, result.switch_count)

    result.trace.append(
        f"selected: {result.preset_name}, "
        f"{len(result.bases)} bases, {result.switch_count} switches, "
        f"last_night_safe={result.last_night_safe}"
    )

    # E4: explain
    base_summary = " → ".join(f"{b.base_city}({b.nights}晚)" for b in result.bases)
    result.explain = HotelExplain(
        why_selected=f"选用 [{result.preset_name}]: {base_summary}",
        expected_tradeoff=f"换酒店 {result.switch_count} 次"
                          + ("" if result.last_night_safe
                             else f", ⚠️最后一晚到机场 {result.last_night_airport_minutes}min 余量不足"),
        coverage_detail=f"共覆盖 {sum(len(b.served_cluster_ids) for b in result.bases)} 个活动簇",
        fallback_hint="可人工 override 住法" if result.override_allowed else "",
    )

    return result


# ── 评分 ──────────────────────────────────────────────────────────────────────

def _score_preset(
    preset: HotelStrategyPreset,
    profile: TripProfile,
    selected_cluster_ids: list[str],
    days: int,
) -> float:
    """对单个住法预设打分。"""
    score = 0.0

    # 1. 天数匹配（硬约束，不匹配直接 -100）
    if days < preset.min_days or days > preset.max_days:
        return -100.0

    # 2. 画像匹配（30%）
    party = profile.party_type or ""
    budget = profile.budget_level or ""
    party_match = 1.0 if party in (preset.fit_party_types or []) else 0.3
    budget_match = 1.0 if budget in (preset.fit_budget_levels or []) else 0.4
    score += (party_match * 0.5 + budget_match * 0.5) * 30

    # 3. 主要活动覆盖（40%）
    if selected_cluster_ids:
        all_served = set()
        for base_data in (preset.bases or []):
            all_served.update(base_data.get("served_cluster_ids", []))
        covered = len(set(selected_cluster_ids) & all_served)
        coverage = covered / len(selected_cluster_ids)
        score += coverage * 40

    # 4. 换酒店容忍度匹配（20%）
    tolerance = (profile.hotel_switch_tolerance or "medium").lower()
    switch = preset.switch_count or 0
    if tolerance == "low":
        switch_score = max(0, 1.0 - switch * 0.5)
    elif tolerance == "high":
        switch_score = 0.8
    else:
        switch_score = max(0, 1.0 - switch * 0.3)
    score += switch_score * 20

    # 5. 多城市契合度（新增 15%）
    # 当 profile.cities 包含多个城市时，bases 城市数量与之匹配的 preset 加分
    profile_cities = {c.get("city_code", "") for c in (getattr(profile, "cities", None) or [])}
    preset_base_cities = {b.get("base_city", "") for b in (preset.bases or [])}
    if len(profile_cities) >= 2:
        city_overlap = len(profile_cities & preset_base_cities) / max(len(profile_cities), 1)
        score += city_overlap * 15
    else:
        # 单城市行程：单基点 preset 加分
        if len(preset_base_cities) == 1 and preset_base_cities & profile_cities:
            score += 15

    # 6. 优先级 bonus（10%）
    priority_bonus = max(0, (100 - (preset.priority or 50)) / 100)
    score += priority_bonus * 10

    return score


# ── 最后一晚安全检查 ──────────────────────────────────────────────────────────

def _check_last_night_safety(
    airport_minutes: Optional[int],
    flight_time: Optional[str],
) -> bool:
    """
    检查最后一晚到机场的时间是否安全。

    规则：到机场时间 + 3 小时 checkin 缓冲 < 航班时间
    """
    if not airport_minutes or not flight_time:
        return True  # 数据不足，默认安全

    try:
        parts = flight_time.split(":")
        flight_hour = int(parts[0])
        flight_min = int(parts[1]) if len(parts) > 1 else 0
        flight_total_min = flight_hour * 60 + flight_min

        # 需要在航班前至少 3 小时到机场
        needed_departure_min = flight_total_min - 180  # 3 小时
        # 假设早上 8 点出发
        departure_time_min = 8 * 60 + airport_minutes

        return departure_time_min <= needed_departure_min
    except (ValueError, TypeError):
        return True


# ── 默认策略 ──────────────────────────────────────────────────────────────────

def _build_default_strategy(
    profile: TripProfile,
    result: HotelStrategyResult,
) -> HotelStrategyResult:
    """无预设时的默认单基点策略。"""
    days = profile.duration_days or 5
    city_codes = [c.get("city_code", "") for c in (profile.cities or []) if isinstance(c, dict)]
    base_city = city_codes[0] if city_codes else "unknown"

    result.bases = [
        HotelBase(
            base_city=base_city,
            nights=days - 1,
        ),
    ]
    result.total_nights = days - 1
    result.switch_count = 0
    result.last_night_safe = True
    result.trace.append(f"default: single base at {base_city}, {days - 1} nights")
    result.explain = HotelExplain(
        why_selected=f"无预设匹配，使用默认单基点: {base_city} ({days - 1} 晚)",
        expected_tradeoff="单基点策略，不换酒店",
    )
    return result

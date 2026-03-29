from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from app.domains.planning.display_registry import display_area as _display_area
from app.domains.planning.display_registry import display_city as _display_city
from app.domains.planning.display_registry import display_corridor as _display_corridor

if TYPE_CHECKING:
    from app.domains.planning.constraint_compiler import PlanningConstraints
    from app.domains.planning.policy_resolver import ResolvedPolicySet

logger = logging.getLogger(__name__)


@dataclass
class MealWindow:
    meal_type: str
    earliest: str = ""
    latest: str = ""
    style_hint: str = ""


@dataclass
class DayFrame:
    day_index: int
    day_type: str = "normal"
    sleep_base: str = ""
    primary_corridor: str = ""
    secondary_corridor: Optional[str] = None
    main_driver: Optional[str] = None
    main_driver_name: str = ""
    day_capacity_units: float = 1.0
    transfer_budget_minutes: int = 120
    meal_windows: list[MealWindow] = field(default_factory=list)
    must_keep_ids: list[str] = field(default_factory=list)
    cut_order: list[str] = field(default_factory=list)
    fallback_corridor: Optional[str] = None
    intensity: str = "balanced"
    title_hint: str = ""
    notes: list[str] = field(default_factory=list)
    daily_capacity_minutes: int = 480
    activity_load_minutes: int = 0
    transit_minutes: int = 120
    slack_minutes: int = 90
    remaining_minutes: int = 0
    day_label: str = "full_day"
    day_mode: str = ""
    day_mode_boosted: list[str] = field(default_factory=list)
    day_mode_suppressed: list[str] = field(default_factory=list)
    booking_status: str = "none"
    booking_explain: str = ""
    booking_alerts: list[dict] = field(default_factory=list)


@dataclass
class SkeletonResult:
    frames: list[DayFrame] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    booking_alerts: list[dict] = field(default_factory=list)
    degraded_majors: list[str] = field(default_factory=list)
    policy_summary: dict[str, object] = field(default_factory=dict)


class _MajorInfo:
    cluster_id: str
    name_zh: str
    capacity_units: float
    default_duration: str
    primary_corridor: str
    activity_load_minutes: int
    reservation_required: bool
    reservation_pressure: str
    booking_hint: str
    anchor_entity_ids: list[str]


class _HotelBaseInfo:
    base_city: str
    area: str
    nights: int
    served_cluster_ids: list[str]


_THEME_PARK_KEYWORDS = {"usj", "themepark", "theme_park", "universal", "disney", "disneyland", "disneysea"}
_DEPARTURE_BLOCKED_KEYWORDS = {"night", "nightlife", "food_night", "theme_park", "bar"}

# ── Pace 参数（从 data/seed/pace_config.json 加载，支持运营调参） ──
def _load_pace_config() -> dict:
    """加载 pace 配置，失败时返回空 dict（使用内联默认值）。"""
    import json
    from pathlib import Path
    cfg_path = Path(__file__).resolve().parents[3] / "data" / "seed" / "pace_config.json"
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

_PACE_CFG = _load_pace_config()

_WAKE_BREAKFAST = {
    k: tuple(v) for k, v in _PACE_CFG.get("wake_breakfast", {
        "early": ["07:00", "08:00"],
        "normal": ["08:00", "09:30"],
        "late": ["09:00", "10:30"],
    }).items()
}
_LUNCH_WINDOW = tuple(_PACE_CFG.get("lunch_window", ["11:30", "13:30"]))
_DINNER_WINDOW = tuple(_PACE_CFG.get("dinner_window", ["17:30", "20:00"]))
_PACE_DAILY_CAPACITY: dict[str, dict[str, int]] = _PACE_CFG.get("daily_capacity", {
    "relaxed": {"arrival": 240, "normal": 390, "departure": 180, "theme_park": 480},
    "moderate": {"arrival": 300, "normal": 480, "departure": 240, "theme_park": 540},
    "packed": {"arrival": 360, "normal": 570, "departure": 270, "theme_park": 600},
})
_PACE_TRANSIT: dict[str, dict[str, int]] = _PACE_CFG.get("transit", {
    "relaxed": {"arrival": 60, "normal": 80, "departure": 60, "theme_park": 20},
    "moderate": {"arrival": 90, "normal": 100, "departure": 90, "theme_park": 30},
    "packed": {"arrival": 120, "normal": 120, "departure": 90, "theme_park": 40},
})
_PACE_SLACK: dict[str, dict[str, int]] = _PACE_CFG.get("slack", {
    "relaxed": {"arrival": 120, "normal": 90, "departure": 120, "theme_park": 90},
    "moderate": {"arrival": 90, "normal": 75, "departure": 90, "theme_park": 60},
    "packed": {"arrival": 75, "normal": 60, "departure": 75, "theme_park": 45},
})
_PACE_CAPACITY = _PACE_CFG.get("capacity_units", {
    "relaxed": {"arrival": 0.3, "normal": 0.7, "departure": 0.3, "theme_park": 0.1},
    "moderate": {"arrival": 0.5, "normal": 1.0, "departure": 0.5, "theme_park": 0.2},
    "packed": {"arrival": 0.7, "normal": 1.3, "departure": 0.5, "theme_park": 0.3},
})
_PACE_TRANSFER = _PACE_CFG.get("transfer_budget", {
    "relaxed": {"arrival": 60, "normal": 90, "departure": 60, "theme_park": 30},
    "moderate": {"arrival": 90, "normal": 120, "departure": 90, "theme_park": 45},
    "packed": {"arrival": 120, "normal": 150, "departure": 90, "theme_park": 60},
})
_DRIVER_LOAD_FALLBACK: dict[str, int] = _PACE_CFG.get("driver_load_fallback", {
    "full_day": 360, "half_day": 200, "quarter_day": 100,
})


def build_route_skeleton(
    duration_days: int,
    selected_majors: list,
    hotel_bases: list,
    pace: str = "moderate",
    wake_up_time: str = "normal",
    arrival_day_half: bool = True,
    departure_day_half: bool = True,
    constraints: "PlanningConstraints | None" = None,
    resolved_policy: "ResolvedPolicySet | None" = None,
    booked_items: list[dict] | None = None,
) -> SkeletonResult:
    result = SkeletonResult()
    result.policy_summary = _policy_summary(resolved_policy)

    frames = [DayFrame(day_index=i, day_type=_default_day_type(i, duration_days)) for i in range(1, duration_days + 1)]
    _assign_sleep_bases(frames, hotel_bases)
    _assign_major_drivers(frames, selected_majors, hotel_bases, constraints=constraints)
    _detect_special_day_types(frames)
    _apply_booking_policy(
        frames,
        selected_majors,
        booked_items or [],
        resolved_policy=resolved_policy,
        constraints=constraints,
        result=result,
    )
    _apply_rhythm_check(frames, selected_majors, result)
    _calc_capacity_and_budget(
        frames,
        pace,
        arrival_day_half,
        departure_day_half,
        constraints=constraints,
        resolved_policy=resolved_policy,
    )
    _set_meal_windows(frames, wake_up_time, constraints=constraints)
    _mark_intensity(frames, pace, constraints=constraints)
    _generate_title_hints(frames)

    result.frames = frames
    result.trace.append(
        f"skeleton days={duration_days} majors={len(selected_majors)} pace={pace} "
        f"booking_alerts={len(result.booking_alerts)} degraded={len(result.degraded_majors)}"
    )
    if result.policy_summary:
        result.trace.append(
            "policy_day_frame="
            f"{result.policy_summary.get('arrival_capacity_ratio')}/"
            f"{result.policy_summary.get('normal_capacity_ratio')}/"
            f"{result.policy_summary.get('departure_capacity_ratio')} "
            f"transit_x={result.policy_summary.get('transit_budget_multiplier')}"
        )
    for frame in frames:
        result.trace.append(
            f"day{frame.day_index} [{frame.day_type}] sleep={frame.sleep_base} "
            f"corridor={frame.primary_corridor or '-'} driver={frame.main_driver or '-'} "
            f"cap={frame.daily_capacity_minutes} transit={frame.transit_minutes} "
            f"remaining={frame.remaining_minutes} booking={frame.booking_status}"
        )
    return result


def _default_day_type(day_index: int, duration_days: int) -> str:
    if day_index == 1:
        return "arrival"
    if day_index == duration_days:
        return "departure"
    return "normal"


def _assign_sleep_bases(frames: list[DayFrame], hotel_bases: list) -> None:
    if not hotel_bases:
        return
    night_assignments: list[str] = []
    for base in hotel_bases:
        city = getattr(base, "base_city", "") or ""
        area = getattr(base, "area", "") or city
        nights = int(getattr(base, "nights", 1) or 1)
        for _ in range(nights):
            night_assignments.append(area or city)
    for idx, frame in enumerate(frames):
        if idx < len(night_assignments):
            frame.sleep_base = night_assignments[idx]
        elif night_assignments:
            frame.sleep_base = night_assignments[-1]


def _assign_major_drivers(
    frames: list[DayFrame],
    selected_majors: list,
    hotel_bases: list,
    *,
    constraints: "PlanningConstraints | None" = None,
) -> None:
    if not selected_majors:
        return

    base_serves: dict[str, set[str]] = {}
    for base in hotel_bases:
        area = getattr(base, "area", "") or getattr(base, "base_city", "")
        base_serves[area] = set(getattr(base, "served_cluster_ids", []) or [])

    full_day: list = []
    half_day: list = []
    for major in selected_majors:
        dur = str(getattr(major, "default_duration", "full_day") or "full_day").lower()
        if "half" in dur or "quarter" in dur:
            half_day.append(major)
        else:
            full_day.append(major)

    normal_days = [frame for frame in frames if frame.day_type == "normal" and frame.main_driver is None]
    edge_days = [frame for frame in frames if frame.day_type in ("arrival", "departure") and frame.main_driver is None]

    def allowed_bases(cluster_id: str) -> set[str]:
        return {area for area, served in base_serves.items() if cluster_id in served}

    # 按 best_time_window 排序：morning 类优先分配到较早的 day_index
    def _time_sort_key(major):
        btw = str(getattr(major, "best_time_window", "") or "").lower()
        if "morning" in btw or "sunrise" in btw:
            return 0
        if "evening" in btw or "night" in btw or "sunset" in btw:
            return 2
        return 1

    full_day_sorted = sorted(full_day, key=_time_sort_key)

    for major in full_day_sorted:
        chosen = _choose_frame(
            candidates=normal_days,
            cluster_id=getattr(major, "cluster_id", ""),
            allowed_bases=allowed_bases(getattr(major, "cluster_id", "")),
            base_serves=base_serves,
        )
        if chosen is None:
            continue
        _attach_major(chosen, major)
        normal_days = [frame for frame in normal_days if frame.day_index != chosen.day_index]

    accept_departure = not (constraints and constraints.departure_day_no_poi)
    remaining_slots = [frame for frame in edge_days if frame.day_type == "arrival"] + normal_days
    if accept_departure:
        remaining_slots += [frame for frame in edge_days if frame.day_type == "departure"]

    # 到达日/离开日优先分配 arrival_friendly 的 half_day 活动
    def _is_arrival_friendly(major) -> bool:
        pf = getattr(major, "profile_fit", None) or []
        return "arrival_friendly" in pf

    # 排序：arrival_friendly 的排前面，优先分到 edge days
    half_day_sorted = sorted(half_day, key=lambda m: (0 if _is_arrival_friendly(m) else 1))

    for major in half_day_sorted:
        chosen = None
        cluster_id = getattr(major, "cluster_id", "")
        allowed = allowed_bases(cluster_id)
        for frame in remaining_slots:
            if frame.day_type == "departure" and not _is_departure_compatible(major):
                continue
            # 到达日/离开日优先给 arrival_friendly 的活动
            if frame.day_type in ("arrival", "departure") and not _is_arrival_friendly(major):
                # 如果还有 arrival_friendly 的活动没分配，跳过 edge day
                has_friendly = any(_is_arrival_friendly(m) for m in half_day_sorted
                                   if getattr(m, "cluster_id", "") != cluster_id)
                if has_friendly:
                    continue
            if not allowed or frame.sleep_base in allowed:
                chosen = frame
                break
        if chosen is None:
            for frame in remaining_slots:
                if frame.day_type != "departure":
                    chosen = frame
                    break
        if chosen is None:
            continue
        _attach_major(chosen, major)
        remaining_slots = [frame for frame in remaining_slots if frame.day_index != chosen.day_index]

    for frame in frames:
        if frame.day_type == "departure" and not frame.main_driver:
            frame.primary_corridor = frame.sleep_base
            frame.notes.append("departure_shape: keep hotel area and airport buffer")


def _choose_frame(
    *,
    candidates: list[DayFrame],
    cluster_id: str,
    allowed_bases: set[str],
    base_serves: dict[str, set[str]],
) -> DayFrame | None:
    best_day = None
    best_score = -1
    for day in candidates:
        if allowed_bases and day.sleep_base not in allowed_bases:
            continue
        score = 5
        if cluster_id in base_serves.get(day.sleep_base, set()):
            score += 10
        if score > best_score:
            best_score = score
            best_day = day
    if best_day is not None:
        return best_day
    for day in candidates:
        if day.main_driver is None:
            return day
    return None


def _attach_major(frame: DayFrame, major: _MajorInfo) -> None:
    frame.main_driver = getattr(major, "cluster_id", "")
    frame.main_driver_name = getattr(major, "name_zh", frame.main_driver or "")
    corridor = getattr(major, "primary_corridor", "") or ""
    if not frame.primary_corridor:
        frame.primary_corridor = corridor
    elif corridor and corridor != frame.primary_corridor:
        frame.secondary_corridor = corridor
    frame.must_keep_ids.append(frame.main_driver or "")
    frame.activity_load_minutes = int(getattr(major, "activity_load_minutes", 0) or 0)
    # 记录活动最佳时段偏好，供时间线生成使用
    btw = getattr(major, "best_time_window", None) or ""
    if btw:
        frame.extras = getattr(frame, "extras", {}) or {}
        frame.extras["best_time_window"] = btw


def _is_departure_compatible(major: _MajorInfo) -> bool:
    name = str(getattr(major, "name_zh", "") or "").lower()
    cluster_id = str(getattr(major, "cluster_id", "") or "").lower()
    return not any(keyword in name or keyword in cluster_id for keyword in _DEPARTURE_BLOCKED_KEYWORDS)


def _detect_special_day_types(frames: list[DayFrame]) -> None:
    for frame in frames:
        if frame.day_type != "normal":
            continue
        tokens = " ".join(
            [
                str(frame.main_driver or "").lower(),
                str(frame.main_driver_name or "").lower(),
                str(frame.primary_corridor or "").lower(),
            ]
        )
        if any(keyword in tokens for keyword in _THEME_PARK_KEYWORDS):
            frame.day_type = "theme_park"
            frame.notes.append("theme_park day")


def _apply_booking_policy(
    frames: list[DayFrame],
    selected_majors: list,
    booked_items: list[dict],
    *,
    resolved_policy: "ResolvedPolicySet | None",
    constraints: "PlanningConstraints | None",
    result: SkeletonResult,
) -> None:
    major_map = {getattr(major, "cluster_id", ""): major for major in selected_majors}
    if not major_map:
        return

    for frame in frames:
        if not frame.main_driver:
            continue
        major = major_map.get(frame.main_driver)
        if major is None or not bool(getattr(major, "reservation_required", False)):
            continue

        pressure = str(getattr(major, "reservation_pressure", "medium") or "medium").lower()
        confirmed = _is_major_booked(major, booked_items)
        frame.booking_status = "confirmed" if confirmed else "unbooked"
        frame.booking_explain = str(getattr(major, "booking_hint", "") or "")

        booking_level = "must_book" if pressure == "high" else "should_book"
        alert = {
            "day_index": frame.day_index,
            "cluster_id": frame.main_driver,
            "cluster_name": frame.main_driver_name,
            "booking_level": booking_level,
            "confirmed": confirmed,
            "reason": frame.booking_explain or "reservation pressure detected",
        }
        frame.booking_alerts.append(alert)
        result.booking_alerts.append(alert)

        hold_back_edge_days = bool(
            resolved_policy and resolved_policy.booking_and_reservation_policy.hold_back_edge_days
        )
        degrade_only = bool(
            resolved_policy is None
            or resolved_policy.booking_and_reservation_policy.unbooked_major_action == "degrade_only"
        )
        hard_pressure = pressure == "high" or (
            resolved_policy is not None
            and resolved_policy.booking_and_reservation_policy.high_pressure_constraint == "hard"
        )
        edge_day = frame.day_type in {"arrival", "departure"}

        if not confirmed and degrade_only and (hard_pressure or (hold_back_edge_days and edge_day)):
            original_driver = frame.main_driver
            original_name = frame.main_driver_name
            frame.booking_status = "degraded"
            frame.fallback_corridor = frame.primary_corridor or frame.sleep_base
            frame.primary_corridor = frame.sleep_base or frame.primary_corridor
            frame.cut_order = [original_driver] if original_driver else []
            frame.notes.append(
                f"booking_policy: {original_name} not hard-scheduled without confirmed reservation"
            )
            if original_driver in frame.must_keep_ids:
                frame.must_keep_ids.remove(original_driver)
            frame.main_driver = None
            frame.main_driver_name = ""
            frame.activity_load_minutes = 0
            result.degraded_majors.append(original_driver)
            result.trace.append(
                f"booking_degrade day{frame.day_index} cluster={original_driver} pressure={pressure}"
            )

    if constraints is not None:
        constraints.record_consumption(
            "policy_booking_and_reservation",
            "skeleton",
            "booking_policy_applied",
            f"alerts={len(result.booking_alerts)} degraded={len(result.degraded_majors)}",
        )


def _is_major_booked(major: _MajorInfo, booked_items: list[dict]) -> bool:
    cluster_id = str(getattr(major, "cluster_id", "") or "")
    name = str(getattr(major, "name_zh", "") or "").lower()
    anchor_ids = {str(anchor_id) for anchor_id in (getattr(major, "anchor_entity_ids", []) or [])}
    for item in booked_items:
        if not isinstance(item, dict):
            continue
        raw_keys = {
            str(item.get("cluster_id") or ""),
            str(item.get("item_id") or ""),
            str(item.get("entity_id") or ""),
            str(item.get("name") or "").lower(),
        }
        if cluster_id in raw_keys or name in raw_keys:
            return True
        if anchor_ids & {value for value in raw_keys if value}:
            return True
    return False


def _calc_capacity_and_budget(
    frames: list[DayFrame],
    pace: str,
    arrival_half: bool,
    departure_half: bool,
    *,
    constraints: "PlanningConstraints | None",
    resolved_policy: "ResolvedPolicySet | None",
) -> None:
    pace_key = pace if pace in _PACE_DAILY_CAPACITY else "moderate"
    cap_map = _PACE_DAILY_CAPACITY[pace_key]
    transit_map = _PACE_TRANSIT[pace_key]
    slack_map = _PACE_SLACK[pace_key]
    unit_map = _PACE_CAPACITY[pace_key]
    transfer_map = _PACE_TRANSFER[pace_key]
    day_frame_policy = resolved_policy.day_frame_policy if resolved_policy is not None else None

    for frame in frames:
        dtype = frame.day_type if frame.day_type in cap_map else "normal"
        capacity = cap_map[dtype]
        transit = transit_map[dtype]
        slack = slack_map[dtype]

        if frame.day_type == "arrival" and not arrival_half:
            capacity = max(capacity, cap_map["normal"])
        if frame.day_type == "departure" and not departure_half:
            capacity = max(capacity, cap_map["normal"])

        ratio = 1.0
        if day_frame_policy is not None:
            if frame.day_type == "arrival":
                ratio = day_frame_policy.arrival_capacity_ratio
            elif frame.day_type == "departure":
                ratio = day_frame_policy.departure_capacity_ratio
            else:
                ratio = day_frame_policy.normal_capacity_ratio
            transit = int(round(transit * day_frame_policy.transit_budget_multiplier)) + day_frame_policy.transit_buffer_minutes
            slack += day_frame_policy.driving_day_slack_minutes
            if day_frame_policy.low_density_mode and frame.day_type == "normal":
                frame.notes.append("day_frame_policy: low_density")

        frame.daily_capacity_minutes = int(round(capacity * ratio))
        frame.transit_minutes = transit
        frame.slack_minutes = slack
        if frame.main_driver and frame.activity_load_minutes <= 0:
            dur_key = "full_day"
            frame.activity_load_minutes = _DRIVER_LOAD_FALLBACK.get(dur_key, 360)
        frame.remaining_minutes = max(
            0,
            frame.daily_capacity_minutes - frame.activity_load_minutes - frame.transit_minutes - frame.slack_minutes,
        )
        frame.day_label = minutes_to_day_label(frame.daily_capacity_minutes)
        frame.day_capacity_units = unit_map[dtype]
        frame.transfer_budget_minutes = int(round(transfer_map[dtype] * (day_frame_policy.transit_budget_multiplier if day_frame_policy else 1.0)))
        if frame.main_driver:
            frame.day_capacity_units = max(0.0, frame.day_capacity_units - 0.3)

    if constraints is not None and day_frame_policy is not None:
        constraints.record_consumption(
            "policy_day_frame",
            "skeleton",
            "frame_budget_applied",
            (
                f"arrival_ratio={day_frame_policy.arrival_capacity_ratio} "
                f"departure_ratio={day_frame_policy.departure_capacity_ratio} "
                f"transit_multiplier={day_frame_policy.transit_budget_multiplier}"
            ),
        )
        constraints.record_consumption(
            "policy_mobility",
            "skeleton",
            "transit_budget_applied",
            f"max_transfer_minutes_per_day={constraints.max_transfer_minutes_per_day}",
        )
        constraints.record_consumption(
            "policy_routing_style",
            "skeleton",
            "routing_mode_applied",
            f"routing_mode={constraints.routing_mode}",
        )


def _set_meal_windows(
    frames: list[DayFrame],
    wake_up: str,
    *,
    constraints: "PlanningConstraints | None",
) -> None:
    breakfast_early, breakfast_late = _WAKE_BREAKFAST.get(wake_up, _WAKE_BREAKFAST["normal"])
    departure_meal_window = "breakfast_only"
    arrival_evening_only = False
    if constraints is not None:
        departure_meal_window = constraints.departure_meal_window
        arrival_evening_only = constraints.arrival_evening_only
        constraints.record_consumption(
            "departure_constraints",
            "skeleton",
            "meal_window_applied",
            f"departure meals={departure_meal_window}",
        )
        constraints.record_consumption(
            "arrival_constraints",
            "skeleton",
            "arrival_shape_applied",
            f"evening_only={arrival_evening_only}",
        )

    for frame in frames:
        meals: list[MealWindow] = []
        if frame.day_type == "departure":
            if departure_meal_window in ("breakfast_only", "breakfast_lunch"):
                meals.append(MealWindow("breakfast", breakfast_early, breakfast_late, "quick"))
            if departure_meal_window == "breakfast_lunch":
                meals.append(MealWindow("lunch", _LUNCH_WINDOW[0], _LUNCH_WINDOW[1], "route_meal"))
        elif frame.day_type == "arrival":
            if arrival_evening_only:
                meals.append(MealWindow("dinner", _DINNER_WINDOW[0], _DINNER_WINDOW[1], "route_meal"))
            else:
                meals.append(MealWindow("lunch", _LUNCH_WINDOW[0], _LUNCH_WINDOW[1], "route_meal"))
                meals.append(MealWindow("dinner", _DINNER_WINDOW[0], _DINNER_WINDOW[1], "route_meal"))
        elif frame.day_type == "theme_park":
            meals.extend(
                [
                    MealWindow("breakfast", breakfast_early, breakfast_late, "quick"),
                    MealWindow("lunch", _LUNCH_WINDOW[0], _LUNCH_WINDOW[1], "park_meal"),
                    MealWindow("dinner", _DINNER_WINDOW[0], _DINNER_WINDOW[1], "destination_meal"),
                ]
            )
        else:
            meals.extend(
                [
                    MealWindow("breakfast", breakfast_early, breakfast_late, "quick"),
                    MealWindow("lunch", _LUNCH_WINDOW[0], _LUNCH_WINDOW[1], "route_meal"),
                    MealWindow("dinner", _DINNER_WINDOW[0], _DINNER_WINDOW[1], "route_meal"),
                ]
            )
        frame.meal_windows = meals


def _mark_intensity(frames: list[DayFrame], pace: str, *, constraints: "PlanningConstraints | None") -> None:
    pace_cap = {"relaxed": "balanced", "moderate": "dense", "packed": "dense"}.get(pace, "dense")
    order = {"light": 0, "balanced": 1, "dense": 2}
    if constraints is not None:
        from app.domains.planning.constraint_compiler import max_allowed_intensity_name

        constraint_cap = max_allowed_intensity_name(constraints)
        if order.get(constraint_cap, 2) < order.get(pace_cap, 2):
            pace_cap = constraint_cap
        constraints.record_consumption(
            "max_intensity",
            "skeleton",
            "intensity_cap",
            f"capped at {pace_cap}",
        )

    for frame in frames:
        if frame.day_type in {"arrival", "departure"}:
            raw = "light"
        elif frame.day_type == "theme_park":
            raw = "dense"
        elif pace == "relaxed":
            raw = "balanced" if frame.main_driver else "light"
        elif pace == "packed":
            raw = "dense"
        else:
            raw = "balanced"
        if order.get(raw, 1) > order.get(pace_cap, 2):
            raw = pace_cap
        frame.intensity = "light" if frame.day_index == len(frames) else raw


def _generate_title_hints(frames: list[DayFrame]) -> None:
    for frame in frames:
        parts: list[str] = []
        if frame.day_type == "arrival":
            parts.append("到达日")
        elif frame.day_type == "departure":
            parts.append("返程日")
        if frame.main_driver_name and frame.booking_status != "degraded":
            parts.append(frame.main_driver_name)
        elif frame.primary_corridor:
            parts.append(display_corridor(frame.primary_corridor))
        if frame.sleep_base and frame.day_type != "departure":
            parts.append(f"住{_display_area(frame.sleep_base)}")
        if frame.day_type == "departure":
            parts.append("轻松收尾")
        frame.title_hint = " · ".join([part for part in parts if part]) or f"Day {frame.day_index}"


# ── 节奏检查后处理 ──────────────────────────────────────────────────────────

def _apply_rhythm_check(
    frames: list[DayFrame],
    selected_majors: list,
    result: SkeletonResult,
) -> None:
    """
    3 条节奏硬规则后处理。检查连续天的 driver 节奏属性，
    违规时尝试交换相邻天的 driver 来修复。

    硬规则：
      R1: 相邻两天 experience_family 不能相同
      R2: 两个 peak 之间至少隔一个 recovery 或 contrast
      R3: energy_level=high 后面必须跟 medium 或 low
    """
    # 构建 cluster_id → 节奏属性映射
    rhythm_map: dict[str, dict[str, str]] = {}
    for major in selected_majors:
        cid = getattr(major, "cluster_id", "")
        if cid:
            rhythm_map[cid] = {
                "experience_family": getattr(major, "experience_family", "") or "",
                "rhythm_role": getattr(major, "rhythm_role", "") or "",
                "energy_level": getattr(major, "energy_level", "") or "",
            }

    if not rhythm_map:
        return

    def _get_rhythm(frame: DayFrame) -> dict[str, str]:
        return rhythm_map.get(frame.main_driver or "", {})

    max_passes = 3
    for pass_num in range(max_passes):
        violations = _find_rhythm_violations(frames, _get_rhythm)
        if not violations:
            return

        result.trace.append(
            f"rhythm_check pass={pass_num+1} violations={len(violations)}: "
            + ", ".join(f"{v[0]}@day{v[1]}" for v in violations)
        )

        fixed_any = False
        for rule, day_idx, *_ in violations:
            if _try_swap_to_fix(frames, day_idx, _get_rhythm, rule):
                fixed_any = True
                result.trace.append(f"  rhythm_fix: swapped day{day_idx} driver")
                break  # 每轮只修一个，重新检查

        if not fixed_any:
            result.trace.append("rhythm_check: unfixable violations remain")
            return


def _find_rhythm_violations(
    frames: list[DayFrame],
    get_rhythm,
) -> list[tuple]:
    """返回所有节奏违规: [(rule_id, day_index, detail), ...]"""
    violations = []
    driven_frames = [f for f in frames if f.main_driver]

    for i in range(len(driven_frames) - 1):
        curr = get_rhythm(driven_frames[i])
        next_ = get_rhythm(driven_frames[i + 1])
        day_idx = driven_frames[i].day_index

        if not curr or not next_:
            continue

        # R1: 同 experience_family 不连续
        cf = curr.get("experience_family")
        nf = next_.get("experience_family")
        if cf and nf and cf == nf:
            violations.append(("R1_same_family", day_idx, cf))

        # R2: peak 后面不能紧跟 peak
        cr = curr.get("rhythm_role")
        nr = next_.get("rhythm_role")
        if cr == "peak" and nr == "peak":
            violations.append(("R2_consecutive_peaks", day_idx))

        # R3: high energy 后面必须跟 medium 或 low
        ce = curr.get("energy_level")
        ne = next_.get("energy_level")
        if ce == "high" and ne == "high":
            violations.append(("R3_consecutive_high", day_idx))

    return violations


def _try_swap_to_fix(
    frames: list[DayFrame],
    problem_day: int,
    get_rhythm,
    rule: str,
) -> bool:
    """
    尝试将 problem_day 的 driver 与其他非相邻天交换来修复违规。
    只交换 normal 类型的天，不动 arrival/departure/theme_park。
    """
    problem_frame = None
    for f in frames:
        if f.day_index == problem_day:
            problem_frame = f
            break
    if not problem_frame or not problem_frame.main_driver:
        return False

    # 找候选交换天：有 driver、normal 类型、不是 problem_day 本身及其相邻天
    candidates = [
        f for f in frames
        if f.main_driver
        and f.day_type == "normal"
        and abs(f.day_index - problem_day) >= 2
    ]

    old_count = len(_find_rhythm_violations(frames, get_rhythm))

    for candidate in candidates:
        # 模拟交换
        _swap_drivers(problem_frame, candidate)

        new_violations = _find_rhythm_violations(frames, get_rhythm)
        if len(new_violations) < old_count:
            return True  # 改善了

        # 没用，换回来
        _swap_drivers(problem_frame, candidate)

    return False


def _swap_drivers(a: DayFrame, b: DayFrame) -> None:
    """交换两个 frame 的 driver 信息。"""
    (a.main_driver, b.main_driver) = (b.main_driver, a.main_driver)
    (a.main_driver_name, b.main_driver_name) = (b.main_driver_name, a.main_driver_name)
    (a.primary_corridor, b.primary_corridor) = (b.primary_corridor, a.primary_corridor)
    (a.secondary_corridor, b.secondary_corridor) = (b.secondary_corridor, a.secondary_corridor)
    (a.activity_load_minutes, b.activity_load_minutes) = (b.activity_load_minutes, a.activity_load_minutes)


def display_corridor(corridor: str) -> str:
    return _display_corridor(corridor)


def display_city(city_code: str) -> str:
    return _display_city(city_code)


def minutes_to_day_label(minutes: int) -> str:
    if minutes <= 120:
        return "light_slot"
    if minutes <= 240:
        return "short_activity"
    if minutes <= 360:
        return "half_day"
    if minutes <= 480:
        return "strong_half_day"
    return "full_day"


def minutes_to_intensity_hint(remaining: int) -> str:
    if remaining > 150:
        return "loose"
    if remaining >= 90:
        return "balanced"
    if remaining >= 30:
        return "tight"
    return "very_tight"


def _policy_summary(resolved_policy: "ResolvedPolicySet | None") -> dict[str, object]:
    if resolved_policy is None:
        return {}
    policy = resolved_policy.day_frame_policy
    booking = resolved_policy.booking_and_reservation_policy
    return {
        "arrival_capacity_ratio": policy.arrival_capacity_ratio,
        "normal_capacity_ratio": policy.normal_capacity_ratio,
        "departure_capacity_ratio": policy.departure_capacity_ratio,
        "transit_budget_multiplier": policy.transit_budget_multiplier,
        "transit_buffer_minutes": policy.transit_buffer_minutes,
        "low_density_mode": policy.low_density_mode,
        "booking_high_pressure_constraint": booking.high_pressure_constraint,
        "booking_unbooked_major_action": booking.unbooked_major_action,
    }

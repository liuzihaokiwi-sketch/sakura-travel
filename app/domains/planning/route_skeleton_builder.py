"""
route_skeleton_builder.py — 日骨架生成器（Phase 3 骨架编排）

输入：
  - selected_majors（已选主要活动列表，from major_activity_ranker）
  - hotel_strategy（住法策略，from hotel_base_builder）
  - TripProfile
  - circle_id

输出：
  - list[DayFrame] — 每天的骨架，包含 11 个字段，足以约束后续次要活动和餐厅填充

DayFrame 字段：
  day_index, sleep_base, primary_corridor, secondary_corridor,
  main_driver, day_capacity_units, transfer_budget_minutes,
  meal_windows, must_keep_ids, cut_order, fallback_corridor
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ── DayFrame 定义 ─────────────────────────────────────────────────────────────

@dataclass
class MealWindow:
    meal_type: str       # breakfast / lunch / dinner
    earliest: str = ""   # HH:MM
    latest: str = ""     # HH:MM
    style_hint: str = "" # quick / route_meal / destination_meal


@dataclass
class DayFrame:
    """单天骨架 — 约束后续所有填充。"""
    day_index: int                                    # 1-based
    day_type: str = "normal"                          # arrival / normal / departure / transfer
    sleep_base: str = ""                              # 当晚住在哪个 base area
    primary_corridor: str = ""                        # 主走廊（来自 main_driver 的 cluster corridor）
    secondary_corridor: Optional[str] = None          # 副走廊
    main_driver: Optional[str] = None                 # cluster_id of the day's main activity
    main_driver_name: str = ""                        # 活动簇名称
    day_capacity_units: float = 1.0                   # 今天可装入多少活动单位
    transfer_budget_minutes: int = 120                # 当天剩余通勤预算（分钟）
    meal_windows: list[MealWindow] = field(default_factory=list)
    must_keep_ids: list[str] = field(default_factory=list)  # 不可砍的 entity/cluster id
    cut_order: list[str] = field(default_factory=list)      # 可砍优先级（先砍的在前）
    fallback_corridor: Optional[str] = None           # 雨天/关闭时的替代走廊
    intensity: str = "balanced"                       # light / balanced / dense
    title_hint: str = ""                              # 标题提示（给 AI 用）
    notes: list[str] = field(default_factory=list)    # 骨架层备注


@dataclass
class SkeletonResult:
    frames: list[DayFrame] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)


# ── 外部导入类型提示 ──────────────────────────────────────────────────────────
# 避免循环导入，用字符串协议

class _MajorInfo:
    """duck type for RankedMajor from major_activity_ranker"""
    cluster_id: str
    name_zh: str
    capacity_units: float
    default_duration: str
    primary_corridor: str


class _HotelBaseInfo:
    """duck type for HotelBase from hotel_base_builder"""
    base_city: str
    area: str
    nights: int
    served_cluster_ids: list[str]


# ── 主入口 ────────────────────────────────────────────────────────────────────

def build_route_skeleton(
    duration_days: int,
    selected_majors: list,       # list[RankedMajor]
    hotel_bases: list,           # list[HotelBase]
    pace: str = "moderate",
    wake_up_time: str = "normal",
    arrival_day_half: bool = True,
    departure_day_half: bool = True,
) -> SkeletonResult:
    """
    纯函数（无 I/O）：根据主要活动和住法，生成每天的骨架。

    核心逻辑：
    1. 铺底：创建 duration_days 个 DayFrame，标记 arrival/departure/normal
    2. 分配 sleep_base：根据 hotel_bases 分配每天住哪里
    3. 锁 major：每天最多锁 1 个 major activity 作为 main_driver
    4. 计算容量和通勤预算
    5. 设定 meal_windows
    6. 标记 intensity
    """
    result = SkeletonResult()

    # Step 1: 创建空白 frames
    frames: list[DayFrame] = []
    for i in range(1, duration_days + 1):
        day_type = "normal"
        if i == 1:
            day_type = "arrival"
        elif i == duration_days:
            day_type = "departure"
        frames.append(DayFrame(day_index=i, day_type=day_type))

    # Step 2: 分配 sleep_base
    _assign_sleep_bases(frames, hotel_bases, duration_days)

    # Step 3: 锁 major activities
    _assign_major_drivers(frames, selected_majors, hotel_bases)

    # Step 4: 计算容量和通勤预算
    _calc_capacity_and_budget(frames, pace, arrival_day_half, departure_day_half)

    # Step 5: 设定 meal_windows
    _set_meal_windows(frames, wake_up_time)

    # Step 6: 标记 intensity
    _mark_intensity(frames, pace)

    # Step 7: 生成标题提示
    _generate_title_hints(frames)

    result.frames = frames
    result.trace.append(
        f"skeleton: {duration_days} days, "
        f"{len(selected_majors)} majors assigned, "
        f"pace={pace}"
    )
    for f in frames:
        result.trace.append(
            f"  day{f.day_index} [{f.day_type}] "
            f"sleep={f.sleep_base} corridor={f.primary_corridor} "
            f"driver={f.main_driver or 'none'} "
            f"cap={f.day_capacity_units} intensity={f.intensity}"
        )

    return result


# ── Step 2: 分配 sleep_base ──────────────────────────────────────────────────

def _assign_sleep_bases(
    frames: list[DayFrame],
    hotel_bases: list,
    duration_days: int,
) -> None:
    """按 hotel_bases 的 nights 顺序分配每天住哪里。"""
    if not hotel_bases:
        return

    night_assignments: list[str] = []
    for base in hotel_bases:
        city = getattr(base, "base_city", "") or ""
        area = getattr(base, "area", "") or city
        nights = getattr(base, "nights", 1) or 1
        for _ in range(nights):
            night_assignments.append(area or city)

    # frames: day 1 到 day N
    # 住宿：第 1 晚到第 N-1 晚
    for i, frame in enumerate(frames):
        if i < len(night_assignments):
            frame.sleep_base = night_assignments[i]
        elif night_assignments:
            frame.sleep_base = night_assignments[-1]


# ── Step 3: 锁 major activities ──────────────────────────────────────────────

def _assign_major_drivers(
    frames: list[DayFrame],
    selected_majors: list,
    hotel_bases: list,
) -> None:
    """
    贪心分配：
    - 全日型 major 优先分配到 normal 天
    - 半日型 major 可以分配到 arrival/departure 天
    - 尽量让 major 的 corridor 和 sleep_base 在同城市
    """
    if not selected_majors:
        return

    # 分成全日和半日
    full_day: list = []
    half_day: list = []
    for m in selected_majors:
        dur = getattr(m, "default_duration", "full_day") or "full_day"
        if "half" in dur.lower() or "quarter" in dur.lower():
            half_day.append(m)
        else:
            full_day.append(m)

    # 可用天：normal 天优先给 full_day，arrival/departure 给 half_day
    normal_days = [f for f in frames if f.day_type == "normal" and f.main_driver is None]
    edge_days = [f for f in frames if f.day_type in ("arrival", "departure") and f.main_driver is None]

    # 构建 base → served_clusters 映射
    base_serves: dict[str, set[str]] = {}
    for base in hotel_bases:
        area = getattr(base, "area", "") or getattr(base, "base_city", "")
        served = set(getattr(base, "served_cluster_ids", []) or [])
        base_serves[area] = served

    # ── 推断 major → 最佳 base area 映射 ──
    def _major_best_bases(cid: str) -> set[str]:
        """返回能 serve 此 cluster 的所有 base area"""
        matching = set()
        for area, served in base_serves.items():
            if cid in served:
                matching.add(area)
        return matching

    # 分配 full_day majors 到 normal days（硬约束：活动 base 必须匹配 sleep_base）
    for major in full_day:
        cid = getattr(major, "cluster_id", "")
        corridor = getattr(major, "primary_corridor", "")
        name = getattr(major, "name_zh", cid)
        allowed_bases = _major_best_bases(cid)

        # 硬约束：sleep_base 必须在 allowed_bases 内
        best_day = None
        best_score = -1
        for day in normal_days:
            if allowed_bases and day.sleep_base not in allowed_bases:
                continue  # 硬约束：跳过不匹配的天
            score = 0
            if cid in base_serves.get(day.sleep_base, set()):
                score += 10
            if day.main_driver is None:
                score += 5
            if score > best_score:
                best_score = score
                best_day = day

        # 如果硬约束下无可用天，放宽到所有 normal days（降级，加 trace）
        if best_day is None:
            for day in normal_days:
                if day.main_driver is None:
                    best_day = day
                    logger.warning(
                        "major %s 无法匹配 sleep_base (allowed=%s)，降级分配到 Day%d sleep=%s",
                        cid, allowed_bases, day.day_index, day.sleep_base,
                    )
                    break

        if best_day:
            best_day.main_driver = cid
            best_day.main_driver_name = name
            best_day.primary_corridor = corridor
            best_day.must_keep_ids.append(cid)
            normal_days = [d for d in normal_days if d.day_index != best_day.day_index]

    # ── departure 白名单：夜游/重度 cluster 不能放 departure ──
    _DEPARTURE_BLOCKED_TAGS = {"night", "nightlife", "food_night", "theme_park"}

    def _is_departure_compatible(cid: str, name: str) -> bool:
        name_lower = name.lower()
        if any(tag in name_lower for tag in ["夜游", "夜市", "night"]):
            return False
        if any(tag in cid for tag in ["night", "themepark", "usj"]):
            return False
        return True

    # 分配 half_day majors：优先 arrival → normal → departure（departure 最后用且有白名单）
    arrival_slots = [f for f in edge_days if f.day_type == "arrival"]
    departure_slots = [f for f in edge_days if f.day_type == "departure"]
    remaining_slots = arrival_slots + normal_days + departure_slots
    for major in half_day:
        cid = getattr(major, "cluster_id", "")
        corridor = getattr(major, "primary_corridor", "")
        name = getattr(major, "name_zh", cid)
        allowed_bases = _major_best_bases(cid)

        # 先找 base 匹配 + day_type 兼容的 slot
        chosen = None
        for day in remaining_slots:
            # departure 天检查白名单
            if day.day_type == "departure" and not _is_departure_compatible(cid, name):
                continue
            if not allowed_bases or day.sleep_base in allowed_bases:
                chosen = day
                break
        # 降级：如果没有匹配的，用第一个非 departure slot；最后才考虑 departure
        if chosen is None:
            for day in remaining_slots:
                if day.day_type != "departure":
                    chosen = day
                    break
            if chosen is None and remaining_slots:
                chosen = remaining_slots[0]
            if chosen:
                logger.warning(
                    "half-day major %s 降级分配到 Day%d (%s)",
                    cid, chosen.day_index, chosen.day_type,
                )

        if chosen:
            remaining_slots = [d for d in remaining_slots if d.day_index != chosen.day_index]
            chosen.main_driver = cid
            chosen.main_driver_name = name
            if not chosen.primary_corridor:
                chosen.primary_corridor = corridor
            else:
                chosen.secondary_corridor = corridor
            chosen.must_keep_ids.append(cid)

    # departure 天如果没有 driver，给一个轻量默认标题
    for frame in frames:
        if frame.day_type == "departure" and not frame.main_driver:
            frame.title_hint = "返程日 · 轻松收尾"
            frame.primary_corridor = frame.sleep_base  # 酒店周边


# ── Step 4: 容量和通勤预算 ───────────────────────────────────────────────────

_PACE_CAPACITY = {
    "relaxed": {"arrival": 0.3, "normal": 0.7, "departure": 0.3},
    "moderate": {"arrival": 0.5, "normal": 1.0, "departure": 0.5},
    "packed": {"arrival": 0.7, "normal": 1.3, "departure": 0.5},
}

_PACE_TRANSFER = {
    "relaxed": {"arrival": 60, "normal": 90, "departure": 60},
    "moderate": {"arrival": 90, "normal": 120, "departure": 90},
    "packed": {"arrival": 120, "normal": 150, "departure": 90},
}


def _calc_capacity_and_budget(
    frames: list[DayFrame],
    pace: str,
    arrival_half: bool,
    departure_half: bool,
) -> None:
    pace_key = pace if pace in _PACE_CAPACITY else "moderate"
    cap_map = _PACE_CAPACITY[pace_key]
    trans_map = _PACE_TRANSFER[pace_key]

    for frame in frames:
        dtype = frame.day_type if frame.day_type in cap_map else "normal"
        frame.day_capacity_units = cap_map[dtype]
        frame.transfer_budget_minutes = trans_map[dtype]

        # 有 main_driver 的天，已经用掉部分容量
        if frame.main_driver:
            # full_day driver 用掉 0.7 容量，half_day 用掉 0.35
            frame.day_capacity_units = max(0, frame.day_capacity_units - 0.3)


# ── Step 5: Meal Windows ─────────────────────────────────────────────────────

_WAKE_BREAKFAST = {
    "early": ("07:00", "08:00"),
    "normal": ("08:00", "09:30"),
    "late": ("09:00", "10:30"),
}

_LUNCH_WINDOW = ("11:30", "13:30")
_DINNER_WINDOW = ("17:30", "20:00")


def _set_meal_windows(
    frames: list[DayFrame],
    wake_up: str,
) -> None:
    bf_early, bf_late = _WAKE_BREAKFAST.get(wake_up, _WAKE_BREAKFAST["normal"])

    for frame in frames:
        meals = []

        if frame.day_type != "departure":
            meals.append(MealWindow(
                meal_type="breakfast",
                earliest=bf_early,
                latest=bf_late,
                style_hint="quick",
            ))

        meals.append(MealWindow(
            meal_type="lunch",
            earliest=_LUNCH_WINDOW[0],
            latest=_LUNCH_WINDOW[1],
            style_hint="route_meal",
        ))

        if frame.day_type != "departure":
            meals.append(MealWindow(
                meal_type="dinner",
                earliest=_DINNER_WINDOW[0],
                latest=_DINNER_WINDOW[1],
                style_hint="route_meal",
            ))

        frame.meal_windows = meals


# ── Step 6: Intensity ─────────────────────────────────────────────────────────

def _mark_intensity(frames: list[DayFrame], pace: str) -> None:
    for frame in frames:
        if frame.day_type in ("arrival", "departure"):
            frame.intensity = "light"
        elif pace == "relaxed":
            frame.intensity = "light" if not frame.main_driver else "balanced"
        elif pace == "packed":
            frame.intensity = "dense"
        else:
            frame.intensity = "balanced"

        # 最后一天强制 light
        if frame.day_index == len(frames):
            frame.intensity = "light"


# ── Step 7: Title Hints ──────────────────────────────────────────────────────

# ── area → 中文展示名映射 ─────────────────────────────────────────────────────

_AREA_DISPLAY = {
    "kawaramachi": "京都·河原町",
    "gion": "京都·祇园",
    "kyoto_station": "京都·京都站",
    "namba": "大阪·难波",
    "shinsaibashi": "大阪·心斋桥",
    "umeda": "大阪·梅田",
    "nara": "奈良",
    "kyoto": "京都",
    "osaka": "大阪",
}


def _display_area(area: str) -> str:
    return _AREA_DISPLAY.get(area, area)


def _generate_title_hints(frames: list[DayFrame]) -> None:
    for frame in frames:
        parts = []
        if frame.day_type == "arrival":
            parts.append("到达日")
        elif frame.day_type == "departure":
            parts.append("返程日")

        if frame.main_driver_name:
            # 去掉 cluster name 中的 "城市·" 前缀重复
            parts.append(frame.main_driver_name)
        elif frame.primary_corridor:
            parts.append(frame.primary_corridor)

        if frame.sleep_base and frame.day_type not in ("departure",):
            parts.append(f"住{_display_area(frame.sleep_base)}")

        frame.title_hint = " · ".join(parts) if parts else f"Day {frame.day_index}"

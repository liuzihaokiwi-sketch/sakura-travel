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
    day_capacity_units: float = 1.0                   # 兼容保留（展示/旧逻辑用），内部调度用分钟字段
    transfer_budget_minutes: int = 120                # 当天剩余通勤预算（分钟）
    meal_windows: list[MealWindow] = field(default_factory=list)
    must_keep_ids: list[str] = field(default_factory=list)  # 不可砍的 entity/cluster id
    cut_order: list[str] = field(default_factory=list)      # 可砍优先级（先砍的在前）
    fallback_corridor: Optional[str] = None           # 雨天/关闭时的替代走廊
    intensity: str = "balanced"                       # light / balanced / dense
    title_hint: str = ""                              # 标题提示（给 AI 用）
    notes: list[str] = field(default_factory=list)    # 骨架层备注
    # ── 分钟预算模型（4层时间模型）────────────────────────────────────────────
    daily_capacity_minutes: int = 480                 # 用户今天可用活动总分钟数
    activity_load_minutes: int = 0                    # main_driver 已占用分钟数
    transit_minutes: int = 120                        # 通勤占用（含换乘缓冲）
    slack_minutes: int = 90                           # 弹性缓冲（不可压缩）
    remaining_minutes: int = 0                        # 剩余可用分钟 = capacity - load - transit - slack
    day_label: str = "全天活动"                        # 展示标签（从分钟翻译，供报告用）


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
    constraints: "PlanningConstraints | None" = None,
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

    # Step 3: 锁 major activities（constraints-aware: departure_day_no_poi）
    _assign_major_drivers(frames, selected_majors, hotel_bases, constraints=constraints)

    # Step 3b: 识别特殊日类型（theme_park 等）
    _detect_special_day_types(frames)

    # Step 4: 计算容量和通勤预算
    _calc_capacity_and_budget(frames, pace, arrival_day_half, departure_day_half)

    # Step 5: 设定 meal_windows（constraints-aware）
    _set_meal_windows(frames, wake_up_time, constraints=constraints)

    # Step 6: 标记 intensity（constraints-aware）
    _mark_intensity(frames, pace, constraints=constraints)

    # Step 7: 生成标题提示
    _generate_title_hints(frames)

    result.frames = frames
    _constraints_tag = f", constraints.max_intensity={constraints.max_intensity}" if constraints else ""
    result.trace.append(
        f"skeleton: {duration_days} days, "
        f"{len(selected_majors)} majors assigned, "
        f"pace={pace}{_constraints_tag}"
    )
    for f in frames:
        result.trace.append(
            f"  day{f.day_index} [{f.day_type}] "
            f"sleep={f.sleep_base} corridor={f.primary_corridor} "
            f"driver={f.main_driver or 'none'} "
            f"cap={f.day_capacity_units} intensity={f.intensity} | "
            f"capacity={f.daily_capacity_minutes}min "
            f"load={f.activity_load_minutes}min "
            f"transit={f.transit_minutes}min "
            f"slack={f.slack_minutes}min "
            f"remaining={f.remaining_minutes}min "
            f"[{f.day_label}]"
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
    constraints=None,
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
        """返程日 cluster 白名单：只允许轻量/半日类活动，禁止以下类型"""
        name_lower = name.lower()
        cid_lower = cid.lower()
        # 禁止：夜游、夜市、主题公园、美食街、重度观光
        blocked_name_kw = ["夜游", "夜市", "night", "美食街", "道顿堀", "namba", "食道"]
        blocked_cid_kw = ["night", "themepark", "usj", "food_night", "namba_food"]
        if any(kw in name_lower for kw in blocked_name_kw):
            return False
        if any(kw in cid_lower for kw in blocked_cid_kw):
            return False
        return True

    # 分配 half_day majors：优先 arrival → normal → departure（departure 最后用且有白名单）
    # constraints-aware: departure_day_no_poi=True 时，departure 天完全不接收 major
    _departure_accepts_major = not (constraints and constraints.departure_day_no_poi)
    arrival_slots = [f for f in edge_days if f.day_type == "arrival"]
    departure_slots = [f for f in edge_days if f.day_type == "departure"] if _departure_accepts_major else []
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
        # 降级：优先非 departure slot；如果白名单不通过，departure 不接收
        if chosen is None:
            for day in remaining_slots:
                if day.day_type != "departure":
                    chosen = day
                    break
            # departure 只在 compatible 时才作为最后兜底
            if chosen is None:
                for day in remaining_slots:
                    if day.day_type == "departure" and _is_departure_compatible(cid, name):
                        chosen = day
                        break
            if chosen is None:
                # 完全放弃分配，不强塞进 departure
                logger.warning(
                    "half-day major %s 无合适 slot（不强塞 departure），跳过",
                    cid,
                )
                continue
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
            frame.title_hint = f"返程日 · {_display_area(frame.sleep_base)}周边轻松收尾"
            frame.primary_corridor = frame.sleep_base  # 酒店周边
            frame.notes.append("departure_shape: 仅安排住宿周边轻量活动+午餐，预留返程缓冲")


# ── Step 3b: 特殊日类型检测 ──────────────────────────────────────────────────

_THEME_PARK_KEYWORDS = {"usj", "themepark", "theme_park", "universal", "disney", "disneyland", "disneysea"}

def _detect_special_day_types(frames: list[DayFrame]) -> None:
    """
    在 major drivers 分配后，检测并标记特殊 day_type。
    目前支持：theme_park（USJ / Disney 等主题公园日）
    """
    for frame in frames:
        if frame.day_type not in ("normal",):
            continue  # 不覆盖 arrival/departure
        cid = (frame.main_driver or "").lower()
        name = (frame.main_driver_name or "").lower()
        corridor = (frame.primary_corridor or "").lower()
        if any(kw in cid or kw in name or kw in corridor for kw in _THEME_PARK_KEYWORDS):
            frame.day_type = "theme_park"
            frame.notes.append("theme_park day: 午餐由园区内自行解决，晚餐回住宿周边")


# ── Step 4: 容量和通勤预算 ───────────────────────────────────────────────────

# ── 分钟预算：4 层时间模型常量表 ─────────────────────────────────────────────
#
# daily_capacity_minutes: 用户这一天最多适合活动的分钟数（不含睡眠/早晚梳洗）
# transit_minutes:        当天通勤预算（含换乘、步行缓冲）
# slack_minutes:          弹性缓冲（午休、突发、不可压缩）
#
# pace × day_type 矩阵：
#
#              | arrival | normal | departure | theme_park |
#   relaxed    | 240     | 390    | 180       | 480        |
#   moderate   | 300     | 480    | 240       | 540        |
#   packed     | 360     | 570    | 270       | 600        |
#
# 说明：
#   - arrival/departure 天因交通消耗，可用时间已打折
#   - theme_park 日 daily_capacity 不低（全天在园），但 transit 极低
#   - relaxed pace 对应"轻松型 300-420 分钟"区间

_PACE_DAILY_CAPACITY: dict[str, dict[str, int]] = {
    "relaxed":  {"arrival": 240, "normal": 390,  "departure": 180, "theme_park": 480},
    "moderate": {"arrival": 300, "normal": 480,  "departure": 240, "theme_park": 540},
    "packed":   {"arrival": 360, "normal": 570,  "departure": 270, "theme_park": 600},
}

_PACE_TRANSIT: dict[str, dict[str, int]] = {
    "relaxed":  {"arrival": 60,  "normal": 80,  "departure": 60,  "theme_park": 20},
    "moderate": {"arrival": 90,  "normal": 100, "departure": 90,  "theme_park": 30},
    "packed":   {"arrival": 120, "normal": 120, "departure": 90,  "theme_park": 40},
}

_PACE_SLACK: dict[str, dict[str, int]] = {
    "relaxed":  {"arrival": 120, "normal": 90,  "departure": 120, "theme_park": 90},
    "moderate": {"arrival": 90,  "normal": 75,  "departure": 90,  "theme_park": 60},
    "packed":   {"arrival": 75,  "normal": 60,  "departure": 75,  "theme_park": 45},
}

# 兼容旧逻辑：units 表（保留，供旧消费方使用）
_PACE_CAPACITY = {
    "relaxed": {"arrival": 0.3, "normal": 0.7, "departure": 0.3, "theme_park": 0.1},
    "moderate": {"arrival": 0.5, "normal": 1.0, "departure": 0.5, "theme_park": 0.2},
    "packed": {"arrival": 0.7, "normal": 1.3, "departure": 0.5, "theme_park": 0.3},
}

_PACE_TRANSFER = {
    "relaxed": {"arrival": 60, "normal": 90, "departure": 60, "theme_park": 30},
    "moderate": {"arrival": 90, "normal": 120, "departure": 90, "theme_park": 45},
    "packed": {"arrival": 120, "normal": 150, "departure": 90, "theme_park": 60},
}

# main_driver 类型 → 标准活动占用分钟（无分钟数据时的 fallback 估算）
_DRIVER_LOAD_FALLBACK: dict[str, int] = {
    "full_day":    360,   # 全天主活动（如 USJ）
    "half_day":    200,   # 半天主活动（如伏见稻荷）
    "quarter_day": 100,   # 轻量活动
}


def _calc_capacity_and_budget(
    frames: list[DayFrame],
    pace: str,
    arrival_half: bool,
    departure_half: bool,
) -> None:
    """
    计算每天的时间预算（分钟模型 + 兼容 units 模型）。

    分钟模型（主）：
      daily_capacity_minutes  — 用户今天可用活动总分钟
      activity_load_minutes   — main_driver 已占用分钟
      transit_minutes         — 通勤预算
      slack_minutes           — 弹性缓冲
      remaining_minutes       — 剩余可填入次要活动的分钟数

    units 模型（兼容保留）：
      day_capacity_units / transfer_budget_minutes — 旧逻辑用
    """
    pace_key = pace if pace in _PACE_DAILY_CAPACITY else "moderate"
    cap_map  = _PACE_DAILY_CAPACITY[pace_key]
    trans_map = _PACE_TRANSIT[pace_key]
    slack_map = _PACE_SLACK[pace_key]

    # 旧 units 兼容
    old_cap_map   = _PACE_CAPACITY[pace_key]
    old_trans_map = _PACE_TRANSFER[pace_key]

    for frame in frames:
        dtype = frame.day_type if frame.day_type in cap_map else "normal"

        # ── 分钟模型 ──────────────────────────────────────────────────────
        frame.daily_capacity_minutes = cap_map[dtype]
        frame.transit_minutes        = trans_map[dtype]
        frame.slack_minutes          = slack_map[dtype]

        # main_driver 的活动占用分钟
        if frame.main_driver:
            # 优先读 RankedMajor 上的 activity_load_minutes（由 ranker 从 cluster 读取）
            # 这里 frame 只存了 cluster_id，实际分钟数由 ranker 注入到 frame 上
            # 若未注入（=0），用 default_duration 推断 fallback
            if frame.activity_load_minutes <= 0:
                # 从活动簇找 default_duration 做 fallback
                dur_key = "full_day"  # 无法在此拿到 cluster 对象，用保守估算
                frame.activity_load_minutes = _DRIVER_LOAD_FALLBACK.get(dur_key, 360)
        else:
            frame.activity_load_minutes = 0

        # remaining = capacity - load - transit - slack（下限为 0）
        frame.remaining_minutes = max(0,
            frame.daily_capacity_minutes
            - frame.activity_load_minutes
            - frame.transit_minutes
            - frame.slack_minutes
        )

        # 展示标签（从 daily_capacity_minutes 翻译）
        frame.day_label = minutes_to_day_label(frame.daily_capacity_minutes)

        # ── units 兼容模型 ────────────────────────────────────────────────
        frame.day_capacity_units = old_cap_map[dtype]
        frame.transfer_budget_minutes = old_trans_map[dtype]
        if frame.main_driver:
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
    constraints=None,
) -> None:
    bf_early, bf_late = _WAKE_BREAKFAST.get(wake_up, _WAKE_BREAKFAST["normal"])

    # constraints-aware: 读取 departure/arrival 餐次约束
    dep_meal_window = "breakfast_only"   # 默认：仅早餐
    arrival_evening_only = False
    if constraints:
        dep_meal_window = constraints.departure_meal_window
        arrival_evening_only = constraints.arrival_evening_only

    for frame in frames:
        meals = []

        if frame.day_type == "departure":
            # ── 返程日餐次由 departure_meal_window 控制 ──
            if dep_meal_window in ("breakfast_only", "breakfast_lunch"):
                meals.append(MealWindow(
                    meal_type="breakfast",
                    earliest=bf_early, latest=bf_late,
                    style_hint="quick",
                ))
            if dep_meal_window == "breakfast_lunch":
                meals.append(MealWindow(
                    meal_type="lunch",
                    earliest=_LUNCH_WINDOW[0], latest=_LUNCH_WINDOW[1],
                    style_hint="route_meal",
                ))
            # dep_meal_window == "none" → 不排任何餐
            # departure 日永远不给 dinner
        elif frame.day_type == "arrival":
            # ── 到达日：如果 evening_only，只给 dinner ──
            if arrival_evening_only:
                meals.append(MealWindow(
                    meal_type="dinner",
                    earliest=_DINNER_WINDOW[0], latest=_DINNER_WINDOW[1],
                    style_hint="route_meal",
                ))
            else:
                # 正常到达日：lunch + dinner（不给 breakfast）
                meals.append(MealWindow(
                    meal_type="lunch",
                    earliest=_LUNCH_WINDOW[0], latest=_LUNCH_WINDOW[1],
                    style_hint="route_meal",
                ))
                meals.append(MealWindow(
                    meal_type="dinner",
                    earliest=_DINNER_WINDOW[0], latest=_DINNER_WINDOW[1],
                    style_hint="route_meal",
                ))
        elif frame.day_type == "theme_park":
            # breakfast + park_meal lunch + dinner
            meals.append(MealWindow(
                meal_type="breakfast",
                earliest=bf_early, latest=bf_late,
                style_hint="quick",
            ))
            meals.append(MealWindow(
                meal_type="lunch",
                earliest=_LUNCH_WINDOW[0], latest=_LUNCH_WINDOW[1],
                style_hint="park_meal",
            ))
            meals.append(MealWindow(
                meal_type="dinner",
                earliest=_DINNER_WINDOW[0], latest=_DINNER_WINDOW[1],
                style_hint="destination_meal",
            ))
        else:
            # normal day: breakfast + lunch + dinner
            meals.append(MealWindow(
                meal_type="breakfast",
                earliest=bf_early, latest=bf_late,
                style_hint="quick",
            ))
            meals.append(MealWindow(
                meal_type="lunch",
                earliest=_LUNCH_WINDOW[0], latest=_LUNCH_WINDOW[1],
                style_hint="route_meal",
            ))
            meals.append(MealWindow(
                meal_type="dinner",
                earliest=_DINNER_WINDOW[0], latest=_DINNER_WINDOW[1],
                style_hint="route_meal",
            ))

        frame.meal_windows = meals


# ── Step 6: Intensity ─────────────────────────────────────────────────────────

def _mark_intensity(frames: list[DayFrame], pace: str, constraints=None) -> None:
    # 用户节奏 → 全局强度上限映射
    _PACE_INTENSITY_CAP = {
        "relaxed": "balanced",   # relaxed 用户: 最多 balanced，不允许 dense
        "moderate": "dense",     # moderate: 不限
        "packed": "dense",       # packed: 不限
    }
    cap = _PACE_INTENSITY_CAP.get(pace, "dense")
    _ORDER = {"light": 0, "balanced": 1, "dense": 2}

    # constraints-aware: 如果 constraints 提供了 max_intensity，取更严格的上限
    if constraints:
        from app.domains.planning.constraint_compiler import max_allowed_intensity_name
        cc_cap = max_allowed_intensity_name(constraints)
        if _ORDER.get(cc_cap, 2) < _ORDER.get(cap, 2):
            logger.info(
                "intensity cap tightened by constraints: %s → %s (max_intensity=%d)",
                cap, cc_cap, constraints.max_intensity,
            )
            cap = cc_cap

    for frame in frames:
        if frame.day_type in ("arrival", "departure"):
            raw = "light"
        elif frame.day_type == "theme_park":
            raw = "dense"  # 主题公园日天然密集
        elif pace == "relaxed":
            raw = "light" if not frame.main_driver else "balanced"
        elif pace == "packed":
            raw = "dense"
        else:
            raw = "balanced"

        # 用 pace cap 截断：relaxed 用户的 theme_park dense → balanced
        if _ORDER.get(raw, 1) > _ORDER.get(cap, 2):
            raw = cap

        frame.intensity = raw

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

# 走廊 key → 中文展示名（Authority Bare Keys，与 DB primary_corridor 一一对应）
_CORRIDOR_DISPLAY = {
    # ── 京都 ──────────────────────────────────────────────
    "arashiyama":       "岚山·嵯峨野",
    "daigo":            "醍醐（醍醐寺·山樱）",
    "fushimi":          "伏见（稻荷·酒藏）",
    "gion":             "祇园·花见小路",
    "gosho":            "御所·西阵·二条",
    "higashiyama":      "东山（清水寺·祇园）",
    "kawaramachi":      "河原町·四条",
    "kinugasa":         "衣笠（金阁寺·龙安寺）",
    "kita_ku":          "北区（大德寺·上贺茂）",
    "nijo":             "二条城·西阵",
    "nishikyo":         "西京（桂离宫·松尾大社）",
    "okazaki":          "冈崎·哲学之道",
    "philosopher_path": "哲学之道·南禅寺",
    "zen_garden":       "枯山水庭园线",
    "uji":              "宇治（平等院·抹茶）",
    # ── 大阪 ──────────────────────────────────────────────
    "namba":            "难波·道顿堀·心斋桥",
    "osakajo":          "大阪城·天满桥",
    "sakurajima":       "此花·USJ",
    "shinsekai":        "新世界·天王寺",
    "osa_nakanoshima":  "中之岛·北滨",
    "tsuruhashi":       "鹤桥·生野韩国城",
    # ── 奈良 / 神户 / 其他 ───────────────────────────────
    "nara_park":        "奈良公园·东大寺",
    "kobe_kitano":      "神户·北野·南京町",
    "arima":            "有马温泉",
    "shiga":            "滋贺（MIHO 美术馆）",
}

_CITY_DISPLAY = {
    "kyoto": "京都",
    "osaka": "大阪",
    "nara": "奈良",
    "kobe": "神户",
    "tokyo": "东京",
}


def _display_area(area: str) -> str:
    return _AREA_DISPLAY.get(area, area)


def display_corridor(corridor: str) -> str:
    """走廊 key → 中文展示名（供 PDF / API 使用）。"""
    return _CORRIDOR_DISPLAY.get(corridor, _AREA_DISPLAY.get(corridor, corridor))


def display_city(city_code: str) -> str:
    """city_code → 中文展示名。"""
    return _CITY_DISPLAY.get(city_code, city_code)


# departure 日标题白名单关键词（不允许出现夜游/美食街等主题）
_DEPARTURE_TITLE_BLOCKED = {"夜游", "夜市", "美食夜", "night", "nightlife", "bar"}


def _generate_title_hints(frames: list[DayFrame]) -> None:
    for frame in frames:
        parts = []
        if frame.day_type == "arrival":
            parts.append("到达日")
        elif frame.day_type == "departure":
            parts.append("返程日")

        if frame.main_driver_name:
            driver_name = frame.main_driver_name
            # departure 日：如果 driver name 含有不合适的关键词，用走廊 display 替代
            if frame.day_type == "departure":
                name_lower = driver_name.lower()
                if any(kw in name_lower for kw in _DEPARTURE_TITLE_BLOCKED):
                    driver_name = ""  # 抑制，用下面的走廊兜底
                    frame.notes.append(f"departure title: 抑制不合适的 driver name '{frame.main_driver_name}'")
            if driver_name:
                parts.append(driver_name)
        
        # 走廊展示名（转中文）
        if not frame.main_driver_name or (frame.day_type == "departure" and len(parts) <= 1):
            if frame.primary_corridor:
                corr_display = display_corridor(frame.primary_corridor)
                parts.append(corr_display)

        if frame.sleep_base and frame.day_type not in ("departure",):
            parts.append(f"住{_display_area(frame.sleep_base)}")

        # departure 日加固定后缀
        if frame.day_type == "departure" and not any("周边" in p or "收尾" in p for p in parts):
            parts.append("轻松收尾")

        frame.title_hint = " · ".join(parts) if parts else f"Day {frame.day_index}"


# ── 展示翻译：分钟 → 人类可读标签 ───────────────────────────────────────────

def minutes_to_day_label(minutes: int) -> str:
    """
    将「今日可用活动分钟数」翻译为人类可读的节奏标签。

    分级标准（对应用户侧认知）：
      0–120   → 轻量补位（到达夜 / 返程晨）
      121–240 → 短活动（半天不足）
      241–360 → 半天活动
      361–480 → 强半天 / 弱全天
      481+    → 全天活动

    注意：这是「展示输出」，不用于内部调度逻辑。
    """
    if minutes <= 120:
        return "轻量补位"
    elif minutes <= 240:
        return "短活动"
    elif minutes <= 360:
        return "半天活动"
    elif minutes <= 480:
        return "强半天"
    else:
        return "全天活动"


def minutes_to_intensity_hint(remaining: int) -> str:
    """
    将剩余可用分钟翻译为节奏提示（供报告/AI 文案使用）。

      > 150  → 偏轻松（还有大量余量）
      90–150 → 节奏平衡
      30–89  → 偏紧凑
      < 30   → 极紧凑，不建议再塞活动
    """
    if remaining > 150:
        return "偏轻松"
    elif remaining >= 90:
        return "节奏平衡"
    elif remaining >= 30:
        return "偏紧凑"
    else:
        return "极紧凑"

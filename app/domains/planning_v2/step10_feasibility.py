"""
step10_feasibility.py — 可行性硬约束检查

检查 Step 9 输出的每日活动序列是否满足所有时间和逻辑约束。

检查规则（按优先级）：
  1. 时间重叠检查（HARD FAIL）— buffer/slack/free_time 块不参与
  2. 营业时间/定休日检查（HARD FAIL）
  3. 通勤可行性（WARNING）
  4. 日出/日落约束（WARNING）
  5. 餐食冲突检查（WARNING）
  6. 总时间检查（WARNING）— buffer/commute 块不计入活动时间

buffer 类型说明：
  Step 9 会在时间线中插入缓冲块（type="buffer"/"slack"/"free_time"），
  这些是有意留白（排队/机动/休息时间），不算真实活动时间。

纯 Python，所有数据通过参数传入，不需要数据库调用。
"""

import json
import logging
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from app.domains.planning_v2.models import DailyConstraints, FeasibilityResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Severity constants
# ---------------------------------------------------------------------------
FAIL = "fail"
WARNING = "warning"

# Outdoor-related activity types / tags
OUTDOOR_TYPES = {"park", "garden", "shrine", "temple", "beach", "hiking", "viewpoint"}
OUTDOOR_TAGS = {"outdoor", "nature", "garden", "hiking", "park", "beach", "scenic"}

# Buffer/slack block types (not counted as active time, not checked for overlap)
BUFFER_TYPES = {"buffer", "slack", "free_time", "flex_meal", "rest", "commute"}

# Meal-related activity types
BREAKFAST_TYPES = {"breakfast", "morning_cafe"}
DINNER_TYPES = {"dinner", "izakaya", "kaiseki"}

# Meal time windows (HH:MM)
BREAKFAST_WINDOW = ("06:00", "09:30")
DINNER_WINDOW = ("17:00", "21:30")

# Max recommended active hours per day (excluding commute)
MAX_ACTIVE_HOURS = 10


def _build_sub_type_to_bucket() -> dict[str, str]:
    """从 taxonomy.json 的 experience_buckets 构建 sub_type → bucket 映射。"""
    mapping: dict[str, str] = {}
    # 搜索所有圈的 taxonomy（取第一个有 experience_buckets 的）
    data_dir = Path(__file__).resolve().parents[3] / "data"
    for config_dir in data_dir.glob("*/config/taxonomy.json"):
        try:
            with open(config_dir, encoding="utf-8") as f:
                tax = json.load(f)
            buckets = tax.get("experience_buckets", {})
            for bucket_id, bucket_def in buckets.items():
                if bucket_id.startswith("_"):
                    continue
                for st in bucket_def.get("sub_types", []):
                    mapping[st] = bucket_id
            if mapping:
                return mapping
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return mapping


_SUB_TYPE_TO_BUCKET: dict[str, str] = _build_sub_type_to_bucket()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_time(hhmm: str) -> datetime:
    """Parse HH:MM string to a datetime (date part is arbitrary 2000-01-01)."""
    return datetime.strptime(hhmm, "%H:%M").replace(year=2000, month=1, day=1)


def _add_minutes(hhmm: str, mins: int) -> datetime:
    """Parse HH:MM and add minutes."""
    return _parse_time(hhmm) + timedelta(minutes=mins)


def _minutes_between(start: str, end: str) -> int:
    """Return minutes between two HH:MM strings."""
    delta = _parse_time(end) - _parse_time(start)
    return int(delta.total_seconds() / 60)


def _is_buffer_block(activity: dict) -> bool:
    """Check if this is a buffer/slack/free-time block (intentional gap)."""
    atype = (activity.get("type") or "").lower()
    if atype in BUFFER_TYPES:
        return True
    # Also check the optional flag from Step 9
    return activity.get("is_buffer", False)


def _is_outdoor(activity: dict) -> bool:
    """Heuristic: is this activity an outdoor one?"""
    atype = (activity.get("type") or "").lower()
    if atype in OUTDOOR_TYPES:
        return True
    tags = [t.lower() for t in (activity.get("tags") or [])]
    return bool(OUTDOOR_TAGS & set(tags))


def _is_meal_in_window(activity: dict, window_start: str, window_end: str) -> bool:
    """Check if an activity's time overlaps with a meal window."""
    act_start = _parse_time(activity["start_time"])
    act_end = _parse_time(activity["end_time"])
    win_start = _parse_time(window_start)
    win_end = _parse_time(window_end)
    return act_start < win_end and act_end > win_start


def _is_breakfast_activity(activity: dict) -> bool:
    """Heuristic: does this activity look like an external breakfast/morning cafe?"""
    atype = (activity.get("type") or "").lower()
    if atype in BREAKFAST_TYPES:
        return True
    if atype == "restaurant" and _is_meal_in_window(activity, *BREAKFAST_WINDOW):
        name = (activity.get("name") or "").lower()
        if any(kw in name for kw in ("朝食", "早餐", "morning", "breakfast", "モーニング")):
            return True
    return False


def _is_dinner_activity(activity: dict) -> bool:
    """Heuristic: does this activity look like an external dinner?"""
    atype = (activity.get("type") or "").lower()
    if atype in DINNER_TYPES:
        return True
    if atype == "restaurant" and _is_meal_in_window(activity, *DINNER_WINDOW):
        name = (activity.get("name") or "").lower()
        if any(kw in name for kw in ("夕食", "晚餐", "dinner", "ディナー", "居酒屋")):
            return True
    return False


def _detect_bucket_from_activities(day_seq: dict) -> str:
    """从一天的活动列表推断主体验桶。

    统计所有非 buffer 活动的 tags 命中哪个 bucket 最多，返回该 bucket。
    无法判断时返回 "unknown"。
    """
    bucket_counts: Counter[str] = Counter()
    for act in day_seq.get("activities", []):
        if _is_buffer_block(act):
            continue
        tags = [t.lower() for t in (act.get("tags") or [])]
        sub_type = (act.get("sub_type") or "").lower()
        # 先用 sub_type 直接映射
        if sub_type in _SUB_TYPE_TO_BUCKET:
            bucket_counts[_SUB_TYPE_TO_BUCKET[sub_type]] += 1
        # 再用 tags 映射（一个 tag 可能命中）
        for tag in tags:
            if tag in _SUB_TYPE_TO_BUCKET:
                bucket_counts[_SUB_TYPE_TO_BUCKET[tag]] += 1
    if not bucket_counts:
        return "unknown"
    return bucket_counts.most_common(1)[0][0]


def _get_constraints_for_date(
    date_str: str,
    daily_constraints: list[DailyConstraints],
) -> DailyConstraints | None:
    """Find DailyConstraints matching a given date string."""
    for dc in daily_constraints:
        if dc.date == date_str:
            return dc
    return None


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def _check_time_overlap(day_seq: dict, violations: list) -> None:
    """Rule 1: 同一天内活动时间窗不能重叠（HARD FAIL）

    Buffer/slack/free_time 类型的时间块允许与相邻活动重叠（它们是有意留白）。
    只检查"真实活动"之间的重叠。
    """
    activities = day_seq.get("activities", [])
    day = day_seq.get("day")
    for i in range(len(activities)):
        for j in range(i + 1, len(activities)):
            a = activities[i]
            b = activities[j]
            # 缓冲块不参与重叠检查
            if _is_buffer_block(a) or _is_buffer_block(b):
                continue
            a_start = _parse_time(a["start_time"])
            a_end = _parse_time(a["end_time"])
            b_start = _parse_time(b["start_time"])
            b_end = _parse_time(b["end_time"])
            if a_end > b_start and a_start < b_end:
                violations.append(
                    {
                        "severity": FAIL,
                        "type": "time_overlap",
                        "day": day,
                        "entity_id": f"{a.get('entity_id')} & {b.get('entity_id')}",
                        "reason": (
                            f"时间重叠: {a['name']}({a['start_time']}-{a['end_time']}) "
                            f"与 {b['name']}({b['start_time']}-{b['end_time']})"
                        ),
                    }
                )


def _check_closed_entities(
    day_seq: dict,
    dc: DailyConstraints | None,
    violations: list,
) -> None:
    """Rule 2 & 5: 关闭/定休日实体不能安排（HARD FAIL）"""
    if dc is None:
        return
    closed_set = set(dc.closed_entities)
    if not closed_set:
        return
    day = day_seq.get("day")
    for act in day_seq.get("activities", []):
        eid = act.get("entity_id")
        if eid and eid in closed_set:
            violations.append(
                {
                    "severity": FAIL,
                    "type": "closed_entity",
                    "day": day,
                    "entity_id": eid,
                    "reason": f"定休日/临时关闭: {act['name']} 在 {dc.date} 不可用",
                }
            )


def _check_commute_feasibility(day_seq: dict, violations: list) -> None:
    """Rule 3: 通勤时间是否足够（WARNING）"""
    activities = day_seq.get("activities", [])
    day = day_seq.get("day")
    for i in range(1, len(activities)):
        prev = activities[i - 1]
        curr = activities[i]
        commute_mins = curr.get("commute_from_prev_mins", 0)
        if commute_mins <= 0:
            continue
        prev_end = _parse_time(prev["end_time"])
        curr_start = _parse_time(curr["start_time"])
        available = (curr_start - prev_end).total_seconds() / 60
        if available < commute_mins:
            violations.append(
                {
                    "severity": WARNING,
                    "type": "commute_infeasible",
                    "day": day,
                    "entity_id": curr.get("entity_id"),
                    "reason": (
                        f"通勤时间不足: {prev['name']} {prev['end_time']} → "
                        f"{curr['name']} {curr['start_time']}，"
                        f"需要 {commute_mins} 分钟但仅有 {int(available)} 分钟间隔"
                    ),
                }
            )


def _check_daylight(
    day_seq: dict,
    dc: DailyConstraints | None,
    violations: list,
) -> None:
    """Rule 4: 户外活动日出/日落约束（WARNING）"""
    if dc is None:
        return
    day = day_seq.get("day")
    sunrise = _parse_time(dc.sunrise)
    sunset_buffer = _parse_time(dc.sunset) + timedelta(minutes=30)
    for act in day_seq.get("activities", []):
        if not _is_outdoor(act):
            continue
        act_start = _parse_time(act["start_time"])
        act_end = _parse_time(act["end_time"])
        if act_start < sunrise:
            violations.append(
                {
                    "severity": WARNING,
                    "type": "before_sunrise",
                    "day": day,
                    "entity_id": act.get("entity_id"),
                    "reason": (
                        f"日出前户外活动: {act['name']} {act['start_time']} 开始，"
                        f"但日出在 {dc.sunrise}"
                    ),
                }
            )
        if act_end > sunset_buffer:
            violations.append(
                {
                    "severity": WARNING,
                    "type": "after_sunset",
                    "day": day,
                    "entity_id": act.get("entity_id"),
                    "reason": (
                        f"日落后户外活动: {act['name']} {act['end_time']} 结束，"
                        f"但日落+30min 在 {dc.sunset}+30min"
                    ),
                }
            )


def _check_meal_conflict(
    day_seq: dict,
    dc: DailyConstraints | None,
    violations: list,
) -> None:
    """Rule 6: 酒店包餐与外部餐食冲突（WARNING）"""
    if dc is None:
        return
    day = day_seq.get("day")
    for act in day_seq.get("activities", []):
        if dc.hotel_breakfast_included and _is_breakfast_activity(act):
            violations.append(
                {
                    "severity": WARNING,
                    "type": "meal_conflict_breakfast",
                    "day": day,
                    "entity_id": act.get("entity_id"),
                    "reason": (
                        f"酒店已含早餐但安排了外部早餐: {act['name']} "
                        f"({act['start_time']}-{act['end_time']})"
                    ),
                }
            )
        if dc.hotel_dinner_included and _is_dinner_activity(act):
            violations.append(
                {
                    "severity": WARNING,
                    "type": "meal_conflict_dinner",
                    "day": day,
                    "entity_id": act.get("entity_id"),
                    "reason": (
                        f"酒店已含晚餐但安排了外部晚餐: {act['name']} "
                        f"({act['start_time']}-{act['end_time']})"
                    ),
                }
            )


def _check_total_active_time(day_seq: dict, violations: list) -> None:
    """Rule 7: 一天总活动时间不超过上限（WARNING）

    Buffer/slack/commute 块不计入活动时间——它们是有意留白或移动时间。
    """
    activities = day_seq.get("activities", [])
    day = day_seq.get("day")
    total_mins = 0
    for act in activities:
        if _is_buffer_block(act):
            continue  # 缓冲块不计入活动时间
        mins = _minutes_between(act["start_time"], act["end_time"])
        total_mins += max(mins, 0)
    total_hours = total_mins / 60
    if total_hours > MAX_ACTIVE_HOURS:
        violations.append(
            {
                "severity": WARNING,
                "type": "overloaded_day",
                "day": day,
                "entity_id": None,
                "reason": (
                    f"体力过高: 第 {day} 天总活动时间 {total_hours:.1f} 小时，"
                    f"超过推荐上限 {MAX_ACTIVE_HOURS} 小时"
                ),
            }
        )


def _check_consecutive_same_bucket(
    daily_sequences: list[dict],
    violations: list,
) -> None:
    """连续 3 天主体验桶相同时标 warning，避免审美疲劳。"""
    if len(daily_sequences) < 3:
        return
    # 按 day 排序，确保顺序正确
    sorted_seqs = sorted(daily_sequences, key=lambda s: s.get("day", 0))
    buckets = [_detect_bucket_from_activities(ds) for ds in sorted_seqs]
    days = [ds.get("day") for ds in sorted_seqs]

    for i in range(len(buckets) - 2):
        b = buckets[i]
        if b == "unknown":
            continue
        if buckets[i] == buckets[i + 1] == buckets[i + 2]:
            violations.append(
                {
                    "type": "consecutive_same_bucket",
                    "severity": WARNING,
                    "day": days[i + 1],
                    "entity_id": None,
                    "reason": (f"连续 3 天主体验桶均为 {b}，建议调整以避免审美疲劳"),
                    "bucket": b,
                    "consecutive_days": [days[i], days[i + 1], days[i + 2]],
                }
            )


# ---------------------------------------------------------------------------
# Suggestion generator
# ---------------------------------------------------------------------------


def _generate_suggestions(violations: list) -> list[str]:
    """Generate simple fix suggestions based on violation types."""
    suggestions = []
    types_seen = {v["type"] for v in violations}

    if "time_overlap" in types_seen:
        suggestions.append("调整重叠活动的时间窗或移除其中一项")
    if "closed_entity" in types_seen:
        suggestions.append("将定休日实体移到其他日期或替换为备选")
    if "commute_infeasible" in types_seen:
        suggestions.append("增大活动间隔或缩短前一活动时长以留出通勤时间")
    if "before_sunrise" in types_seen or "after_sunset" in types_seen:
        suggestions.append("将户外活动调整到日出后、日落前的时间段")
    if "meal_conflict_breakfast" in types_seen:
        suggestions.append("酒店已含早餐，考虑去掉外部早餐安排")
    if "meal_conflict_dinner" in types_seen:
        suggestions.append("酒店已含晚餐，考虑去掉外部晚餐安排")
    if "overloaded_day" in types_seen:
        suggestions.append(f"减少当天活动数量，保持总活动时间在 {MAX_ACTIVE_HOURS} 小时内")
    if "consecutive_same_bucket" in types_seen:
        suggestions.append("连续多天安排了同类体验，考虑穿插不同类型活动以丰富行程节奏")

    return suggestions


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def check_feasibility(
    daily_sequences: list[dict],
    daily_constraints: list[DailyConstraints],
) -> FeasibilityResult:
    """
    检查每日活动序列的可行性。

    Args:
        daily_sequences: Step 9 输出的每日活动列表，每项含 day/date/activities。
        daily_constraints: 每日约束列表（DailyConstraints）。

    Returns:
        FeasibilityResult，status 为 pass/fail/warning，附带 violations 和 suggestions。
    """
    violations: list[dict] = []

    for day_seq in daily_sequences:
        date_str = day_seq.get("date", "")
        dc = _get_constraints_for_date(date_str, daily_constraints)

        # Rule 1: 时间重叠
        _check_time_overlap(day_seq, violations)
        # Rule 2 & 5: 关闭/定休日
        _check_closed_entities(day_seq, dc, violations)
        # Rule 3: 通勤可行性
        _check_commute_feasibility(day_seq, violations)
        # Rule 4: 日出/日落
        _check_daylight(day_seq, dc, violations)
        # Rule 6: 餐食冲突
        _check_meal_conflict(day_seq, dc, violations)
        # Rule 7: 总时间
        _check_total_active_time(day_seq, violations)

    # Rule 8: 连续同类体验桶
    _check_consecutive_same_bucket(daily_sequences, violations)

    # Sort: fail first, warning second
    severity_order = {FAIL: 0, WARNING: 1}
    violations.sort(key=lambda v: severity_order.get(v["severity"], 99))

    # Determine overall status
    has_fail = any(v["severity"] == FAIL for v in violations)
    has_warning = any(v["severity"] == WARNING for v in violations)

    if has_fail:
        status = "fail"
    elif has_warning:
        status = "warning"
    else:
        status = "pass"

    suggestions = _generate_suggestions(violations)

    # Log summary
    fail_count = sum(1 for v in violations if v["severity"] == FAIL)
    warn_count = sum(1 for v in violations if v["severity"] == WARNING)
    logger.info(
        "Feasibility check: status=%s, %d fail(s), %d warning(s), %d day(s) checked",
        status,
        fail_count,
        warn_count,
        len(daily_sequences),
    )
    if violations:
        for v in violations:
            log_fn = logger.error if v["severity"] == FAIL else logger.warning
            log_fn("[Day %s] %s: %s", v["day"], v["type"], v["reason"])

    return FeasibilityResult(
        status=status,
        violations=violations,
        suggestions=suggestions,
    )

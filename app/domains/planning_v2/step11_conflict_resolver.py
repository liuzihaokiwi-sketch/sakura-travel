"""
step11_conflict_resolver.py — 冲突处理链

当 Step 10 可行性检查返回 fail/warning 时，执行 4 步冲突处理链：

  11.1  删除模块    — 删除可行性最差的次要活动（纯规则）
  11.2  压缩时间    — 减少 visit_minutes，最多减 20%（纯规则）
  11.3  降级强度    — 仅处理 capacity_overload（总时间超限等体验层问题）
  11.4  AI 回退     — 调用 Opus 重排（仅在 11.1-11.3 都无法解决时）

违规分类：
  - hard_infeasible: 时间重叠、定休日、通勤不足 → 只能删除/重排
  - capacity_overload: 总时间超限、日出日落、餐食冲突 → 可缩减/降级

确定性优先，AI 回退兜底。
"""

import copy
import json
import logging
import re
from datetime import datetime, timedelta

import anthropic

from app.core.config import settings
from app.domains.planning_v2.models import (
    CandidatePool,
    CircleProfile,
    DailyConstraints,
    FeasibilityResult,
)
from app.domains.planning_v2.step10_feasibility import check_feasibility

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GRADE_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3}
INTENSITY_LEVELS = ["heavy", "medium", "light"]
MAX_ACTIVE_HOURS = 10
MAX_COMPRESS_RATIO = 0.20  # 最多压缩 20%
AI_MODEL = "claude-opus-4-0-20250514"
AI_THINKING_BUDGET = 8000
AI_MAX_OUTPUT_TOKENS = 16000

# 不可删除的活动类型
PROTECTED_TYPES = {"anchor", "flight", "hotel_checkin", "hotel_checkout"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_time(hhmm: str) -> datetime:
    """Parse HH:MM to datetime (date part fixed to 2000-01-01)."""
    return datetime.strptime(hhmm, "%H:%M").replace(year=2000, month=1, day=1)


def _format_time(dt: datetime) -> str:
    """Format datetime to HH:MM."""
    return dt.strftime("%H:%M")


def _minutes_between(start: str, end: str) -> int:
    """Minutes between two HH:MM strings."""
    delta = _parse_time(end) - _parse_time(start)
    return int(delta.total_seconds() / 60)


def _total_active_hours(day_seq: dict) -> float:
    """计算一天的总活动小时数。"""
    total_mins = 0
    for act in day_seq.get("activities", []):
        mins = _minutes_between(act["start_time"], act["end_time"])
        total_mins += max(mins, 0)
    return total_mins / 60


def _grade_value(grade: str) -> int:
    """Grade 转数值，越小越重要。"""
    return GRADE_ORDER.get(grade, 4)


def _is_protected(act: dict) -> bool:
    """是否为受保护活动（锚点、航班等）。"""
    act_type = (act.get("type") or "").lower()
    return act_type in PROTECTED_TYPES


def _find_grade_in_pool(
    entity_id: str | None,
    poi_pool: list[CandidatePool],
) -> str:
    """从 poi_pool 中查找实体的 grade。"""
    if not entity_id:
        return "C"
    for p in poi_pool:
        if p.entity_id == entity_id:
            return p.grade
    return "C"


def _find_intensity_in_pool(
    entity_id: str | None,
    poi_pool: list[CandidatePool],
) -> str:
    """从 poi_pool 中推测活动强度。"""
    if not entity_id:
        return "light"
    for p in poi_pool:
        if p.entity_id == entity_id:
            visit = p.visit_minutes
            if visit >= 120:
                return "heavy"
            elif visit >= 60:
                return "medium"
            else:
                return "light"
    return "medium"


def _get_violations_for_day(
    violations: list[dict],
    day: int,
) -> list[dict]:
    """筛选指定天的违规。"""
    return [v for v in violations if v.get("day") == day]


def _get_fail_violations(violations: list[dict]) -> list[dict]:
    """筛选 FAIL 级别的违规。"""
    return [v for v in violations if v.get("severity") == "fail"]


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
# Step 11.1 — 删除模块
# ---------------------------------------------------------------------------


def _step_11_1_delete(
    daily_sequences: list[dict],
    violations: list[dict],
    poi_pool: list[CandidatePool],
    resolution_log: list[dict],
) -> list[dict]:
    """
    11.1 删除模块：删除可行性最差的次要活动。

    规则：
      - 对于 time_overlap：删除 grade 更低的那个活动
      - 对于 closed_entity：直接删除该活动
      - 不删除受保护活动（锚点、航班等）

    Args:
        daily_sequences: 当前每日序列（会被修改）
        violations: FAIL 类型的违规列表
        poi_pool: 候选池（用于查 grade）
        resolution_log: 解决日志（追加）

    Returns:
        修改后的 daily_sequences
    """
    fail_violations = _get_fail_violations(violations)

    for v in fail_violations:
        day = v.get("day")
        v_type = v.get("type")

        # 找到对应天的序列
        day_seq = None
        for ds in daily_sequences:
            if ds.get("day") == day:
                day_seq = ds
                break
        if day_seq is None:
            continue

        activities = day_seq.get("activities", [])

        if v_type == "closed_entity":
            # 直接删除关闭的实体
            entity_id = v.get("entity_id")
            if entity_id:
                before_len = len(activities)
                day_seq["activities"] = [a for a in activities if a.get("entity_id") != entity_id]
                if len(day_seq["activities"]) < before_len:
                    resolution_log.append(
                        {
                            "step": "11.1",
                            "action": f"删除 entity {entity_id}",
                            "day": day,
                            "reason": f"定休日冲突: {v.get('reason', '')}",
                        }
                    )
                    logger.info("11.1: Day %d — 删除定休日实体 %s", day, entity_id)

        elif v_type == "time_overlap":
            # 删除 grade 更低的活动
            entity_str = v.get("entity_id", "")
            if " & " in str(entity_str):
                eid_a, eid_b = str(entity_str).split(" & ", 1)
                grade_a = _find_grade_in_pool(eid_a.strip(), poi_pool)
                grade_b = _find_grade_in_pool(eid_b.strip(), poi_pool)

                # 删除 grade 更低的（数值更大 = 质量更低）
                to_remove = (
                    eid_b.strip()
                    if _grade_value(grade_b) >= _grade_value(grade_a)
                    else eid_a.strip()
                )

                # 不删除受保护活动
                remove_act = next(
                    (a for a in activities if a.get("entity_id") == to_remove),
                    None,
                )
                if remove_act and _is_protected(remove_act):
                    # 如果要删的是受保护的，就删另一个
                    to_remove = eid_a.strip() if to_remove == eid_b.strip() else eid_b.strip()

                before_len = len(activities)
                day_seq["activities"] = [a for a in activities if a.get("entity_id") != to_remove]
                if len(day_seq["activities"]) < before_len:
                    resolution_log.append(
                        {
                            "step": "11.1",
                            "action": f"删除 entity {to_remove}",
                            "day": day,
                            "reason": f"时间冲突，grade 更低: {v.get('reason', '')}",
                        }
                    )
                    logger.info(
                        "11.1: Day %d — 删除时间冲突实体 %s (grade=%s)",
                        day,
                        to_remove,
                        _find_grade_in_pool(to_remove, poi_pool),
                    )

    return daily_sequences


# ---------------------------------------------------------------------------
# Step 11.2 — 压缩时间
# ---------------------------------------------------------------------------


def _step_11_2_compress(
    daily_sequences: list[dict],
    violations: list[dict],
    resolution_log: list[dict],
) -> list[dict]:
    """
    11.2 压缩时间：对于通勤不够的情况，缩短上一活动的时长（最多 20%）。

    Args:
        daily_sequences: 当前每日序列
        violations: 违规列表
        resolution_log: 解决日志

    Returns:
        修改后的 daily_sequences
    """
    commute_violations = [v for v in violations if v.get("type") == "commute_infeasible"]

    for v in commute_violations:
        day = v.get("day")
        target_entity = v.get("entity_id")

        day_seq = None
        for ds in daily_sequences:
            if ds.get("day") == day:
                day_seq = ds
                break
        if day_seq is None:
            continue

        activities = day_seq.get("activities", [])

        # 找到目标活动及其前一个活动
        for i in range(1, len(activities)):
            if activities[i].get("entity_id") == target_entity:
                prev_act = activities[i - 1]
                curr_act = activities[i]

                prev_start = prev_act["start_time"]
                prev_end = prev_act["end_time"]
                visit_mins = _minutes_between(prev_start, prev_end)

                # 最多压缩 20%
                compress_mins = int(visit_mins * MAX_COMPRESS_RATIO)
                if compress_mins < 5:
                    continue  # 压缩量太小，跳过

                # 计算新的 end_time
                new_end_dt = _parse_time(prev_end) - timedelta(minutes=compress_mins)
                new_end = _format_time(new_end_dt)

                old_end = prev_end
                prev_act["end_time"] = new_end

                # 重新计算通勤时间可用空间
                commute_needed = curr_act.get("commute_from_prev_mins", 0)
                available = _minutes_between(new_end, curr_act["start_time"])

                resolution_log.append(
                    {
                        "step": "11.2",
                        "action": (
                            f"压缩 {prev_act.get('name', '?')} end_time "
                            f"{old_end} → {new_end} (减少 {compress_mins} 分钟)"
                        ),
                        "day": day,
                        "reason": (
                            f"通勤时间不足: 需要 {commute_needed} 分钟，压缩后可用 {available} 分钟"
                        ),
                    }
                )
                logger.info(
                    "11.2: Day %d — 压缩 %s end_time %s → %s (-%d min)",
                    day,
                    prev_act.get("name", "?"),
                    old_end,
                    new_end,
                    compress_mins,
                )
                break

    return daily_sequences


# ---------------------------------------------------------------------------
# Step 11.3 — 降级强度
# ---------------------------------------------------------------------------


def _classify_violations(
    violations: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    将违规分为两类：

    - hard_infeasible: 物理不可行（时间重叠、定休日关闭、通勤时间不足）
      → 只能通过删除/重排解决，降 intensity 标签无效
    - capacity_overload: 体验层超载（总活动时间超限、日出日落、餐食冲突）
      → 可以通过缩短停留、降级强度、移除次要活动解决

    Returns:
        (hard_infeasible, capacity_overload) 两个列表
    """
    HARD_TYPES = {"time_overlap", "closed_entity", "commute_infeasible"}

    hard = [v for v in violations if v.get("type") in HARD_TYPES]
    capacity = [v for v in violations if v.get("type") not in HARD_TYPES]
    return hard, capacity


def _step_11_3_downgrade(
    daily_sequences: list[dict],
    violations: list[dict],
    poi_pool: list[CandidatePool],
    resolution_log: list[dict],
) -> list[dict]:
    """
    11.3 降级强度：仅处理 capacity_overload 类型的违规。

    对于 hard_infeasible（时间重叠、定休日、通勤不足），降 intensity 标签
    不能改变物理事实，跳过不处理（留给 11.4 AI 回退）。

    对于 capacity_overload（总时间超限等）：
      1. 如果有 2+ 个 heavy 活动：将 grade 最低的 heavy 缩减 visit_minutes 30%
      2. 否则：移除 grade 最低的非受保护活动

    Args:
        daily_sequences: 当前每日序列
        violations: 当前违规列表（用于分类判断）
        poi_pool: 候选池
        resolution_log: 解决日志

    Returns:
        修改后的 daily_sequences
    """
    hard, capacity = _classify_violations(violations)

    if hard:
        logger.info(
            "11.3: 跳过 %d 个 hard_infeasible 违规（需 11.4 AI 重排解决）: %s",
            len(hard),
            [f"Day{v.get('day')}/{v.get('type')}" for v in hard],
        )

    # 只处理有 overloaded_day 的天
    overloaded_days = set()
    for v in capacity:
        if v.get("type") == "overloaded_day":
            overloaded_days.add(v.get("day"))

    if not overloaded_days:
        logger.info("11.3: 无 capacity_overload 违规，跳过")
        return daily_sequences

    for day_seq in daily_sequences:
        day = day_seq.get("day")
        if day not in overloaded_days:
            continue

        active_hours = _total_active_hours(day_seq)
        activities = day_seq.get("activities", [])
        logger.info(
            "11.3: Day %d — 总活动时间 %.1f 小时 > %d，需要降级（capacity_overload）",
            day,
            active_hours,
            MAX_ACTIVE_HOURS,
        )

        # 统计 heavy 活动
        heavy_acts = []
        for act in activities:
            if _is_protected(act):
                continue
            intensity = _find_intensity_in_pool(act.get("entity_id"), poi_pool)
            if intensity == "heavy":
                heavy_acts.append(act)

        if len(heavy_acts) >= 2:
            # 策略 1: 将 grade 最低的 heavy 活动缩减 visit_minutes
            heavy_acts.sort(
                key=lambda a: _grade_value(_find_grade_in_pool(a.get("entity_id"), poi_pool)),
                reverse=True,
            )
            target = heavy_acts[0]
            old_end = target["end_time"]
            visit_mins = _minutes_between(target["start_time"], target["end_time"])

            # 缩减到原来的 70%
            new_visit = int(visit_mins * 0.7)
            new_end_dt = _parse_time(target["start_time"]) + timedelta(minutes=new_visit)
            target["end_time"] = _format_time(new_end_dt)

            resolution_log.append(
                {
                    "step": "11.3",
                    "action": (
                        f"缩减 {target.get('name', '?')} visit_minutes "
                        f"end_time {old_end} → {target['end_time']} "
                        f"(visit {visit_mins} → {new_visit} min)"
                    ),
                    "day": day,
                    "reason": (
                        f"capacity_overload: 总活动时间 {active_hours:.1f}h > {MAX_ACTIVE_HOURS}h"
                    ),
                }
            )
            logger.info(
                "11.3: Day %d — 缩减 %s: visit %d → %d min",
                day,
                target.get("name", "?"),
                visit_mins,
                new_visit,
            )

        else:
            # 策略 2: 移除 grade 最低的非受保护活动
            removable = [a for a in activities if not _is_protected(a)]
            if not removable:
                logger.warning("11.3: Day %d — 所有活动均受保护，无法降级", day)
                continue

            removable.sort(
                key=lambda a: _grade_value(_find_grade_in_pool(a.get("entity_id"), poi_pool)),
                reverse=True,
            )
            to_remove = removable[0]
            day_seq["activities"] = [
                a
                for a in activities
                if a.get("entity_id") != to_remove.get("entity_id")
                or (a.get("entity_id") is None and a is not to_remove)
            ]

            eid = to_remove.get("entity_id")
            resolution_log.append(
                {
                    "step": "11.3",
                    "action": (f"移除 {to_remove.get('name', '?')} (entity={eid})"),
                    "day": day,
                    "reason": (
                        f"capacity_overload: 总活动时间 {active_hours:.1f}h > {MAX_ACTIVE_HOURS}h"
                    ),
                }
            )
            logger.info(
                "11.3: Day %d — 移除 %s (grade=%s)",
                day,
                to_remove.get("name", "?"),
                _find_grade_in_pool(to_remove.get("entity_id"), poi_pool),
            )

    return daily_sequences


# ---------------------------------------------------------------------------
# Step 11.4 — AI 回退
# ---------------------------------------------------------------------------


def _build_ai_retry_prompt(
    day_seq: dict,
    constraints: DailyConstraints,
    violations: list[dict],
) -> str:
    """为 11.4 AI 回退构建 prompt，包含冲突信息。"""
    parts = []

    parts.append(f"## 重新排序请求：第 {day_seq.get('day')} 天 ({day_seq.get('date')})")
    parts.append("")
    parts.append(f"日出: {constraints.sunrise}")
    parts.append(f"日落: {constraints.sunset}")

    if constraints.hotel_breakfast_included:
        parts.append("酒店含早餐: 是")
    if constraints.hotel_dinner_included:
        parts.append("酒店含晚餐: 是")
    parts.append("")

    # 当前活动
    parts.append("### 当前活动（需要重新排序）")
    for act in day_seq.get("activities", []):
        parts.append(
            f"- {act.get('name', '?')} ({act.get('type', '?')}, "
            f"{act.get('start_time', '?')}-{act.get('end_time', '?')})"
        )
    parts.append("")

    # 冲突信息
    day = day_seq.get("day")
    day_violations = [v for v in violations if v.get("day") == day]
    if day_violations:
        parts.append("### 已知冲突（必须解决）")
        for v in day_violations:
            sev = v.get("severity", "?")
            vtype = v.get("type", "?")
            reason = v.get("reason", "?")
            parts.append(f"- [{sev}] {vtype}: {reason}")
        parts.append("")

    parts.append("### 要求")
    parts.append("请重新排序以上活动，解决所有冲突。")
    parts.append("如果无法在时间内安排所有活动，可以删除 grade 最低的活动。")
    parts.append("输出严格 JSON 格式，与原输入结构相同。")

    return "\n".join(parts)


def _extract_json(text: str) -> dict:
    """从 AI 输出中提取 JSON（复用 step09 的逻辑）。"""
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从 AI 输出中提取有效 JSON，原文前 500 字符：{text[:500]}")


async def _step_11_4_ai_fallback(
    daily_sequences: list[dict],
    violations: list[dict],
    daily_constraints: list[DailyConstraints],
    resolution_log: list[dict],
    api_key: str,
    circle: CircleProfile,
) -> tuple[list[dict], int]:
    """
    11.4 AI 回退：对仍有冲突的天调用 Opus 重排。

    Args:
        daily_sequences: 当前每日序列
        violations: 剩余违规
        daily_constraints: 每日约束
        resolution_log: 解决日志
        api_key: Anthropic API Key

    Returns:
        (修改后的 daily_sequences, thinking_tokens_used)
    """
    from app.domains.planning_v2.step09_sequence_planner import (
        _build_system_prompt as _build_sequence_prompt,
    )

    client = anthropic.AsyncAnthropic(api_key=api_key)
    total_thinking_tokens = 0

    # 找到仍有 FAIL 违规的天
    fail_days = set()
    for v in violations:
        if v.get("severity") == "fail":
            fail_days.add(v.get("day"))

    if not fail_days:
        logger.info("11.4: 无需 AI 回退，所有 FAIL 已解决")
        return daily_sequences, 0

    for day_seq in daily_sequences:
        day = day_seq.get("day")
        if day not in fail_days:
            continue

        date_str = day_seq.get("date", "")
        dc = _get_constraints_for_date(date_str, daily_constraints)
        if dc is None:
            dc = DailyConstraints(date=date_str, day_of_week="", sunrise="06:00", sunset="18:00")

        user_prompt = _build_ai_retry_prompt(day_seq, dc, violations)

        logger.info(
            "11.4: Calling Opus to re-sequence day %d (%s), thinking_budget=%d",
            day,
            date_str,
            AI_THINKING_BUDGET,
        )

        try:
            response = await client.messages.create(
                model=AI_MODEL,
                max_tokens=AI_MAX_OUTPUT_TOKENS,
                thinking={
                    "type": "enabled",
                    "budget_tokens": AI_THINKING_BUDGET,
                },
                system=_build_sequence_prompt(circle),
                messages=[{"role": "user", "content": user_prompt}],
            )

            text_content = ""
            for block in response.content:
                if block.type == "text":
                    text_content += block.text

            # Extended thinking tokens 计入 output_tokens
            output_tokens = 0
            if hasattr(response, "usage") and response.usage:
                output_tokens = getattr(response.usage, "output_tokens", 0)
            total_thinking_tokens += output_tokens

            if not text_content:
                logger.error("11.4: Day %d — AI 返回空内容", day)
                continue

            new_seq = _extract_json(text_content)
            new_seq["day"] = day
            new_seq["date"] = date_str

            if "activities" in new_seq:
                day_seq["activities"] = new_seq["activities"]
                resolution_log.append(
                    {
                        "step": "11.4",
                        "action": f"AI 重排第 {day} 天，生成 {len(new_seq['activities'])} 个活动",
                        "day": day,
                        "reason": "11.1-11.3 无法解决所有冲突",
                    }
                )
                logger.info(
                    "11.4: Day %d — AI 重排完成，%d activities",
                    day,
                    len(new_seq["activities"]),
                )
            else:
                logger.warning("11.4: Day %d — AI 输出缺少 activities 字段", day)

        except anthropic.APIError as e:
            logger.error("11.4: Day %d — Anthropic API 错误: %s", day, e)
            resolution_log.append(
                {
                    "step": "11.4",
                    "action": f"AI 重排第 {day} 天失败",
                    "day": day,
                    "reason": f"API 错误: {e}",
                }
            )
        except (ValueError, json.JSONDecodeError) as e:
            logger.error("11.4: Day %d — JSON 解析失败: %s", day, e)
            resolution_log.append(
                {
                    "step": "11.4",
                    "action": f"AI 重排第 {day} 天 JSON 解析失败",
                    "day": day,
                    "reason": str(e),
                }
            )

    return daily_sequences, total_thinking_tokens


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def resolve_conflicts(
    daily_sequences: list[dict],
    feasibility_result: FeasibilityResult,
    daily_constraints: list[DailyConstraints],
    poi_pool: list[CandidatePool],
    circle: CircleProfile,
    api_key: str | None = None,
) -> dict:
    """
    冲突处理主入口：按 11.1→11.2→11.3→11.4 顺序尝试解决。

    Args:
        daily_sequences: Step 9 输出的每日活动序列
        feasibility_result: Step 10 输出的可行性检查结果
        daily_constraints: 每日约束
        poi_pool: 候选池（用于查 grade/intensity）
        api_key: Anthropic API Key（仅 11.4 需要），不传则从 settings 获取

    Returns:
        {
            "resolved_sequences": [...],
            "resolution_log": [
                {"step": "11.1", "action": "...", "day": 2, "reason": "..."},
                ...
            ],
            "final_status": "resolved" | "partially_resolved" | "unresolved",
            "ai_fallback_used": false,
            "thinking_tokens_used": 0,
        }
    """
    if feasibility_result.status == "pass":
        logger.info("Feasibility status=pass, no conflicts to resolve")
        return {
            "resolved_sequences": daily_sequences,
            "resolution_log": [],
            "final_status": "resolved",
            "ai_fallback_used": False,
            "thinking_tokens_used": 0,
        }

    # Deep copy 以避免修改原始数据
    sequences = copy.deepcopy(daily_sequences)
    violations = copy.deepcopy(feasibility_result.violations)
    resolution_log: list[dict] = []
    ai_fallback_used = False
    thinking_tokens_used = 0

    logger.info(
        "Starting conflict resolution: %d violations (%d fail, %d warning)",
        len(violations),
        sum(1 for v in violations if v.get("severity") == "fail"),
        sum(1 for v in violations if v.get("severity") == "warning"),
    )

    # ── Step 11.1: 删除模块 ─────────────────────────────────────
    logger.info("=== Step 11.1: 删除模块 ===")
    sequences = _step_11_1_delete(sequences, violations, poi_pool, resolution_log)

    # 重新检查可行性
    recheck = check_feasibility(sequences, daily_constraints)
    if recheck.status == "pass":
        logger.info("11.1 解决了所有冲突")
        return {
            "resolved_sequences": sequences,
            "resolution_log": resolution_log,
            "final_status": "resolved",
            "ai_fallback_used": False,
            "thinking_tokens_used": 0,
        }
    violations = recheck.violations
    logger.info(
        "After 11.1: %d violations remain (%d fail)",
        len(violations),
        sum(1 for v in violations if v.get("severity") == "fail"),
    )

    # ── Step 11.2: 压缩时间 ─────────────────────────────────────
    logger.info("=== Step 11.2: 压缩时间 ===")
    sequences = _step_11_2_compress(sequences, violations, resolution_log)

    recheck = check_feasibility(sequences, daily_constraints)
    if recheck.status == "pass":
        logger.info("11.2 解决了所有冲突")
        return {
            "resolved_sequences": sequences,
            "resolution_log": resolution_log,
            "final_status": "resolved",
            "ai_fallback_used": False,
            "thinking_tokens_used": 0,
        }
    violations = recheck.violations
    logger.info(
        "After 11.2: %d violations remain (%d fail)",
        len(violations),
        sum(1 for v in violations if v.get("severity") == "fail"),
    )

    # ── Step 11.3: 降级强度（仅 capacity_overload）──────────────
    logger.info("=== Step 11.3: 降级强度（仅 capacity_overload）===")
    sequences = _step_11_3_downgrade(sequences, violations, poi_pool, resolution_log)

    recheck = check_feasibility(sequences, daily_constraints)
    if recheck.status == "pass":
        logger.info("11.3 解决了所有冲突")
        return {
            "resolved_sequences": sequences,
            "resolution_log": resolution_log,
            "final_status": "resolved",
            "ai_fallback_used": False,
            "thinking_tokens_used": 0,
        }
    violations = recheck.violations
    has_fail = any(v.get("severity") == "fail" for v in violations)
    logger.info(
        "After 11.3: %d violations remain (%d fail)",
        len(violations),
        sum(1 for v in violations if v.get("severity") == "fail"),
    )

    # ── Step 11.4: AI 回退 ──────────────────────────────────────
    if has_fail:
        logger.info("=== Step 11.4: AI 回退 ===")
        resolved_key = api_key or settings.anthropic_api_key
        if not resolved_key:
            logger.error("11.4: 需要 AI 回退但未提供 Anthropic API Key，跳过")
        else:
            ai_fallback_used = True
            sequences, thinking_tokens_used = await _step_11_4_ai_fallback(
                daily_sequences=sequences,
                violations=violations,
                daily_constraints=daily_constraints,
                resolution_log=resolution_log,
                api_key=resolved_key,
                circle=circle,
            )

            # 最终检查
            recheck = check_feasibility(sequences, daily_constraints)
            violations = recheck.violations
            logger.info(
                "After 11.4: %d violations remain (%d fail)",
                len(violations),
                sum(1 for v in violations if v.get("severity") == "fail"),
            )
    else:
        logger.info("11.3 后无 FAIL 违规，跳过 11.4 AI 回退（仅剩 WARNING）")

    # ── 判断最终状态 ────────────────────────────────────────────
    final_recheck = check_feasibility(sequences, daily_constraints)
    if final_recheck.status == "pass":
        final_status = "resolved"
    elif any(v.get("severity") == "fail" for v in final_recheck.violations):
        final_status = "unresolved"
    else:
        final_status = "partially_resolved"

    logger.info(
        "Conflict resolution complete: final_status=%s, %d log entries, "
        "ai_fallback=%s, thinking_tokens=%d",
        final_status,
        len(resolution_log),
        ai_fallback_used,
        thinking_tokens_used,
    )

    return {
        "resolved_sequences": sequences,
        "resolution_log": resolution_log,
        "final_status": final_status,
        "ai_fallback_used": ai_fallback_used,
        "thinking_tokens_used": thinking_tokens_used,
    }

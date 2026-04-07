"""
step05_5_validator.py -- 活动可用性初筛（Sonnet）

检查 Step 5 选出的活动是否在旅行日期内存在冲突：
  1. 定休日（closed_entities）
  2. 营业时间窗不匹配（open_hours vs 预计到达时间）
  3. 最后入场时间（last_admission）
  4. 预约制/场次制（reservation_required, time_slot）
  5. 季节性闭馆（special_closure）

冲突时调用 Sonnet 推荐替代方案（从 POI 候选池中选）。

API: claude-sonnet-4-6 / 阿里云 qwen-max (轻量级)
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import anthropic

from app.core.config import settings
from app.domains.planning_v2.models import CandidatePool, CircleProfile, DailyConstraints

logger = logging.getLogger(__name__)

# -- 常量 --------------------------------------------------------------------

MODEL_ID = "claude-sonnet-4-6"
MAX_TOKENS = 2000

# Grade 排序权重（用于 fallback 排序）
_GRADE_ORDER: dict[str, int] = {"S": 0, "A": 1, "B": 2, "C": 3}


# -- 公共接口 -----------------------------------------------------------------


async def validate_and_substitute(
    daily_activities: dict,
    daily_constraints: list[DailyConstraints],
    poi_pool: list[CandidatePool],
    circle: CircleProfile,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    检查每天的活动是否有定休日冲突，冲突时从候选池找替代。

    逻辑：
    1. 遍历 daily_activities 的每天每个活动
    2. 检查 entity_id 是否在该天的 closed_entities 中
    3. 如果冲突：
       a. 从 poi_pool 中找同走廊+同类型的替代候选��最多5个）
       b. 调用 Sonnet 从候选中选出最佳替代
       c. 替换原活动
    4. 如果无冲突：保持不变

    Args:
        daily_activities: Step 5 输出，含 "daily_activities" 列表。
        daily_constraints: Step 8 输出的每日约束列表。
        poi_pool: Step 4 输出的 CandidatePool 列表。
        api_key: 可选，覆盖默认 ANTHROPIC_API_KEY。

    Returns:
        {
          "validated_activities": {...},
          "substitutions": [
            {"day": 2, "original": "xxx", "replacement": "yyy", "reason": "周二定休"},
          ],
          "no_substitute_found": [],
        }
    """
    # 构建索引
    pool_map: dict[str, CandidatePool] = {p.entity_id: p for p in poi_pool}
    constraints_by_date: dict[str, DailyConstraints] = {dc.date: dc for dc in daily_constraints}

    # 已被分配的 entity_id（用于排除重复）
    all_assigned_ids = _collect_all_assigned_ids(daily_activities)

    substitutions: list[dict] = []
    no_substitute_found: list[dict] = []
    conflicts_for_sonnet: list[dict] = []  # 需要 AI 帮忙选替代的冲突

    days = daily_activities.get("daily_activities", [])

    for day_data in days:
        day_num = day_data.get("day", 0)
        date_str = day_data.get("date", "")
        dc = constraints_by_date.get(date_str)
        if dc is None:
            continue

        closed_set = set(dc.closed_entities) if dc.closed_entities else set()

        corridor = day_data.get("main_corridor", "")
        secondary_corridors = day_data.get("secondary_corridors", [])

        for act_list_key in ("main_activities", "time_anchors"):
            activities = day_data.get(act_list_key, [])
            for idx, act in enumerate(activities):
                eid = act.get("entity_id", "")
                if not eid:
                    continue

                original_poi = pool_map.get(eid)
                original_name = act.get("name", eid)

                # --- 冲突检测（5种类型） ---
                conflict_reason = _detect_conflict(
                    eid=eid,
                    act=act,
                    poi=original_poi,
                    closed_set=closed_set,
                    dc=dc,
                )

                if conflict_reason is None:
                    continue

                # 找到冲突，准备候选列表
                original_type = original_poi.entity_type if original_poi else "poi"
                original_tags = set(original_poi.tags) if original_poi else set()

                candidates = _find_replacement_candidates(
                    poi_pool=poi_pool,
                    corridor=corridor,
                    secondary_corridors=secondary_corridors,
                    entity_type=original_type,
                    original_tags=original_tags,
                    exclude_ids=all_assigned_ids | closed_set,
                    max_count=5,
                )

                if not candidates:
                    logger.warning(
                        "[Step05.5] Day %d: %s 冲突(%s)，无可用替代候选",
                        day_num,
                        original_name,
                        conflict_reason,
                    )
                    no_substitute_found.append(
                        {
                            "day": day_num,
                            "entity_id": eid,
                            "name": original_name,
                            "reason": conflict_reason,
                        }
                    )
                    continue

                conflicts_for_sonnet.append(
                    {
                        "day_num": day_num,
                        "date_str": date_str,
                        "act_list_key": act_list_key,
                        "act_index": idx,
                        "original_id": eid,
                        "original_name": original_name,
                        "original_type": original_type,
                        "day_of_week": dc.day_of_week,
                        "conflict_reason": conflict_reason,
                        "candidates": candidates,
                    }
                )

    # 无冲突，直接返回
    if not conflicts_for_sonnet and not no_substitute_found:
        logger.info("[Step05.5] 无可用性冲突，跳过校验")
        return {
            "validated_activities": daily_activities,
            "substitutions": [],
            "no_substitute_found": [],
        }

    # 有冲突 -> 调用 Sonnet 批量选替代
    if conflicts_for_sonnet:
        try:
            ai_selections = await _call_sonnet_for_substitutes(
                conflicts=conflicts_for_sonnet,
                circle=circle,
                api_key=api_key,
            )
        except Exception as exc:
            logger.error(
                "[Step05.5] Sonnet 调用失败，降级到规则选择: %s",
                exc,
            )
            ai_selections = _rule_based_substitute(conflicts_for_sonnet)

        # 应用替换
        for conflict, selection in zip(conflicts_for_sonnet, ai_selections):
            replacement_id = selection.get("entity_id")
            replacement_poi = pool_map.get(replacement_id)

            if not replacement_id or not replacement_poi:
                no_substitute_found.append(
                    {
                        "day": conflict["day_num"],
                        "entity_id": conflict["original_id"],
                        "name": conflict["original_name"],
                        "reason": f"{conflict['day_of_week']}定休，AI未找到合适替代",
                    }
                )
                continue

            # 执行替换
            day_idx = _find_day_index(days, conflict["day_num"])
            if day_idx is None:
                continue

            act_list = days[day_idx].get(conflict["act_list_key"], [])
            act_idx = conflict["act_index"]
            if act_idx < len(act_list):
                act_list[act_idx] = {
                    "entity_id": replacement_poi.entity_id,
                    "name": replacement_poi.name_zh,
                    "visit_minutes": replacement_poi.visit_minutes,
                    "why": selection.get("reason", "替代定休日冲突活动"),
                }

                # 更新已分配集合
                all_assigned_ids.discard(conflict["original_id"])
                all_assigned_ids.add(replacement_poi.entity_id)

                substitutions.append(
                    {
                        "day": conflict["day_num"],
                        "original": conflict["original_name"],
                        "original_id": conflict["original_id"],
                        "replacement": replacement_poi.name_zh,
                        "replacement_id": replacement_poi.entity_id,
                        "reason": conflict.get("conflict_reason", f"{conflict['day_of_week']}定休"),
                    }
                )

                logger.info(
                    "[Step05.5] Day %d: %s -> %s (%s)",
                    conflict["day_num"],
                    conflict["original_name"],
                    replacement_poi.name_zh,
                    conflict.get("conflict_reason", "冲突"),
                )

    logger.info(
        "[Step05.5] 校验完成: %d 替换, %d 无替代",
        len(substitutions),
        len(no_substitute_found),
    )

    return {
        "validated_activities": daily_activities,
        "substitutions": substitutions,
        "no_substitute_found": no_substitute_found,
    }


# -- 冲突检测 -----------------------------------------------------------------


def _detect_conflict(
    eid: str,
    act: dict,
    poi: CandidatePool | None,
    closed_set: set[str],
    dc: DailyConstraints,
) -> str | None:
    """
    检测活动是否与当天约束冲突。返回冲突原因字符串，无冲突返回 None。

    检测项：
      1. 定休日（closed_entities）
      2. 营业时间窗不匹配
      3. 最后入场时间
      4. 预约制/场次制
      5. 季节性闭馆
    """
    # 1. 定休日
    if eid in closed_set:
        return f"{dc.day_of_week}定休"

    if poi is None:
        return None

    open_hours = poi.open_hours or {}

    # 2. 营业时间窗检查
    open_time = open_hours.get("open_time")  # "HH:MM"
    close_time = open_hours.get("close_time")  # "HH:MM"
    estimated_arrival = act.get("start_time")  # "HH:MM" (Step 5 预估)

    if open_time and close_time and estimated_arrival:
        try:
            arr = datetime.strptime(estimated_arrival, "%H:%M")
            close = datetime.strptime(close_time, "%H:%M")
            visit_mins = poi.visit_minutes or 60
            departure = arr + timedelta(minutes=visit_mins)
            if departure > close:
                return (
                    f"营业时间不足: 预计{estimated_arrival}到达，"
                    f"需停留{visit_mins}分钟，但{close_time}闭馆"
                )
        except ValueError:
            pass  # 时间格式异常，跳过

    # 3. 最后入场时间
    last_admission = open_hours.get("last_admission")  # "HH:MM"
    if last_admission and estimated_arrival:
        try:
            arr = datetime.strptime(estimated_arrival, "%H:%M")
            last = datetime.strptime(last_admission, "%H:%M")
            if arr > last:
                return f"超过最后入场时间: 预计{estimated_arrival}到达，最后入场{last_admission}"
        except ValueError:
            pass

    # 4. 预约制检查
    reservation_required = open_hours.get("reservation_required", False)
    time_slot = open_hours.get("time_slot")  # 场次时间，如 "10:00,14:00"
    if reservation_required:
        tags = set(poi.tags) if poi.tags else set()
        if "hard_to_book" in tags or "要予約" in tags:
            return "预约制且预约困难，需提前确认可用性"

    if time_slot and estimated_arrival:
        slots = [s.strip() for s in str(time_slot).split(",")]
        try:
            arr = datetime.strptime(estimated_arrival, "%H:%M")
            matched = False
            for slot in slots:
                slot_time = datetime.strptime(slot, "%H:%M")
                diff = abs((arr - slot_time).total_seconds()) / 60
                if diff <= 15:
                    matched = True
                    break
            if not matched:
                return f"场次制: 可选场次{time_slot}，预计到达{estimated_arrival}不匹配任何场次"
        except ValueError:
            pass

    # 5. 季节性闭馆 / 特殊关闭
    special_closure = open_hours.get("special_closure")  # list of date ranges or notes
    if special_closure and isinstance(special_closure, list):
        for closure in special_closure:
            if isinstance(closure, str) and dc.date in closure:
                return f"季节性闭馆: {closure}"
            if isinstance(closure, dict):
                start = closure.get("start", "")
                end = closure.get("end", "")
                if start <= dc.date <= end:
                    return f"季节性闭馆: {start}~{end} {closure.get('reason', '')}"

    return None


# -- 候选查找 -----------------------------------------------------------------


def _find_replacement_candidates(
    poi_pool: list[CandidatePool],
    corridor: str,
    secondary_corridors: list[str],
    entity_type: str,
    original_tags: set[str],
    exclude_ids: set[str],
    max_count: int = 5,
) -> list[CandidatePool]:
    """
    从 POI 候选池中找同走廊+同类型的替代候选。

    优先级：
    1. 同 main_corridor + 同 entity_type
    2. 同 secondary_corridor + 同 entity_type
    3. 同走廊不限类型但 tag 有交集
    4. 按 grade 排序取 top N
    """
    all_corridors = set()
    if corridor:
        all_corridors.add(corridor.lower())
    for sc in secondary_corridors:
        if sc:
            all_corridors.add(sc.lower())

    scored: list[tuple[int, CandidatePool]] = []

    for poi in poi_pool:
        if poi.entity_id in exclude_ids:
            continue

        poi_tags_lower = {t.lower() for t in poi.tags} if poi.tags else set()

        # 走廊匹配检测
        in_main_corridor = corridor and corridor.lower() in poi_tags_lower
        in_any_corridor = bool(all_corridors & poi_tags_lower)
        same_type = poi.entity_type == entity_type
        tag_overlap = len(original_tags & poi_tags_lower) if original_tags else 0

        # 计算优先分数（越小越优先）
        score = _GRADE_ORDER.get(poi.grade, 99) * 10  # grade 基础分

        if in_main_corridor and same_type:
            score -= 50  # 最优：同主走廊+同类型
        elif in_any_corridor and same_type:
            score -= 30  # 次优：同走廊组+同类型
        elif in_main_corridor:
            score -= 20  # 同主走廊不同类型
        elif in_any_corridor:
            score -= 10  # 同走廊组不同类型
        else:
            score += 50  # 不在走廊内，低优先

        score -= tag_overlap * 3  # tag 交集越多越好

        scored.append((score, poi))

    # 按分数排序取 top N
    scored.sort(key=lambda x: x[0])
    return [poi for _, poi in scored[:max_count]]


# -- Sonnet 调用 --------------------------------------------------------------


async def _call_sonnet_for_substitutes(
    conflicts: list[dict],
    circle: CircleProfile,
    api_key: str | None = None,
) -> list[dict]:
    """
    批量调用 Sonnet，为每个冲突选出最佳替代。

    Args:
        conflicts: 冲突列表，每项包含 original_name, candidates 等。
        api_key: Anthropic API key。

    Returns:
        与 conflicts 同长度的列表，每项 {"entity_id": ..., "reason": ...}。
    """
    client = anthropic.AsyncAnthropic(
        api_key=api_key or settings.anthropic_api_key,
    )

    prompt_parts: list[str] = []
    prompt_parts.append(
        "以下活动因可用性冲突（定休日/营业时间/最后入场/预约制等）需要替换。"
        "请为每个冲突从候选中选出最佳替代，输出 JSON 数组。\n"
    )

    for i, conflict in enumerate(conflicts):
        prompt_parts.append(
            f"### 冲突 {i + 1}: Day {conflict['day_num']} ({conflict['day_of_week']})"
        )
        prompt_parts.append(
            f"原活动: {conflict['original_name']} (类型: {conflict['original_type']})"
        )
        prompt_parts.append(f"冲突原因: {conflict.get('conflict_reason', '定休日')}")
        prompt_parts.append("候选替代:")
        for cand in conflict["candidates"]:
            tags_short = cand.tags[:5] if cand.tags else []
            prompt_parts.append(
                f"  - {cand.entity_id} | {cand.name_zh} | grade={cand.grade} | "
                f"tags={tags_short} | {cand.visit_minutes}min | {cand.cost_local}{cand.currency}"
            )
        prompt_parts.append("")

    prompt_parts.append(
        "输出格式（纯 JSON，不要其他文字）:\n"
        "[\n"
        '  {"conflict_index": 0, "entity_id": "选中的实体ID", '
        '"reason": "选择理由（一句话）"},\n'
        "  ...\n"
        "]"
    )

    user_prompt = "\n".join(prompt_parts)

    logger.info(
        "[Step05.5] 调用 Sonnet 处理 %d 个定休日冲突",
        len(conflicts),
    )

    response = await client.messages.create(
        model=MODEL_ID,
        max_tokens=MAX_TOKENS,
        system=(
            f"你是{circle.region_desc}旅行规划助手。任务：为定休日冲突的活动选择最佳替代。"
            "优先选同区域、同类型、高评级的替代。输出纯 JSON。"
        ),
        messages=[{"role": "user", "content": user_prompt}],
    )

    # 提取文本
    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content += block.text

    # 解析 JSON 数组
    selections = _parse_json_array(text_content)
    if selections is None or len(selections) != len(conflicts):
        logger.warning(
            "[Step05.5] Sonnet 返回解析异常 (got %s items, expected %d), 降级规则选择",
            len(selections) if selections else "None",
            len(conflicts),
        )
        return _rule_based_substitute(conflicts)

    # 将 JSON 数组映射回结果
    result = []
    selection_map = {s.get("conflict_index", i): s for i, s in enumerate(selections)}
    for i in range(len(conflicts)):
        sel = selection_map.get(i, {})
        result.append(
            {
                "entity_id": sel.get("entity_id", ""),
                "reason": sel.get("reason", ""),
            }
        )

    return result


# -- JSON 解析 ----------------------------------------------------------------


def _parse_json_array(raw_text: str) -> list | None:
    """从 Sonnet 返回中解析 JSON 数组。"""
    if not raw_text or not raw_text.strip():
        return None

    text = raw_text.strip()

    # 直接解析
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    # markdown 代码块
    md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if md_match:
        try:
            parsed = json.loads(md_match.group(1))
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    # 找第一个 [ 和最后一个 ]
    first_bracket = text.find("[")
    last_bracket = text.rfind("]")
    if first_bracket != -1 and last_bracket > first_bracket:
        try:
            parsed = json.loads(text[first_bracket : last_bracket + 1])
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    logger.error("[Step05.5] 无法解析 Sonnet 返回: %s...", text[:200])
    return None


# -- 规则引擎 fallback --------------------------------------------------------


def _rule_based_substitute(conflicts: list[dict]) -> list[dict]:
    """
    当 Sonnet 调用失败时的规则引擎降级。

    策略：从每个冲突的候选列表中选 grade 最高的第一个。
    """
    logger.info("[Step05.5] 使用规则引擎 fallback 选择替代")
    result = []
    for conflict in conflicts:
        candidates = conflict.get("candidates", [])
        if not candidates:
            result.append({"entity_id": "", "reason": "无可用候选"})
            continue

        # 候选已按 score 排好序（_find_replacement_candidates 的输出）
        best = candidates[0]
        result.append(
            {
                "entity_id": best.entity_id,
                "reason": f"规则选择: grade={best.grade}, {best.name_zh}",
            }
        )
    return result


# -- 辅助函数 -----------------------------------------------------------------


def _collect_all_assigned_ids(daily_activities: dict) -> set[str]:
    """从 daily_activities 中收集所有已分配的 entity_id。"""
    assigned: set[str] = set()
    for day in daily_activities.get("daily_activities", []):
        for act in day.get("main_activities", []):
            eid = act.get("entity_id")
            if eid:
                assigned.add(eid)
        for anchor in day.get("time_anchors", []):
            eid = anchor.get("entity_id")
            if eid:
                assigned.add(eid)
    return assigned


def _find_day_index(days: list[dict], day_num: int) -> int | None:
    """在 days 列表中找到 day == day_num 的索引。"""
    for i, d in enumerate(days):
        if d.get("day") == day_num:
            return i
    return None

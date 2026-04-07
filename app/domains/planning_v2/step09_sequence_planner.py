"""
step09_sequence_planner.py — 每日活动最优排序（含时间窗约束）

调用 Opus 模型，为每天的活动排出分钟级的最优顺序。

输入：
  - Step 5 的 daily_activities（每天的主活动+走廊）
  - Step 8 的 DailyConstraints（日出日落、定休日、酒店餐、锚点）
  - 通勤距离矩阵（Step 7.5 的结果或 route_matrix 的数据）

输出：
  {
    "daily_sequences": [
      {
        "day": 1,
        "date": "2026-04-01",
        "activities": [
          {
            "entity_id": "xxx",
            "name": "伏见稲荷大社",
            "start_time": "07:00",
            "end_time": "09:00",
            "type": "poi",
            "commute_from_prev_mins": 0,
            "notes": "清晨人少，最佳拍照时间"
          },
          ...
        ]
      }
    ],
    "thinking_tokens_used": N,
  }
"""

import json
import logging
import re

import anthropic

from app.core.config import settings
from app.domains.planning_v2.models import CircleProfile, DailyConstraints

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_NAME = "claude-opus-4-0-20250514"
THINKING_BUDGET_TOKENS = 15000
MAX_OUTPUT_TOKENS = 16000


def _build_system_prompt(circle: CircleProfile) -> str:
    region = circle.region_desc
    return f"""\
你是一位精通{region}的行程编排专家。你的任务是为每天的活动排出分钟级的最优顺序。

编排原则：
1. 时间窗约束：尊重景点营业时间、日出日落、交通班次
2. 通勤效率：相邻活动之间通勤时间要合理（理想 <30 分钟）
3. 体力曲线：上午安排高强度，下午渐缓，傍晚轻松
4. 锚点优先：有固定时间的活动（飞行、预约）不可移动
5. 弹性午餐：在 11:30-13:30 之间插入一个 flex_meal 时段
6. 酒店含餐时：酒店含早餐 → 早上 08:00 前在酒店；含晚餐 → 晚上 18:30 前回酒店
7. 第一个活动从 sunrise 后开始，最后一个活动在 sunset+60min 前结束

每个活动必须标注 start_time 和 end_time（HH:MM格式），以及到前一个活动的通勤时间。
输出 JSON 格式，不要任何额外文字。"""


# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------


def _build_user_prompt(
    day_index: int,
    date_str: str,
    activities: list[dict],
    constraints: DailyConstraints,
    commute_matrix: dict[str, dict[str, int]],
) -> str:
    """
    构建单天的 user prompt。

    Args:
        day_index: 天序号（从1开始）
        date_str: 日期字符串 YYYY-MM-DD
        activities: 当天候选活动列表
        constraints: 当天的 DailyConstraints
        commute_matrix: 通勤矩阵 {entity_id: {entity_id: minutes}}

    Returns:
        格式化的 user prompt 字符串
    """
    parts = []

    # 基础信息
    parts.append(f"## 第 {day_index} 天 ({date_str}, {constraints.day_of_week})")
    parts.append("")

    # 日出日落
    parts.append(f"日出: {constraints.sunrise}")
    parts.append(f"日落: {constraints.sunset}")
    parts.append("")

    # 酒店餐食
    if constraints.hotel_breakfast_included:
        parts.append("酒店含早餐: 是 → 08:00 前在酒店用餐")
    if constraints.hotel_dinner_included:
        parts.append("酒店含晚餐: 是 → 18:30 前回酒店")
    parts.append("")

    # 锚点
    if constraints.anchors:
        parts.append("### 锚点（不可移动）")
        for anchor in constraints.anchors:
            parts.append(
                f"- {anchor.get('name', '未知')} @ {anchor.get('time', '?')} "
                f"({anchor.get('type', 'unknown')}, {anchor.get('constraint', '')})"
            )
        parts.append("")

    # 关闭实体
    if constraints.closed_entities:
        parts.append(f"### 当日定休: {', '.join(constraints.closed_entities)}")
        parts.append("（以上实体不可安排在今天）")
        parts.append("")

    # 低频班次
    if constraints.low_freq_transits:
        parts.append("### 低频班次限制")
        for transit in constraints.low_freq_transits:
            parts.append(
                f"- {transit.get('route', '?')}: "
                f"{transit.get('start_time', '?')}-{transit.get('end_time', '?')} "
                f"(每{transit.get('frequency_mins', '?')}分钟)"
            )
        parts.append("")

    # 候选活动
    parts.append("### 候选活动")
    for act in activities:
        entity_id = act.get("entity_id", "unknown")
        name = act.get("name", act.get("name_zh", "未知"))
        act_type = act.get("type", act.get("entity_type", "poi"))
        visit_mins = act.get("visit_minutes", 60)
        grade = act.get("grade", "B")
        tags = act.get("tags", [])
        open_hours = act.get("open_hours", {})

        line = f"- [{entity_id}] {name} (type={act_type}, grade={grade}, visit_mins={visit_mins}"
        if tags:
            line += f", tags={','.join(tags)}"
        if open_hours:
            open_str = open_hours.get("open_hours", "")
            if open_str:
                line += f", 营业={open_str}"
        line += ")"
        parts.append(line)
    parts.append("")

    # 通勤矩阵
    # 只提供当天候选活动之间的通勤时间
    entity_ids = [act.get("entity_id") for act in activities if act.get("entity_id")]
    if commute_matrix and entity_ids:
        parts.append("### 通勤时间矩阵（分钟）")
        for from_id in entity_ids:
            if from_id not in commute_matrix:
                continue
            for to_id in entity_ids:
                if from_id == to_id:
                    continue
                mins = commute_matrix.get(from_id, {}).get(to_id)
                if mins is not None:
                    from_name = _find_name(activities, from_id)
                    to_name = _find_name(activities, to_id)
                    parts.append(f"- {from_name} → {to_name}: {mins} 分钟")
        parts.append("")

    # 输出格式要求
    parts.append("### 输出格式")
    parts.append("输出严格 JSON，格式如下（不要任何额外文字、不要 markdown 代码块标记）：")
    parts.append(
        json.dumps(
            {
                "day": day_index,
                "date": date_str,
                "activities": [
                    {
                        "entity_id": "实体ID或null",
                        "name": "活动名称",
                        "start_time": "HH:MM",
                        "end_time": "HH:MM",
                        "type": "poi/restaurant/flex_meal/transit/...",
                        "commute_from_prev_mins": 0,
                        "notes": "安排理由或小贴士",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    return "\n".join(parts)


def _find_name(activities: list[dict], entity_id: str) -> str:
    """在活动列表中查找实体的名称。"""
    for act in activities:
        if act.get("entity_id") == entity_id:
            return act.get("name", act.get("name_zh", entity_id))
    return entity_id


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict:
    """
    从 AI 输出中提取 JSON。

    处理以下情况：
      - 纯 JSON 文本
      - 被 markdown 代码块包裹的 JSON
      - 前后有额外文字的 JSON

    Args:
        text: AI 输出文本

    Returns:
        解析后的 dict

    Raises:
        ValueError: JSON 解析失败
    """
    text = text.strip()

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 markdown 代码块中的 JSON
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试找到第一个 { 和最后一个 } 之间的内容
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从 AI 输出中提取有效 JSON，原文前 500 字符：{text[:500]}")


# ---------------------------------------------------------------------------
# Single-day AI call
# ---------------------------------------------------------------------------


async def _plan_single_day(
    client: anthropic.AsyncAnthropic,
    day_index: int,
    date_str: str,
    activities: list[dict],
    constraints: DailyConstraints,
    commute_matrix: dict[str, dict[str, int]],
    circle: CircleProfile,
) -> tuple[dict, int]:
    """
    为单天调用 Opus 排序活动。

    Args:
        client: Anthropic 异步客户端
        day_index: 天序号
        date_str: 日期
        activities: 当天候选活动
        constraints: 当天约束
        commute_matrix: 通勤矩阵

    Returns:
        (day_sequence_dict, thinking_tokens_used)

    Raises:
        ValueError: AI 输出解析失败
        anthropic.APIError: API 调用失败
    """
    user_prompt = _build_user_prompt(
        day_index=day_index,
        date_str=date_str,
        activities=activities,
        constraints=constraints,
        commute_matrix=commute_matrix,
    )

    logger.info(
        "Calling Opus for day %d (%s) with %d activities, thinking_budget=%d",
        day_index,
        date_str,
        len(activities),
        THINKING_BUDGET_TOKENS,
    )

    response = await client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_OUTPUT_TOKENS,
        thinking={
            "type": "enabled",
            "budget_tokens": THINKING_BUDGET_TOKENS,
        },
        system=_build_system_prompt(circle),
        messages=[
            {"role": "user", "content": user_prompt},
        ],
    )

    # 提取文本内容和 thinking tokens
    text_content = ""
    thinking_tokens = 0

    for block in response.content:
        if block.type == "text":
            text_content += block.text
        elif block.type == "thinking":
            # thinking block 不包含在 output tokens 中，
            # 从 usage 获取实际 thinking tokens
            pass

    # Extended thinking tokens 计入 output_tokens（Anthropic 官方计费方式）。
    # SDK 无独立 thinking_tokens 字段，output_tokens 包含 thinking + visible output。
    if hasattr(response, "usage") and response.usage:
        thinking_tokens = getattr(response.usage, "output_tokens", 0)
        logger.info(
            "Day %d Opus usage: input=%d, output=%d (includes thinking)",
            day_index,
            getattr(response.usage, "input_tokens", 0),
            thinking_tokens,
        )

    if not text_content:
        raise ValueError(f"Day {day_index}: AI 返回空内容")

    logger.debug("Day %d raw response length: %d chars", day_index, len(text_content))

    # 解析 JSON
    day_sequence = _extract_json(text_content)

    # 校验基本结构
    if "activities" not in day_sequence:
        raise ValueError(
            f"Day {day_index}: AI 输出缺少 activities 字段，keys={list(day_sequence.keys())}"
        )

    # 确保 day 和 date 字段正确
    day_sequence["day"] = day_index
    day_sequence["date"] = date_str

    act_count = len(day_sequence["activities"])
    logger.info(
        "Day %d (%s): planned %d activities, thinking_tokens=%d",
        day_index,
        date_str,
        act_count,
        thinking_tokens,
    )

    return day_sequence, thinking_tokens


# ---------------------------------------------------------------------------
# Validation & post-processing
# ---------------------------------------------------------------------------


def _validate_day_sequence(day_seq: dict) -> list[str]:
    """
    校验单天排序结果的基本完整性。

    Returns:
        错误列表（空表示通过）
    """
    errors = []
    activities = day_seq.get("activities", [])

    if not activities:
        errors.append(f"Day {day_seq.get('day')}: 活动列表为空")
        return errors

    prev_end = None
    for i, act in enumerate(activities):
        # 必须字段检查
        for required in ("name", "start_time", "end_time", "type"):
            if required not in act:
                errors.append(f"Day {day_seq.get('day')}, activity[{i}]: 缺少必须字段 '{required}'")

        # 时间格式检查
        for time_field in ("start_time", "end_time"):
            val = act.get(time_field, "")
            if val and not re.match(r"^\d{2}:\d{2}$", val):
                errors.append(
                    f"Day {day_seq.get('day')}, activity[{i}]: {time_field}='{val}' 不是 HH:MM 格式"
                )

        # 时间顺序检查
        start = act.get("start_time", "")
        end = act.get("end_time", "")
        if start and end and start >= end:
            errors.append(
                f"Day {day_seq.get('day')}, activity[{i}] ({act.get('name')}): "
                f"start_time ({start}) >= end_time ({end})"
            )

        # 与前一活动的时间顺序
        if prev_end and start and start < prev_end:
            errors.append(
                f"Day {day_seq.get('day')}, activity[{i}] ({act.get('name')}): "
                f"start_time ({start}) 早于前一活动的 end_time ({prev_end})"
            )

        prev_end = end

    return errors


def _ensure_flex_meal(day_seq: dict) -> None:
    """
    如果 AI 没有插入弹性午餐，尝试在 11:30-13:30 之间补一个。

    直接修改 day_seq['activities']。
    """
    activities = day_seq.get("activities", [])

    # 检查是否已有午餐
    for act in activities:
        act_type = (act.get("type") or "").lower()
        if act_type in ("flex_meal", "restaurant", "lunch"):
            start = act.get("start_time", "")
            if "11:" in start or "12:" in start or "13:" in start:
                return  # 已有午餐

    # 寻找 11:30-13:30 之间的空隙
    lunch_slot = {
        "entity_id": None,
        "name": "午餐",
        "start_time": "12:00",
        "end_time": "13:00",
        "type": "flex_meal",
        "commute_from_prev_mins": 10,
        "notes": "弹性午餐时段，附近有多选择",
    }

    # 找到合适的插入位置
    insert_idx = len(activities)
    for i, act in enumerate(activities):
        if act.get("start_time", "") > "13:00":
            insert_idx = i
            break

    # 检查是否有空间（至少 60 分钟间隙在 11:30-13:30 之间）
    if insert_idx > 0 and insert_idx < len(activities):
        prev_end = activities[insert_idx - 1].get("end_time", "00:00")
        next_start = activities[insert_idx].get("start_time", "23:59")

        if prev_end <= "13:00" and next_start >= "12:00":
            # 动态调整午餐时间
            actual_start = max(prev_end, "11:30")
            # 加 10 分钟通勤
            start_h, start_m = map(int, actual_start.split(":"))
            start_total = start_h * 60 + start_m + 10
            lunch_start = f"{start_total // 60:02d}:{start_total % 60:02d}"
            end_total = start_total + 60
            lunch_end = f"{end_total // 60:02d}:{end_total % 60:02d}"

            if lunch_end <= next_start:
                lunch_slot["start_time"] = lunch_start
                lunch_slot["end_time"] = lunch_end
                activities.insert(insert_idx, lunch_slot)
                logger.info(
                    "Day %d: 插入弹性午餐 %s-%s",
                    day_seq.get("day"),
                    lunch_start,
                    lunch_end,
                )
                return

    # 如果放不下就跳过
    logger.warning("Day %d: 无法在 11:30-13:30 之间插入弹性午餐", day_seq.get("day"))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def plan_daily_sequences(
    daily_activities: list[dict],
    daily_constraints: list[DailyConstraints],
    commute_matrix: dict[str, dict[str, int]],
    circle: CircleProfile,
    api_key: str | None = None,
) -> dict:
    """
    为所有天排出最优活动顺序。

    Args:
        daily_activities: 每天的候选活动列表，格式：
            [
                {
                    "day": 1,
                    "date": "2026-04-01",
                    "activities": [CandidatePool-like dicts...]
                },
                ...
            ]
        daily_constraints: 每天的约束列表（与 daily_activities 按日期对应）
        commute_matrix: 通勤矩阵 {from_entity_id: {to_entity_id: minutes}}
        api_key: Anthropic API Key，不传则从 settings 获取

    Returns:
        {
            "daily_sequences": [
                {"day": 1, "date": "...", "activities": [...]},
                ...
            ],
            "thinking_tokens_used": N,
        }

    Raises:
        ValueError: 输入数据不完整或 AI 输出异常
        anthropic.APIError: API 调用失败
    """
    if not daily_activities:
        raise ValueError("daily_activities 为空，无法编排")

    resolved_key = api_key or settings.anthropic_api_key
    if not resolved_key:
        raise ValueError("未提供 Anthropic API Key，请设置 ANTHROPIC_API_KEY 环境变量")

    client = anthropic.AsyncAnthropic(api_key=resolved_key)

    # 构建日期到约束的快速映射
    constraints_map: dict[str, DailyConstraints] = {}
    for dc in daily_constraints:
        constraints_map[dc.date] = dc

    all_sequences = []
    total_thinking_tokens = 0
    validation_warnings = []

    for day_data in daily_activities:
        day_index = day_data.get("day", 0)
        date_str = day_data.get("date", "")
        activities = day_data.get("activities", [])

        if not activities:
            logger.warning("Day %d (%s): 无候选活动，跳过", day_index, date_str)
            all_sequences.append(
                {
                    "day": day_index,
                    "date": date_str,
                    "activities": [],
                }
            )
            continue

        # 获取当天约束
        dc = constraints_map.get(date_str)
        if dc is None:
            logger.warning(
                "Day %d (%s): 无对应 DailyConstraints，使用默认值",
                day_index,
                date_str,
            )
            dc = DailyConstraints(
                date=date_str,
                day_of_week="",
                sunrise="06:00",
                sunset="18:00",
            )

        # 过滤掉当天关闭的实体
        open_activities = [
            act for act in activities if act.get("entity_id") not in set(dc.closed_entities)
        ]
        if len(open_activities) < len(activities):
            removed = len(activities) - len(open_activities)
            logger.info("Day %d: 过滤掉 %d 个定休日实体", day_index, removed)

        try:
            day_seq, thinking_used = await _plan_single_day(
                client=client,
                day_index=day_index,
                date_str=date_str,
                activities=open_activities,
                constraints=dc,
                commute_matrix=commute_matrix,
                circle=circle,
            )
            total_thinking_tokens += thinking_used
        except (ValueError, json.JSONDecodeError) as e:
            logger.error("Day %d (%s): AI 排序失败: %s", day_index, date_str, e)
            # Fallback: 按原始顺序返回，不排序
            day_seq = _fallback_sequence(day_index, date_str, open_activities)
            validation_warnings.append(f"Day {day_index}: AI 排序失败，使用 fallback 顺序: {e}")
        except anthropic.APIError as e:
            logger.error("Day %d (%s): Anthropic API 错误: %s", day_index, date_str, e)
            day_seq = _fallback_sequence(day_index, date_str, open_activities)
            validation_warnings.append(f"Day {day_index}: API 调用失败，使用 fallback 顺序: {e}")

        # 校验
        errors = _validate_day_sequence(day_seq)
        if errors:
            for err in errors:
                logger.warning("Validation: %s", err)
            validation_warnings.extend(errors)

        # 确保有弹性午餐
        _ensure_flex_meal(day_seq)

        all_sequences.append(day_seq)

    result = {
        "daily_sequences": all_sequences,
        "thinking_tokens_used": total_thinking_tokens,
    }

    if validation_warnings:
        result["validation_warnings"] = validation_warnings

    logger.info(
        "Sequence planning complete: %d days, %d total activities, %d thinking tokens",
        len(all_sequences),
        sum(len(s.get("activities", [])) for s in all_sequences),
        total_thinking_tokens,
    )

    return result


# ---------------------------------------------------------------------------
# Fallback: deterministic ordering when AI fails
# ---------------------------------------------------------------------------


def _fallback_sequence(
    day_index: int,
    date_str: str,
    activities: list[dict],
) -> dict:
    """
    当 AI 调用失败时的 fallback：按 grade 排序，给出粗略时间分配。

    不使用 AI，纯确定性逻辑。
    """
    logger.warning("Day %d (%s): using fallback deterministic sequence", day_index, date_str)

    grade_order = {"S": 0, "A": 1, "B": 2, "C": 3}
    sorted_acts = sorted(
        activities,
        key=lambda a: grade_order.get(a.get("grade", "C"), 4),
    )

    current_time_mins = 8 * 60  # 08:00 start
    result_activities = []

    for act in sorted_acts:
        visit_mins = act.get("visit_minutes", 60)
        commute = 20  # 默认通勤 20 分钟

        start_mins = current_time_mins + commute
        end_mins = start_mins + visit_mins

        result_activities.append(
            {
                "entity_id": act.get("entity_id"),
                "name": act.get("name", act.get("name_zh", "未知")),
                "start_time": f"{start_mins // 60:02d}:{start_mins % 60:02d}",
                "end_time": f"{end_mins // 60:02d}:{end_mins % 60:02d}",
                "type": act.get("type", act.get("entity_type", "poi")),
                "commute_from_prev_mins": commute if result_activities else 0,
                "notes": "fallback 排序，未经 AI 优化",
            }
        )

        current_time_mins = end_mins

    return {
        "day": day_index,
        "date": date_str,
        "activities": result_activities,
    }

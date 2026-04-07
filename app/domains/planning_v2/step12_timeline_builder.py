"""
step12_timeline_builder.py — 精确时间线生成（Sonnet）

将 Step 9 的活动顺序 + Step 11 的冲突修复结果，
生成精确到分钟的每日时间线骨架。

每日时间线包含：
  - hotel_breakfast / hotel_dinner slot（酒店含餐时）
  - poi slot（景点/活动）
  - commute slot（通勤段：JR / 巴士 / 步行 / 出租车）
  - flex_meal slot（弹性午餐，标记 optional=true）
  - dinner slot（晚餐推荐时段）

API: claude-sonnet-4-6（普通模式，不用 extended thinking）
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

AI_MODEL = "claude-sonnet-4-6"
AI_MAX_OUTPUT_TOKENS = 16000


def _build_system_prompt(circle: CircleProfile) -> str:
    region = circle.region_desc
    return f"""\
你是一位精通{region}旅行的行程规划师。
任务：根据活动序列、通勤时间和每日约束，生成精确到分钟的每日时间线骨架。

### 时间线 slot 类型
- hotel_breakfast: 酒店早餐（含早餐时生成，通常 07:00-08:00）
- poi: 景点/活动（entity_id + name + 预估时长）
- commute: 通勤段（mode = JR / 巴士 / 步行 / 出租车 / 新幹線，note = 具体线路）
- flex_meal: 弹性午餐（optional=true，可跳过或改为小吃）
- dinner: 晚餐时段（entity_id 可为 null，表示待定）
- hotel_checkin: 酒店入住
- hotel_checkout: 酒店退房

### 时间规则
1. 第一个活动开始时间 ≥ 日出时间或 07:00（取较晚者）
2. 最后一个活动结束时间 ≤ 日落后 2 小时或 21:00（取较早者）
3. 通勤 slot 必须插在两个活动之间，时长 ≥ commute_from_prev_mins
4. 午餐时段在 11:30-13:30 之间插入，标记 optional=true
5. 晚餐时段在 18:00-20:00 之间插入
6. 酒店含早餐 → 插入 hotel_breakfast slot
7. 酒店含晚餐 → 不插入 dinner slot，改为 hotel_dinner slot
8. 各 slot 之间不能有时间重叠
9. 允许留 15-30 分钟缓冲（buffer）在密集行程之间

### 输出格式
严格输出 JSON，结构如下（不要输出其他内容）：
{{
  "timeline": [
    {{
      "day": 1,
      "date": "2026-04-01",
      "slots": [
        {{"time": "08:00-08:30", "type": "hotel_breakfast", "name": "酒店早餐"}},
        {{"time": "09:00-11:00", "type": "poi", "entity_id": "xxx", "name": "伏见稻荷大社"}},
        {{"time": "11:15-11:30", "type": "commute", "mode": "JR", "note": "JR稲荷→東福寺"}},
        {{"time": "12:00-13:00", "type": "flex_meal", "name": "午餐", "optional": true}},
        ...
      ]
    }}
  ]
}}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict:
    """从 AI 输出中提取 JSON。"""
    text = text.strip()

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试从 code block 中提取
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试从第一个 { 到最后一个 }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从 AI 输出中提取有效 JSON，原文前 500 字符：{text[:500]}")


def _build_user_prompt(
    resolved_sequences: list[dict],
    daily_constraints: list[DailyConstraints],
    hotel_plan: dict,
) -> str:
    """构建发给 Sonnet 的 user prompt。"""
    parts: list[str] = []

    parts.append("## 酒店信息")
    parts.append(json.dumps(hotel_plan, ensure_ascii=False, indent=2))
    parts.append("")

    parts.append("## 每日约束")
    for dc in daily_constraints:
        parts.append(f"### {dc.date} ({dc.day_of_week})")
        parts.append(f"- 日出: {dc.sunrise}，日落: {dc.sunset}")
        parts.append(f"- 酒店含早餐: {'是' if dc.hotel_breakfast_included else '否'}")
        parts.append(f"- 酒店含晚餐: {'是' if dc.hotel_dinner_included else '否'}")
        if dc.anchors:
            parts.append(f"- 锚点: {json.dumps(dc.anchors, ensure_ascii=False)}")
        if dc.closed_entities:
            parts.append(f"- 定休实体: {dc.closed_entities}")
        parts.append("")

    parts.append("## 活动序列（Step 11 冲突修复后）")
    for day_seq in resolved_sequences:
        day = day_seq.get("day", "?")
        date = day_seq.get("date", "?")
        parts.append(f"### 第 {day} 天 ({date})")
        for act in day_seq.get("activities", []):
            parts.append(
                f"- {act.get('name', '?')} (entity_id={act.get('entity_id', 'N/A')}, "
                f"type={act.get('type', '?')}, "
                f"{act.get('start_time', '?')}-{act.get('end_time', '?')}, "
                f"commute_from_prev={act.get('commute_from_prev_mins', 0)}min)"
            )
        parts.append("")

    parts.append("请为每天生成精确到分钟的时间线骨架，包含所有 slot 类型。")
    return "\n".join(parts)


def _build_fallback_timeline(
    resolved_sequences: list[dict],
    daily_constraints: list[DailyConstraints],
) -> dict:
    """API 失败时的 fallback：直接用活动序列构建基本时间线。"""
    timeline: list[dict] = []

    dc_map = {dc.date: dc for dc in daily_constraints}

    for day_seq in resolved_sequences:
        day = day_seq.get("day", 0)
        date = day_seq.get("date", "")
        dc = dc_map.get(date)

        slots: list[dict] = []

        # 酒店早餐
        if dc and dc.hotel_breakfast_included:
            slots.append(
                {
                    "time": "07:00-08:00",
                    "type": "hotel_breakfast",
                    "name": "酒店早餐",
                }
            )

        # 活动 slot
        for act in day_seq.get("activities", []):
            start = act.get("start_time", "09:00")
            end = act.get("end_time", "10:00")
            slots.append(
                {
                    "time": f"{start}-{end}",
                    "type": act.get("type", "poi"),
                    "entity_id": act.get("entity_id"),
                    "name": act.get("name", ""),
                }
            )

        # 弹性午餐
        slots.append(
            {
                "time": "12:00-13:00",
                "type": "flex_meal",
                "name": "午餐",
                "optional": True,
            }
        )

        # 晚餐
        if dc and dc.hotel_dinner_included:
            slots.append(
                {
                    "time": "19:00-20:00",
                    "type": "hotel_dinner",
                    "name": "酒店晚餐",
                }
            )
        else:
            slots.append(
                {
                    "time": "19:00-20:00",
                    "type": "dinner",
                    "entity_id": None,
                    "name": "待定晚餐",
                }
            )

        # 按时间排序
        slots.sort(key=lambda s: s.get("time", "00:00"))

        timeline.append(
            {
                "day": day,
                "date": date,
                "slots": slots,
            }
        )

    return {"timeline": timeline}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def build_timeline(
    resolved_sequences: list[dict],
    daily_constraints: list[DailyConstraints],
    hotel_plan: dict,
    circle: CircleProfile,
    api_key: str | None = None,
) -> dict:
    """
    生成精确到分钟的每日时间线骨架。

    Args:
        resolved_sequences: Step 11 输出（冲突修复后的每日活动序列）
        daily_constraints: Step 8 输出（每日约束：日出日落、酒店含餐等）
        hotel_plan: Step 7 输出（酒店方案：位置、含餐信息等）
        api_key: Anthropic API Key，不传则从 settings 获取

    Returns:
        {
          "timeline": [
            {
              "day": 1,
              "date": "2026-04-01",
              "slots": [
                {"time": "08:00-08:30", "type": "hotel_breakfast", "name": "酒店早餐"},
                {"time": "09:00-11:00", "type": "poi", "entity_id": "xxx", "name": "伏见稻荷大社"},
                {"time": "11:30-11:45", "type": "commute", "mode": "JR", "note": "JR稲荷→東福寺"},
                {"time": "12:00-13:00", "type": "flex_meal", "name": "午餐", "optional": true},
                {"time": "13:30-15:30", "type": "poi", "entity_id": "yyy", "name": "清水寺"},
                {"time": "16:00-17:00", "type": "poi", "entity_id": "zzz", "name": "八坂神社"},
                {"time": "17:30-18:00", "type": "commute", "mode": "巴士", "note": "回酒店"},
                {"time": "19:00-20:00", "type": "dinner", "entity_id": null, "name": "待定晚餐"},
              ]
            }
          ]
        }
    """
    resolved_key = api_key or settings.anthropic_api_key
    if not resolved_key:
        logger.error("[时间线] 未提供 Anthropic API Key，使用 fallback")
        return _build_fallback_timeline(resolved_sequences, daily_constraints)

    if not resolved_sequences:
        logger.warning("[时间线] resolved_sequences 为空，返回空时间线")
        return {"timeline": []}

    user_prompt = _build_user_prompt(
        resolved_sequences,
        daily_constraints,
        hotel_plan,
    )

    logger.info(
        "[时间线] 调用 Sonnet 生成 %d 天的精确时间线，model=%s",
        len(resolved_sequences),
        AI_MODEL,
    )

    client = anthropic.AsyncAnthropic(api_key=resolved_key)

    try:
        response = await client.messages.create(
            model=AI_MODEL,
            max_tokens=AI_MAX_OUTPUT_TOKENS,
            system=_build_system_prompt(circle),
            messages=[{"role": "user", "content": user_prompt}],
        )

        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text

        if not text_content:
            logger.error("[时间线] Sonnet 返回空内容，使用 fallback")
            return _build_fallback_timeline(resolved_sequences, daily_constraints)

        result = _extract_json(text_content)

        # 验证结构
        if "timeline" not in result:
            logger.warning("[时间线] AI 输出缺少 timeline 字段，尝试包装")
            if isinstance(result, list):
                result = {"timeline": result}
            else:
                logger.error("[时间线] AI 输出结构异常，使用 fallback")
                return _build_fallback_timeline(resolved_sequences, daily_constraints)

        # 验证天数
        ai_days = len(result["timeline"])
        expected_days = len(resolved_sequences)
        if ai_days != expected_days:
            logger.warning(
                "[时间线] AI 输出 %d 天，期望 %d 天",
                ai_days,
                expected_days,
            )

        logger.info(
            "[时间线] 生成完成: %d 天, 共 %d 个 slot",
            ai_days,
            sum(len(d.get("slots", [])) for d in result["timeline"]),
        )
        return result

    except anthropic.APIError as e:
        logger.error("[时间线] Anthropic API 错误: %s，使用 fallback", e)
        return _build_fallback_timeline(resolved_sequences, daily_constraints)
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("[时间线] JSON 解析失败: %s，使用 fallback", e)
        return _build_fallback_timeline(resolved_sequences, daily_constraints)

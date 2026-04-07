"""
step15_plan_b.py — Plan B 备选方案（Sonnet）

为每天准备 1-2 个 Plan B 选项（下雨/体力不支/预约失败）。

替代规则：
  1. 户外活动 → 找同走廊的室内替代
  2. 高强度活动 → 找低强度替代
  3. 需预约活动 → 找无需预约替代

API: claude-sonnet-4-6（普通模式，不用 extended thinking）
"""

import json
import logging
import re

import anthropic

from app.core.config import settings
from app.domains.planning_v2.models import CandidatePool, CircleProfile, DailyConstraints

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AI_MODEL = "claude-sonnet-4-6"
AI_MAX_OUTPUT_TOKENS = 16000

# 标签分类
OUTDOOR_TAGS = frozenset(
    {
        "outdoor",
        "garden",
        "park",
        "hiking",
        "beach",
        "mountain",
        "shrine_outdoor",
        "temple_garden",
        "nature",
        "scenic_walk",
        "户外",
        "庭院",
        "公园",
        "登山",
    }
)

INDOOR_TAGS = frozenset(
    {
        "indoor",
        "museum",
        "gallery",
        "shopping",
        "aquarium",
        "onsen",
        "spa",
        "theater",
        "arcade",
        "department_store",
        "室内",
        "博物馆",
        "美术馆",
        "商场",
        "温泉",
    }
)

RESERVATION_TAGS = frozenset(
    {
        "reservation_required",
        "booking_required",
        "limited_entry",
        "预约",
        "要预约",
        "限定入场",
    }
)

HEAVY_TAGS = frozenset(
    {
        "hiking",
        "mountain",
        "long_walk",
        "体力要求高",
        "stairs_many",
        "登山",
        "远足",
    }
)


def _build_system_prompt(circle: CircleProfile) -> str:
    region = circle.region_desc
    return f"""\
你是一位经验丰富的{region}旅行规划师。
任务：为每天准备 1-2 个 Plan B 备选活动，应对以下场景：

### 触发场景（trigger）
- rain: 下雨天 → 用室内活动替代户外活动
- fatigue: 体力不支 → 用轻松活动替代高强度活动
- reservation_fail: 预约失败 → 用无需预约的活动替代

### 替代规则
1. 替代活动必须在同一天的主走廊范围内（避免额外通勤）
2. 替代活动不能与当天其他活动重复
3. 每天最多 2 个 Plan B
4. 优先选择 grade 较高的替代活动
5. rain 替代：必须是室内活动（博物馆、商场、温泉等）
6. fatigue 替代：必须是轻松活动（咖啡厅、购物、小型展览等）
7. reservation_fail 替代：必须无需预约

### 输出格式
严格输出 JSON，结构如下（不要输出其他内容）：
{{
  "plan_b": [
    {{
      "day": 1,
      "alternatives": [
        {{
          "trigger": "rain",
          "replace_entity": "xxx",
          "replace_name": "伏见稻荷大社",
          "alternative_entity": "yyy",
          "alternative_name": "京都国立博物馆",
          "reason": "室内替代，同东山走廊，步行10分钟"
        }}
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


def _classify_entity(tags: list[str]) -> dict:
    """分析实体标签，返回分类标记。"""
    tag_set = frozenset(t.lower() for t in tags)
    return {
        "is_outdoor": bool(tag_set & OUTDOOR_TAGS),
        "is_indoor": bool(tag_set & INDOOR_TAGS),
        "needs_reservation": bool(tag_set & RESERVATION_TAGS),
        "is_heavy": bool(tag_set & HEAVY_TAGS),
    }


def _pool_to_summary(pool: list[CandidatePool]) -> list[dict]:
    """将 CandidatePool 列表转换为精简摘要。"""
    items: list[dict] = []
    for c in pool:
        classification = _classify_entity(c.tags or [])
        item: dict = {
            "entity_id": c.entity_id,
            "name": c.name_zh,
            "grade": c.grade,
            "tags": c.tags[:8] if c.tags else [],
            "visit_minutes": c.visit_minutes,
            "is_indoor": classification["is_indoor"],
            "is_outdoor": classification["is_outdoor"],
            "needs_reservation": classification["needs_reservation"],
            "is_heavy": classification["is_heavy"],
        }
        items.append(item)
    return items


def _build_user_prompt(
    timeline: dict,
    poi_pool: list[CandidatePool],
    daily_constraints: list[DailyConstraints],
) -> str:
    """构建发给 Sonnet 的 user prompt。"""
    parts: list[str] = []

    # 每日时间线
    parts.append("## 每日时间线（Step 12 输出）")
    for day_tl in timeline.get("timeline", []):
        day = day_tl.get("day", "?")
        date = day_tl.get("date", "?")
        parts.append(f"### 第 {day} 天 ({date})")
        for slot in day_tl.get("slots", []):
            slot_type = slot.get("type", "?")
            name = slot.get("name", "")
            eid = slot.get("entity_id", "")
            time_range = slot.get("time", "?")
            line = f"  - {time_range} [{slot_type}] {name}"
            if eid:
                line += f" (entity_id={eid})"
            parts.append(line)
        parts.append("")

    # 每日约束
    parts.append("## 每日约束")
    for dc in daily_constraints:
        parts.append(f"- {dc.date} ({dc.day_of_week}): 日出 {dc.sunrise}, 日落 {dc.sunset}")
    parts.append("")

    # 候选池（可用于替代的实体）
    parts.append("## 可用替代活动候选池")
    pool_summary = _pool_to_summary(poi_pool)
    # 按分类分组呈现
    indoor = [p for p in pool_summary if p.get("is_indoor")]
    light = [p for p in pool_summary if not p.get("is_heavy") and not p.get("is_outdoor")]
    no_reservation = [p for p in pool_summary if not p.get("needs_reservation")]

    parts.append(f"### 室内活动 ({len(indoor)} 个，可用于 rain 替代)")
    parts.append(json.dumps(indoor[:30], ensure_ascii=False))
    parts.append("")
    parts.append(f"### 轻松活动 ({len(light)} 个，可用于 fatigue 替代)")
    parts.append(json.dumps(light[:30], ensure_ascii=False))
    parts.append("")
    parts.append(f"### 无需预约 ({len(no_reservation)} 个，可用于 reservation_fail 替代)")
    parts.append(json.dumps(no_reservation[:30], ensure_ascii=False))
    parts.append("")

    parts.append("请为每天识别需要备选的活动，并从候选池中选择合适的替代。每天最多 2 个 Plan B。")
    return "\n".join(parts)


def _build_fallback_plan_b(
    timeline: dict,
    poi_pool: list[CandidatePool],
) -> dict:
    """API 失败时的 fallback：基于标签匹配简单生成 Plan B。"""
    plan_b: list[dict] = []

    # 预分类候选池
    indoor_candidates = [c for c in poi_pool if _classify_entity(c.tags or [])["is_indoor"]]
    indoor_candidates.sort(key=lambda c: {"S": 0, "A": 1, "B": 2, "C": 3}.get(c.grade, 4))

    for day_tl in timeline.get("timeline", []):
        day = day_tl.get("day", 0)
        alternatives: list[dict] = []

        for slot in day_tl.get("slots", []):
            if slot.get("type") != "poi":
                continue
            if len(alternatives) >= 2:
                break

            entity_id = slot.get("entity_id")
            if not entity_id:
                continue

            # 查找实体标签
            source_entity = next(
                (c for c in poi_pool if c.entity_id == entity_id),
                None,
            )
            if source_entity is None:
                continue

            classification = _classify_entity(source_entity.tags or [])

            # 如果是户外活动，找室内替代
            if classification["is_outdoor"] and indoor_candidates:
                # 排除当天已在时间线中的实体
                day_entity_ids = {
                    s.get("entity_id") for s in day_tl.get("slots", []) if s.get("entity_id")
                }
                candidate = next(
                    (c for c in indoor_candidates if c.entity_id not in day_entity_ids),
                    None,
                )
                if candidate:
                    alternatives.append(
                        {
                            "trigger": "rain",
                            "replace_entity": entity_id,
                            "replace_name": slot.get("name", ""),
                            "alternative_entity": candidate.entity_id,
                            "alternative_name": candidate.name_zh,
                            "reason": "fallback: 室内替代户外活动",
                        }
                    )

        plan_b.append(
            {
                "day": day,
                "alternatives": alternatives,
            }
        )

    return {"plan_b": plan_b}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def build_plan_b(
    timeline: dict,
    poi_pool: list[CandidatePool],
    daily_constraints: list[DailyConstraints],
    circle: CircleProfile,
    api_key: str | None = None,
) -> dict:
    """
    为每天准备 1-2 个 Plan B 备选活动。

    Args:
        timeline: Step 12 输出（每日时间线骨架）
        poi_pool: 候选池（可用于替代的实体列表）
        daily_constraints: Step 8 输出（每日约束）
        api_key: Anthropic API Key，不传则从 settings 获取

    Returns:
        {
          "plan_b": [
            {
              "day": 1,
              "alternatives": [
                {
                  "trigger": "rain",
                  "replace_entity": "xxx",
                  "replace_name": "伏见稻荷大社",
                  "alternative_entity": "yyy",
                  "alternative_name": "京都国立博物馆",
                  "reason": "室内替代，同东山走廊",
                }
              ]
            }
          ]
        }
    """
    resolved_key = api_key or settings.anthropic_api_key
    if not resolved_key:
        logger.error("[Plan B] 未提供 Anthropic API Key，使用 fallback")
        return _build_fallback_plan_b(timeline, poi_pool)

    if not timeline.get("timeline"):
        logger.warning("[Plan B] timeline 为空，返回空 Plan B")
        return {"plan_b": []}

    user_prompt = _build_user_prompt(timeline, poi_pool, daily_constraints)

    logger.info(
        "[Plan B] 调用 Sonnet 为 %d 天生成备选方案，model=%s",
        len(timeline.get("timeline", [])),
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
            logger.error("[Plan B] Sonnet 返回空内容，使用 fallback")
            return _build_fallback_plan_b(timeline, poi_pool)

        result = _extract_json(text_content)

        # 验证结构
        if "plan_b" not in result:
            logger.warning("[Plan B] AI 输出缺少 plan_b 字段")
            if isinstance(result, list):
                result = {"plan_b": result}
            else:
                logger.error("[Plan B] AI 输出结构异常，使用 fallback")
                return _build_fallback_plan_b(timeline, poi_pool)

        # 验证每天最多 2 个替代
        for day_plan in result.get("plan_b", []):
            alts = day_plan.get("alternatives", [])
            if len(alts) > 2:
                logger.warning(
                    "[Plan B] 第 %d 天有 %d 个替代，裁剪为 2 个",
                    day_plan.get("day", "?"),
                    len(alts),
                )
                day_plan["alternatives"] = alts[:2]

        total_alts = sum(len(d.get("alternatives", [])) for d in result.get("plan_b", []))
        logger.info(
            "[Plan B] 完成: %d 天，共 %d 个备选方案",
            len(result["plan_b"]),
            total_alts,
        )
        return result

    except anthropic.APIError as e:
        logger.error("[Plan B] Anthropic API 错误: %s，使用 fallback", e)
        return _build_fallback_plan_b(timeline, poi_pool)
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("[Plan B] JSON 解析失败: %s，使用 fallback", e)
        return _build_fallback_plan_b(timeline, poi_pool)

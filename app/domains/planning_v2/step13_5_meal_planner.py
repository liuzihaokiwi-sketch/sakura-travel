"""
step13_5_meal_planner.py — 餐厅选择（Sonnet）

从 Step 13 餐厅候选池中为每餐选择具体餐厅。

选择规则：
  1. 酒店含早餐 → breakfast = null
  2. 酒店含晚餐 → dinner = null
  3. 午餐从 lunch_pool 选（优先正餐，备选咖啡厅）
  4. 不同天不重复同一菜系
  5. 寿司/拉面全程最多各出现 2 次

API: claude-sonnet-4-6（普通模式，不用 extended thinking）
"""

import json
import logging
import re

import anthropic

from app.core.config import settings
from app.domains.planning_v2.models import (
    CandidatePool,
    CircleProfile,
    DailyConstraints,
    UserConstraints,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AI_MODEL = "claude-sonnet-4-6"
AI_MAX_OUTPUT_TOKENS = 16000

# 全程出现上限
CUISINE_FREQUENCY_CAP: dict[str, int] = {
    "sushi": 2,
    "ramen": 2,
    "寿司": 2,
    "拉面": 2,
}


def _build_system_prompt(circle: CircleProfile) -> str:
    region = circle.region_desc
    return f"""\
你是一位精通{region}美食的旅行餐食规划师。
任务：从候选餐厅池中为每天的每餐选择具体餐厅。

### 选择规则（必须严格遵守）
1. 酒店含早餐 → breakfast 设为 null
2. 酒店含晚餐 → dinner 设为 null
3. 午餐优先从 restaurants 池选正餐，如果当天行程紧凑可选 cafes 池
4. 不同天不得重复同一菜系（如第1天吃了拉面，第2天不能再选拉面）
5. 寿司/拉面全程最多各出现 2 次
6. 优先选择 in_main_corridor=true 的餐厅（距当天活动近）
7. 考虑用户预算等级（budget_tier）
8. 晚餐选择时考虑距酒店的距离

### 输出格式
严格输出 JSON，结构如下（不要输出其他内容）：
{{
  "meal_selections": [
    {{
      "day": 1,
      "breakfast": null,
      "lunch": {{
        "entity_id": "xxx",
        "name": "某拉面店",
        "cuisine": "ramen",
        "type": "restaurant",
        "why": "在东山走廊，步行5分钟"
      }},
      "dinner": {{
        "entity_id": "yyy",
        "name": "某居酒屋",
        "cuisine": "izakaya",
        "type": "restaurant",
        "why": "距酒店近，评分高"
      }}
    }}
  ],
  "cuisine_variety_check": true
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


def _pool_to_summary(pool: list[CandidatePool], label: str) -> list[dict]:
    """将 CandidatePool 列表转换为精简摘要供 prompt 使用。"""
    items: list[dict] = []
    for c in pool:
        item: dict = {
            "entity_id": c.entity_id,
            "name": c.name_zh,
            "grade": c.grade,
            "tags": c.tags[:5] if c.tags else [],
            "cost_local": c.cost_local,
            "visit_minutes": c.visit_minutes,
        }
        signals = c.review_signals or {}
        if signals.get("in_main_corridor"):
            item["in_corridor"] = True
        if signals.get("tabelog_score"):
            item["tabelog"] = signals.get("tabelog_score")
        if signals.get("michelin_star"):
            item["michelin"] = signals.get("michelin_star")
        items.append(item)
    return items


def _build_user_prompt(
    restaurant_pool: dict,
    timeline: dict,
    daily_constraints: list[DailyConstraints],
    user_constraints: UserConstraints,
) -> str:
    """构建发给 Sonnet 的 user prompt。"""
    parts: list[str] = []

    # 用户画像
    profile = user_constraints.user_profile or {}
    parts.append("## 用户画像")
    parts.append(f"- 预算等级: {profile.get('budget_tier', 'mid')}")
    parts.append(f"- 出行类型: {profile.get('party_type', '未知')}")
    if profile.get("must_have_tags"):
        parts.append(f"- 必需标签: {profile['must_have_tags']}")
    parts.append("")

    # 每日约束
    parts.append("## 每日约束（酒店含餐）")
    for dc in daily_constraints:
        bf = "含" if dc.hotel_breakfast_included else "不含"
        dn = "含" if dc.hotel_dinner_included else "不含"
        parts.append(f"- {dc.date} ({dc.day_of_week}): 早餐{bf}, 晚餐{dn}")
    parts.append("")

    # 时间线
    parts.append("## 每日时间线（Step 12 输出）")
    for day_tl in timeline.get("timeline", []):
        day = day_tl.get("day", "?")
        date = day_tl.get("date", "?")
        parts.append(f"### 第 {day} 天 ({date})")
        for slot in day_tl.get("slots", []):
            parts.append(
                f"  - {slot.get('time', '?')} [{slot.get('type', '?')}] {slot.get('name', '')}"
            )
        parts.append("")

    # 餐厅候选池
    parts.append("## 餐厅候选池")

    bp = restaurant_pool.get("breakfast_pool", [])
    if bp:
        parts.append(f"### 早餐池 ({len(bp)} 家)")
        parts.append(json.dumps(_pool_to_summary(bp, "breakfast"), ensure_ascii=False))
    else:
        parts.append("### 早餐池: 空（酒店含早餐）")
    parts.append("")

    lunch_pool = restaurant_pool.get("lunch_pool", {})
    lr = lunch_pool.get("restaurants", [])
    lc = lunch_pool.get("cafes", [])
    parts.append(f"### 午餐正餐池 ({len(lr)} 家)")
    parts.append(json.dumps(_pool_to_summary(lr, "lunch_rest"), ensure_ascii=False))
    parts.append(f"### 午餐咖啡厅池 ({len(lc)} 家)")
    parts.append(json.dumps(_pool_to_summary(lc, "lunch_cafe"), ensure_ascii=False))
    parts.append("")

    dp = restaurant_pool.get("dinner_pool", [])
    if dp:
        parts.append(f"### 晚餐池 ({len(dp)} 家)")
        parts.append(json.dumps(_pool_to_summary(dp, "dinner"), ensure_ascii=False))
    else:
        parts.append("### 晚餐池: 空（酒店含晚餐）")
    parts.append("")

    parts.append("请为每天的每餐选择具体餐厅。注意菜系多样性和频率限制。")
    return "\n".join(parts)


def _build_fallback_selections(
    restaurant_pool: dict,
    timeline: dict,
    daily_constraints: list[DailyConstraints],
) -> dict:
    """API 失败时的 fallback：简单轮询分配餐厅。"""
    dc_map = {dc.date: dc for dc in daily_constraints}

    lunch_rest = restaurant_pool.get("lunch_pool", {}).get("restaurants", [])
    dinner_pool = restaurant_pool.get("dinner_pool", [])
    breakfast_pool = restaurant_pool.get("breakfast_pool", [])

    meal_selections: list[dict] = []
    lunch_idx = 0
    dinner_idx = 0
    breakfast_idx = 0

    for day_tl in timeline.get("timeline", []):
        day = day_tl.get("day", 0)
        date = day_tl.get("date", "")
        dc = dc_map.get(date)

        selection: dict = {"day": day}

        # 早餐
        if dc and dc.hotel_breakfast_included:
            selection["breakfast"] = None
        elif breakfast_pool:
            bp = breakfast_pool[breakfast_idx % len(breakfast_pool)]
            selection["breakfast"] = {
                "entity_id": bp.entity_id,
                "name": bp.name_zh,
                "cuisine": "breakfast",
                "type": "restaurant",
                "why": "fallback 自动分配",
            }
            breakfast_idx += 1
        else:
            selection["breakfast"] = None

        # 午餐
        if lunch_rest:
            lr = lunch_rest[lunch_idx % len(lunch_rest)]
            selection["lunch"] = {
                "entity_id": lr.entity_id,
                "name": lr.name_zh,
                "cuisine": "unknown",
                "type": "restaurant",
                "why": "fallback 自动分配",
            }
            lunch_idx += 1
        else:
            selection["lunch"] = None

        # 晚餐
        if dc and dc.hotel_dinner_included:
            selection["dinner"] = None
        elif dinner_pool:
            dp = dinner_pool[dinner_idx % len(dinner_pool)]
            selection["dinner"] = {
                "entity_id": dp.entity_id,
                "name": dp.name_zh,
                "cuisine": "unknown",
                "type": "restaurant",
                "why": "fallback 自动分配",
            }
            dinner_idx += 1
        else:
            selection["dinner"] = None

        meal_selections.append(selection)

    return {
        "meal_selections": meal_selections,
        "cuisine_variety_check": False,  # fallback 不保证菜系多样性
    }


def _validate_cuisine_frequency(result: dict) -> dict:
    """验证并修正菜系频率限制。返回修正后的 result（添加 warnings）。"""
    cuisine_count: dict[str, int] = {}
    warnings: list[str] = []

    for sel in result.get("meal_selections", []):
        for meal_key in ("breakfast", "lunch", "dinner"):
            meal = sel.get(meal_key)
            if meal and isinstance(meal, dict):
                cuisine = (meal.get("cuisine") or "").lower()
                if cuisine:
                    cuisine_count[cuisine] = cuisine_count.get(cuisine, 0) + 1

    for cuisine, cap in CUISINE_FREQUENCY_CAP.items():
        actual = cuisine_count.get(cuisine, 0)
        if actual > cap:
            warnings.append(f"菜系 '{cuisine}' 出现 {actual} 次，超过上限 {cap} 次")

    if warnings:
        result["cuisine_warnings"] = warnings
        result["cuisine_variety_check"] = False
        logger.warning("[餐食选择] 菜系频率超标: %s", "; ".join(warnings))

    return result


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def select_meals(
    restaurant_pool: dict,
    timeline: dict,
    daily_constraints: list[DailyConstraints],
    user_constraints: UserConstraints,
    circle: CircleProfile,
    api_key: str | None = None,
) -> dict:
    """
    从餐厅候选池中为每餐选择具体餐厅。

    Args:
        restaurant_pool: Step 13 输出（breakfast/lunch/dinner pools）
        timeline: Step 12 输出（每日时间线骨架）
        daily_constraints: Step 8 输出（每日约束）
        user_constraints: Step 1 输出（用户约束）
        api_key: Anthropic API Key，不传则从 settings 获取

    Returns:
        {
          "meal_selections": [
            {
              "day": 1,
              "breakfast": null,  # 酒店含早餐
              "lunch": {
                "entity_id": "xxx",
                "name": "某拉面店",
                "cuisine": "ramen",
                "type": "restaurant",
                "why": "在东山走廊，步行5分钟",
              },
              "dinner": {
                "entity_id": "yyy",
                "name": "某居酒屋",
                "cuisine": "izakaya",
                "type": "restaurant",
                "why": "距酒店近，评分高",
              }
            }
          ],
          "cuisine_variety_check": true,
        }
    """
    resolved_key = api_key or settings.anthropic_api_key
    if not resolved_key:
        logger.error("[餐食选择] 未提供 Anthropic API Key，使用 fallback")
        return _build_fallback_selections(
            restaurant_pool,
            timeline,
            daily_constraints,
        )

    if not timeline.get("timeline"):
        logger.warning("[餐食选择] timeline 为空，返回空选择")
        return {"meal_selections": [], "cuisine_variety_check": True}

    user_prompt = _build_user_prompt(
        restaurant_pool,
        timeline,
        daily_constraints,
        user_constraints,
    )

    logger.info(
        "[餐食选择] 调用 Sonnet 为 %d 天选择餐厅，model=%s",
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
            logger.error("[餐食选择] Sonnet 返回空内容，使用 fallback")
            return _build_fallback_selections(
                restaurant_pool,
                timeline,
                daily_constraints,
            )

        result = _extract_json(text_content)

        # 验证结构
        if "meal_selections" not in result:
            logger.warning("[餐食选择] AI 输出缺少 meal_selections 字段")
            if isinstance(result, list):
                result = {"meal_selections": result, "cuisine_variety_check": True}
            else:
                logger.error("[餐食选择] AI 输出结构异常，使用 fallback")
                return _build_fallback_selections(
                    restaurant_pool,
                    timeline,
                    daily_constraints,
                )

        # 验证菜系频率
        result = _validate_cuisine_frequency(result)

        # 确保 cuisine_variety_check 字段存在
        if "cuisine_variety_check" not in result:
            result["cuisine_variety_check"] = True

        logger.info(
            "[餐食选择] 完成: %d 天的餐食已选择，cuisine_variety=%s",
            len(result["meal_selections"]),
            result["cuisine_variety_check"],
        )
        return result

    except anthropic.APIError as e:
        logger.error("[餐食选择] Anthropic API 错误: %s，使用 fallback", e)
        return _build_fallback_selections(
            restaurant_pool,
            timeline,
            daily_constraints,
        )
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("[餐食选择] JSON 解析失败: %s，使用 fallback", e)
        return _build_fallback_selections(
            restaurant_pool,
            timeline,
            daily_constraints,
        )

"""
step16_handbook.py — 手账本内容生成（Sonnet）

生成手账本装饰内容：
  - 每个活动的简短介绍文案（copy_zh）
  - 内行贴士（insider_tip）
  - 拍照点推荐（photo_spot）
  - 高强度日的"活力补给站"（附近休息点推荐）
  - 每日旅行小贴士（daily_tip）

rest_stops 规则：
  1. 只在 intensity=heavy 的日程生成
  2. 从 poi_pool 中筛选 tags 含 cafe/sweets/rest 的实体
  3. 必须在当天主走廊内
  4. 每天最多 3 个休息推荐

API: claude-sonnet-4-6（普通模式，不用 extended thinking）
"""

import json
import logging
import re

import anthropic

from app.core.config import settings
from app.domains.planning_v2.models import CandidatePool, CircleProfile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AI_MODEL = "claude-sonnet-4-6"
AI_MAX_OUTPUT_TOKENS = 16000
MAX_REST_STOPS_PER_DAY = 3

# 休息站相关标签
REST_STOP_TAGS = frozenset(
    {
        "cafe",
        "coffee",
        "sweets",
        "dessert",
        "bakery",
        "tea",
        "tea_house",
        "rest",
        "rest_area",
        "gelato",
        "ice_cream",
        "patisserie",
        "咖啡",
        "甜品",
        "茶",
        "休息",
    }
)

# 高强度判断标签
HEAVY_TAGS = frozenset(
    {
        "hiking",
        "mountain",
        "long_walk",
        "stairs_many",
        "登山",
        "远足",
        "体力要求高",
    }
)


def _build_system_prompt(circle: CircleProfile) -> str:
    region = circle.region_desc
    return f"""\
你是一位热爱{region}文化的旅行手账内容创作师。
任务：为手账本生成高质量的装饰内容，让旅行者在旅途中翻阅时感到愉悦和实用。

### 内容要求

#### activity_cards（每个活动一张卡片）
- copy_zh: 30-50字的中文介绍文案，生动有趣，突出该景点的独特魅力
- insider_tip: 只有当地人或资深旅行者才知道的贴士（最佳时间、隐藏入口、省钱技巧等）
- photo_spot: 最佳拍照地点（具体到地名或楼层）

#### daily_tip（每日小贴士）
- 针对当天行程的实用建议（天气着装、交通卡充值、文化礼仪等）
- 到达日：适应建议
- 离开日：打包和退税提醒
- 高强度日：体力分配建议

#### rest_stops（仅高强度日）
- 咖啡厅、甜品店或休息点推荐
- 必须在当天活动走廊内
- 每个推荐包含 name、type、why、near_activity

### 输出格式
严格输出 JSON，结构如下（不要输出其他内容）：
{{
  "handbook": {{
    "days": [
      {{
        "day": 1,
        "daily_tip": "到达日不要安排太多，先适应时差",
        "activity_cards": [
          {{
            "entity_id": "xxx",
            "copy_zh": "千本鸟居的朱红色隧道...",
            "insider_tip": "清晨6点前到，几乎没人",
            "photo_spot": "四ツ辻展望台"
          }}
        ],
        "rest_stops": []
      }}
    ]
  }}
}}

### 文案风格
- 亲切自然，像朋友推荐
- 避免百科全书式的干燥描述
- 可以用比喻、感官描写
- 贴士要具体可操作，不要空泛的"建议提前到达"
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


def _is_heavy_day(day_tl: dict, poi_pool: list[CandidatePool]) -> bool:
    """判断某天是否为高强度日。"""
    poi_count = 0
    total_minutes = 0
    has_heavy_entity = False

    pool_map = {c.entity_id: c for c in poi_pool}

    for slot in day_tl.get("slots", []):
        if slot.get("type") != "poi":
            continue
        poi_count += 1

        # 估算时长
        time_range = slot.get("time", "")
        if "-" in time_range:
            parts = time_range.split("-")
            try:
                h1, m1 = parts[0].strip().split(":")
                h2, m2 = parts[1].strip().split(":")
                mins = (int(h2) * 60 + int(m2)) - (int(h1) * 60 + int(m1))
                total_minutes += max(mins, 0)
            except (ValueError, IndexError):
                pass

        # 检查是否有高强度实体
        eid = slot.get("entity_id")
        if eid and eid in pool_map:
            entity_tags = set(t.lower() for t in (pool_map[eid].tags or []))
            if entity_tags & HEAVY_TAGS:
                has_heavy_entity = True

    # 5+ 个 POI 或总活动 > 7 小时 或含高强度实体 → 高强度日
    return poi_count >= 5 or total_minutes >= 420 or has_heavy_entity


def _find_rest_stop_candidates(
    poi_pool: list[CandidatePool],
    day_entity_ids: set[str],
) -> list[dict]:
    """从候选池中筛选适合作为休息站的实体。"""
    candidates: list[dict] = []
    for c in poi_pool:
        if c.entity_id in day_entity_ids:
            continue  # 排除当天已安排的

        tag_set = frozenset(t.lower() for t in (c.tags or []))
        if not (tag_set & REST_STOP_TAGS):
            continue

        candidates.append(
            {
                "entity_id": c.entity_id,
                "name": c.name_zh,
                "grade": c.grade,
                "tags": c.tags[:5] if c.tags else [],
                "in_corridor": (c.review_signals or {}).get("in_main_corridor", False),
            }
        )

    # 走廊内优先，然后按 grade 排序
    candidates.sort(key=lambda x: (0 if x.get("in_corridor") else 1, x.get("grade", "Z")))
    return candidates


def _build_user_prompt(
    timeline: dict,
    meal_selections: dict,
    plan_b: dict,
    poi_pool: list[CandidatePool],
) -> str:
    """构建发给 Sonnet 的 user prompt。"""
    parts: list[str] = []
    pool_map = {c.entity_id: c for c in poi_pool}

    parts.append("## 每日时间线")
    for day_tl in timeline.get("timeline", []):
        day = day_tl.get("day", "?")
        date = day_tl.get("date", "?")
        is_heavy = _is_heavy_day(day_tl, poi_pool)
        intensity_label = "高强度" if is_heavy else "普通"
        parts.append(f"### 第 {day} 天 ({date}) — {intensity_label}")

        for slot in day_tl.get("slots", []):
            slot_type = slot.get("type", "?")
            name = slot.get("name", "")
            time_range = slot.get("time", "?")
            eid = slot.get("entity_id", "")
            line = f"  - {time_range} [{slot_type}] {name}"

            # 附加实体信息
            if eid and eid in pool_map:
                entity = pool_map[eid]
                line += f" (grade={entity.grade}, tags={entity.tags[:5]})"
            parts.append(line)
        parts.append("")

    # 餐食选择
    parts.append("## 餐食安排")
    for sel in meal_selections.get("meal_selections", []):
        day = sel.get("day", "?")
        parts.append(f"### 第 {day} 天")
        for meal_key in ("breakfast", "lunch", "dinner"):
            meal = sel.get(meal_key)
            if meal and isinstance(meal, dict):
                parts.append(f"  - {meal_key}: {meal.get('name', '?')} ({meal.get('why', '')})")
            else:
                parts.append(f"  - {meal_key}: 酒店含餐")
        parts.append("")

    # Plan B
    parts.append("## Plan B 备选")
    for day_plan in plan_b.get("plan_b", []):
        day = day_plan.get("day", "?")
        alts = day_plan.get("alternatives", [])
        if alts:
            parts.append(f"### 第 {day} 天")
            for alt in alts:
                parts.append(
                    f"  - [{alt.get('trigger', '?')}] "
                    f"{alt.get('replace_name', '?')} → {alt.get('alternative_name', '?')} "
                    f"({alt.get('reason', '')})"
                )
            parts.append("")

    # 高强度日的休息站候选
    parts.append("## 休息站候选（仅高强度日使用）")
    for day_tl in timeline.get("timeline", []):
        if not _is_heavy_day(day_tl, poi_pool):
            continue
        day = day_tl.get("day", "?")
        day_entity_ids = {s.get("entity_id") for s in day_tl.get("slots", []) if s.get("entity_id")}
        rest_candidates = _find_rest_stop_candidates(poi_pool, day_entity_ids)
        if rest_candidates:
            parts.append(f"### 第 {day} 天候选 ({len(rest_candidates)} 个)")
            parts.append(json.dumps(rest_candidates[:10], ensure_ascii=False))
            parts.append("")

    parts.append(
        "请为每天的每个活动生成手账卡片内容。"
        "高强度日额外生成 rest_stops（最多3个）。"
        "每天生成一条 daily_tip。"
    )
    return "\n".join(parts)


def _build_fallback_handbook(
    timeline: dict,
    poi_pool: list[CandidatePool],
) -> dict:
    """API 失败时的 fallback：生成基本骨架结构。"""
    days: list[dict] = []

    for day_tl in timeline.get("timeline", []):
        day = day_tl.get("day", 0)
        is_heavy = _is_heavy_day(day_tl, poi_pool)

        activity_cards: list[dict] = []
        for slot in day_tl.get("slots", []):
            if slot.get("type") != "poi":
                continue
            eid = slot.get("entity_id")
            name = slot.get("name", "")
            activity_cards.append(
                {
                    "entity_id": eid,
                    "copy_zh": f"{name} — 值得一去的好地方",
                    "insider_tip": "建议提前查看官网确认开放时间",
                    "photo_spot": "入口处",
                }
            )

        # 高强度日的休息站
        rest_stops: list[dict] = []
        if is_heavy:
            day_entity_ids = {
                s.get("entity_id") for s in day_tl.get("slots", []) if s.get("entity_id")
            }
            rest_candidates = _find_rest_stop_candidates(poi_pool, day_entity_ids)
            for rc in rest_candidates[:MAX_REST_STOPS_PER_DAY]:
                rest_stops.append(
                    {
                        "name": rc.get("name", ""),
                        "type": "cafe",
                        "why": "fallback: 附近休息点",
                        "near_activity": "",
                    }
                )

        days.append(
            {
                "day": day,
                "daily_tip": "享受旅途，不要赶行程",
                "activity_cards": activity_cards,
                "rest_stops": rest_stops,
            }
        )

    return {"handbook": {"days": days}}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def generate_handbook_content(
    timeline: dict,
    meal_selections: dict,
    plan_b: dict,
    poi_pool: list[CandidatePool],
    circle: CircleProfile,
    api_key: str | None = None,
) -> dict:
    """
    生成手账本装饰内容。

    Args:
        timeline: Step 12 输出（每日时间线骨架）
        meal_selections: Step 13.5 输出（餐食选择）
        plan_b: Step 15 输出（Plan B 备选方案）
        poi_pool: 候选池（用于查询实体详情和休息站候选）
        api_key: Anthropic API Key，不传则从 settings 获取

    Returns:
        {
          "handbook": {
            "days": [
              {
                "day": 1,
                "daily_tip": "到达日不要安排太多，先适应时差",
                "activity_cards": [
                  {
                    "entity_id": "xxx",
                    "copy_zh": "千本鸟居的朱红色隧道...",
                    "insider_tip": "清晨6点前到，几乎没人",
                    "photo_spot": "四ツ辻展望台",
                  }
                ],
                "rest_stops": [
                  {
                    "name": "% Arabica 京都东山",
                    "type": "cafe",
                    "why": "走累了来杯咖啡，看八坂塔",
                    "near_activity": "清水寺",
                  }
                ],
              }
            ]
          }
        }
    """
    resolved_key = api_key or settings.anthropic_api_key
    if not resolved_key:
        logger.error("[手账本] 未提供 Anthropic API Key，使用 fallback")
        return _build_fallback_handbook(timeline, poi_pool)

    if not timeline.get("timeline"):
        logger.warning("[手账本] timeline 为空，返回空手账")
        return {"handbook": {"days": []}}

    user_prompt = _build_user_prompt(timeline, meal_selections, plan_b, poi_pool)

    logger.info(
        "[手账本] 调用 Sonnet 生成 %d 天的手账内容，model=%s",
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
            logger.error("[手账本] Sonnet 返回空内容，使用 fallback")
            return _build_fallback_handbook(timeline, poi_pool)

        result = _extract_json(text_content)

        # 验证结构
        if "handbook" not in result:
            logger.warning("[手账本] AI 输出缺少 handbook 字段，尝试包装")
            if "days" in result:
                result = {"handbook": result}
            elif isinstance(result, list):
                result = {"handbook": {"days": result}}
            else:
                logger.error("[手账本] AI 输出结构异常，使用 fallback")
                return _build_fallback_handbook(timeline, poi_pool)

        # 验证 rest_stops 限制
        for day_data in result.get("handbook", {}).get("days", []):
            rest_stops = day_data.get("rest_stops", [])
            if len(rest_stops) > MAX_REST_STOPS_PER_DAY:
                logger.warning(
                    "[手账本] 第 %d 天有 %d 个休息站，裁剪为 %d 个",
                    day_data.get("day", "?"),
                    len(rest_stops),
                    MAX_REST_STOPS_PER_DAY,
                )
                day_data["rest_stops"] = rest_stops[:MAX_REST_STOPS_PER_DAY]

        total_cards = sum(
            len(d.get("activity_cards", [])) for d in result.get("handbook", {}).get("days", [])
        )
        total_rests = sum(
            len(d.get("rest_stops", [])) for d in result.get("handbook", {}).get("days", [])
        )
        logger.info(
            "[手账本] 完成: %d 天，%d 张活动卡片，%d 个休息站",
            len(result["handbook"]["days"]),
            total_cards,
            total_rests,
        )
        return result

    except anthropic.APIError as e:
        logger.error("[手账本] Anthropic API 错误: %s，使用 fallback", e)
        return _build_fallback_handbook(timeline, poi_pool)
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("[手账本] JSON 解析失败: %s，使用 fallback", e)
        return _build_fallback_handbook(timeline, poi_pool)

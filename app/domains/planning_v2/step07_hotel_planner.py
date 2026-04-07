"""
step07_hotel_planner.py -- 住宿选择（Sonnet）

从酒店候选池中选择住宿方案。
考虑：走廊覆盖、预算、体验等级、含餐情况、交通摩擦度。

API: claude-sonnet-4-6
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

from app.core.config import settings
from app.domains.planning_v2.models import CandidatePool, CircleProfile, UserConstraints

logger = logging.getLogger(__name__)

# -- 常量 --------------------------------------------------------------------

MODEL_ID = "claude-sonnet-4-6"
MAX_TOKENS = 3000

# Grade / 星级权重（用于 fallback）
_GRADE_ORDER: dict[str, int] = {"S": 0, "A": 1, "B": 2, "C": 3}


def _build_system_prompt(circle: CircleProfile) -> str:
    region = circle.region_desc
    return f"""\
你是一位经验丰富的{region}住宿顾问。

任务：从候选酒店列表中为旅客选出最佳住宿方案（1-2家酒店）。

决策原则：
1. 通勤优先：平均通勤时间越短越好，理想 < 30 分钟
2. 走廊覆盖：酒店位置应覆盖尽可能多天的主走廊
3. 预算匹配：不超出用户预算偏好
4. 含餐加分：含早餐的酒店可省去早晨觅食时间
5. 体验等级：高评分酒店优先（google_rating, booking_score）
6. 换酒店策略：只有当行程中有明显的区域切换（如大阪→京都）时才建议换酒店
7. 如果不需要换酒店，只选 1 家 primary

输出纯 JSON，不要任何额外文字。"""


# -- 公共接口 -----------------------------------------------------------------


async def select_hotels(
    hotel_pool: list[CandidatePool],
    commute_results: list[dict],
    daily_activities: dict,
    user_constraints: UserConstraints,
    circle: CircleProfile,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    从候选池中选择住宿方案。

    Args:
        hotel_pool: Step 6 输出的酒店候选池。
        commute_results: Step 7.5 通勤检查结果列表，每项含
            hotel_id, hotel_name, status, avg_commute_minutes 等。
        daily_activities: Step 5 输出（用于判断走廊覆盖）。
        user_constraints: 用户约束。
        api_key: 可选，覆盖默认 ANTHROPIC_API_KEY。

    Returns:
        {
          "hotel_plan": {
            "primary": {
              "hotel_id": "xxx",
              "name": "xxx",
              "nights": 4,
              "cost_per_night_jpy": 12000,
              "meals_included": {"breakfast": true, "dinner": false},
              "check_in": "15:00",
              "check_out": "11:00",
              "avg_commute_minutes": 25,
              "why_selected": "...",
            },
            "secondary": null,
          },
          "hotel_switch_day": null,
          "thinking_tokens_used": 0,
        }
    """
    if not hotel_pool:
        logger.warning("[Step07] 酒店候选池为空，返回空方案")
        return _empty_result()

    # 合并酒店数据与通勤数据
    hotel_summaries = _build_hotel_summaries(hotel_pool, commute_results)

    # 过滤掉通勤 fail 的酒店
    viable = [h for h in hotel_summaries if h["status"] != "fail"]
    if not viable:
        logger.warning("[Step07] 所有酒店通勤 fail，放宽到 warning")
        viable = hotel_summaries  # 全部保留，让 AI/规则选

    # 提取每日走廊信息
    daily_corridors = _extract_daily_corridors(daily_activities)

    # 提取用户偏好
    user_profile = user_constraints.user_profile or {}
    budget_tier = user_profile.get("budget_tier", "mid")
    total_days = user_constraints.trip_window.get("total_days", 4)

    # 调用 Sonnet
    try:
        result = await _call_sonnet(
            hotel_summaries=viable,
            daily_corridors=daily_corridors,
            budget_tier=budget_tier,
            total_days=total_days,
            circle=circle,
            api_key=api_key,
        )
    except Exception as exc:
        logger.error("[Step07] Sonnet 调用失败，降级到规则引擎: %s", exc)
        result = _rule_based_fallback(
            hotel_summaries=viable,
            total_days=total_days,
        )
        result["fallback_reason"] = str(exc)

    return result


# -- 数据准备 -----------------------------------------------------------------


def _build_hotel_summaries(
    hotel_pool: list[CandidatePool],
    commute_results: list[dict],
) -> list[dict]:
    """将酒店候选池与通勤检查结果合并为摘要列表。"""
    commute_map: dict[str, dict] = {r["hotel_id"]: r for r in commute_results}

    summaries: list[dict] = []
    for hotel in hotel_pool:
        commute = commute_map.get(hotel.entity_id, {})

        # 从 review_signals 提取评分
        signals = hotel.review_signals or {}
        star_rating = signals.get("star_rating", 0)
        google_rating = signals.get("google_rating", 0)
        booking_score = signals.get("booking_score", 0)
        amenities = signals.get("amenities", [])
        distance_km = signals.get("distance_from_poi_center_km", 0)

        # 从 open_hours 提取 check-in/out
        oh = hotel.open_hours or {}
        check_in = oh.get("check_in_time", "15:00")
        check_out = oh.get("check_out_time", "11:00")

        # 含餐判断（从 amenities 或 tags 推断）
        amenities_lower = {a.lower() for a in amenities} if amenities else set()
        tags_lower = {t.lower() for t in hotel.tags} if hotel.tags else set()
        all_signals = amenities_lower | tags_lower

        has_breakfast = any(
            kw in all_signals for kw in ("breakfast", "朝食", "朝食付き", "breakfast_included")
        )
        has_dinner = any(
            kw in all_signals
            for kw in ("dinner", "夕食", "夕食付き", "dinner_included", "half_board")
        )

        summaries.append(
            {
                "hotel_id": hotel.entity_id,
                "name": hotel.name_zh,
                "grade": hotel.grade,
                "cost_local": hotel.cost_local,
                "star_rating": star_rating,
                "google_rating": google_rating,
                "booking_score": booking_score,
                "check_in": check_in,
                "check_out": check_out,
                "meals_included": {
                    "breakfast": has_breakfast,
                    "dinner": has_dinner,
                },
                "distance_from_center_km": distance_km,
                "avg_commute_minutes": commute.get("avg_commute_minutes", 0),
                "max_commute_minutes": commute.get("max_commute_minutes", 0),
                "status": commute.get("status", "pass"),
                "commute_details": commute.get("commute_details", []),
                "tags": hotel.tags[:8] if hotel.tags else [],
                "latitude": hotel.latitude,
                "longitude": hotel.longitude,
            }
        )

    return summaries


def _extract_daily_corridors(daily_activities: dict) -> list[dict]:
    """从 daily_activities 中提取每日主走廊信息。"""
    corridors: list[dict] = []
    for day in daily_activities.get("daily_activities", []):
        corridors.append(
            {
                "day": day.get("day", 0),
                "city": day.get("city", ""),
                "main_corridor": day.get("main_corridor", ""),
                "intensity": day.get("intensity", "moderate"),
            }
        )
    return corridors


# -- Sonnet 调用 --------------------------------------------------------------


async def _call_sonnet(
    hotel_summaries: list[dict],
    daily_corridors: list[dict],
    budget_tier: str,
    total_days: int,
    circle: CircleProfile,
    api_key: str | None = None,
) -> dict[str, Any]:
    """调用 Sonnet 选出最佳住宿方案。"""

    client = anthropic.AsyncAnthropic(
        api_key=api_key or settings.anthropic_api_key,
    )

    user_prompt = _build_user_prompt(
        hotel_summaries=hotel_summaries,
        daily_corridors=daily_corridors,
        budget_tier=budget_tier,
        total_days=total_days,
    )

    logger.info(
        "[Step07] 调用 Sonnet 选择酒店, %d 候选, %d 天",
        len(hotel_summaries),
        total_days,
    )

    response = await client.messages.create(
        model=MODEL_ID,
        max_tokens=MAX_TOKENS,
        system=_build_system_prompt(circle),
        messages=[{"role": "user", "content": user_prompt}],
    )

    # 提取文本
    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content += block.text

    # 解析 JSON
    parsed = _parse_json_response(text_content)
    if parsed is None:
        logger.warning("[Step07] Sonnet 返回无法解析为 JSON，降级规则引擎")
        return _rule_based_fallback(
            hotel_summaries=hotel_summaries,
            total_days=total_days,
        )

    # 校验并规范化输出结构
    result = _normalize_sonnet_output(parsed, hotel_summaries, total_days)
    result["thinking_tokens_used"] = 0  # Sonnet 普通模式不用 thinking

    logger.info(
        "[Step07] Sonnet 选定酒店: primary=%s, secondary=%s, switch_day=%s",
        result["hotel_plan"]["primary"].get("name") if result["hotel_plan"]["primary"] else "None",
        (
            result["hotel_plan"]["secondary"].get("name")
            if result["hotel_plan"].get("secondary")
            else "None"
        ),
        result.get("hotel_switch_day"),
    )

    return result


def _build_user_prompt(
    hotel_summaries: list[dict],
    daily_corridors: list[dict],
    budget_tier: str,
    total_days: int,
) -> str:
    """构建发送给 Sonnet 的用户提示。"""
    sections: list[str] = []

    # 用户信息
    sections.append("## 旅行信息")
    sections.append(f"- 预算等级: {budget_tier}")
    sections.append(f"- 总天数: {total_days}")
    sections.append("")

    # 每日走廊
    sections.append("## 每日主走廊")
    for dc in daily_corridors:
        sections.append(
            f"- Day {dc['day']}: {dc['city']} / {dc['main_corridor']} ({dc['intensity']})"
        )
    sections.append("")

    # 检查是否有城市切换（用于判断是否需要换酒店）
    cities_in_order = [dc["city"] for dc in daily_corridors if dc["city"]]
    city_switches = []
    for i in range(1, len(cities_in_order)):
        if cities_in_order[i] != cities_in_order[i - 1]:
            city_switches.append(
                f"Day {i} -> Day {i + 1}: {cities_in_order[i - 1]} -> {cities_in_order[i]}"
            )
    if city_switches:
        sections.append("## 城市切换")
        for sw in city_switches:
            sections.append(f"- {sw}")
        sections.append("")

    # 酒店候选
    sections.append(f"## 候选酒店 ({len(hotel_summaries)} 家)")
    for h in hotel_summaries:
        meals = []
        if h["meals_included"].get("breakfast"):
            meals.append("含早餐")
        if h["meals_included"].get("dinner"):
            meals.append("含晚餐")
        meals_str = ", ".join(meals) if meals else "不含餐"

        ratings = []
        if h["google_rating"]:
            ratings.append(f"Google={h['google_rating']}")
        if h["booking_score"]:
            ratings.append(f"Booking={h['booking_score']}")
        if h["star_rating"]:
            ratings.append(f"{h['star_rating']}星")
        ratings_str = ", ".join(ratings) if ratings else "无评分"

        sections.append(
            f"- [{h['hotel_id']}] {h['name']}\n"
            f"  价格: {h['cost_local']}JPY/晚 | 评分: {ratings_str}\n"
            f"  通勤: 平均{h['avg_commute_minutes']}min, "
            f"最长{h['max_commute_minutes']}min "
            f"(状态: {h['status']})\n"
            f"  入住/退房: {h['check_in']}/{h['check_out']} | {meals_str}\n"
            f"  距中心: {h['distance_from_center_km']}km | "
            f"grade={h['grade']}"
        )
    sections.append("")

    # 输出格式
    sections.append("## 输出格式")
    sections.append(
        "输出严格 JSON（不要任何额外文字），结构如下:\n"
        "{\n"
        '  "hotel_plan": {\n'
        '    "primary": {\n'
        '      "hotel_id": "实体ID",\n'
        '      "name": "酒店名称",\n'
        '      "nights": 住宿晚数,\n'
        '      "cost_per_night_jpy": 每晚价格,\n'
        '      "meals_included": {"breakfast": bool, "dinner": bool},\n'
        '      "check_in": "15:00",\n'
        '      "check_out": "11:00",\n'
        '      "avg_commute_minutes": 平均通勤分钟数,\n'
        '      "why_selected": "选择理由（一句话）"\n'
        "    },\n"
        '    "secondary": null 或同结构对象\n'
        "  },\n"
        '  "hotel_switch_day": null 或第几天换酒店\n'
        "}\n\n"
        "如果不需要换酒店：secondary=null, hotel_switch_day=null。\n"
        "如果需要换酒店：secondary 填第二家酒店，hotel_switch_day 填切换的天数。"
    )

    return "\n".join(sections)


# -- JSON 解析 ----------------------------------------------------------------


def _parse_json_response(raw_text: str) -> dict | None:
    """从 Sonnet 返回文本中解析 JSON 对象。"""
    if not raw_text or not raw_text.strip():
        return None

    text = raw_text.strip()

    # 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # markdown 代码块
    md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if md_match:
        try:
            return json.loads(md_match.group(1))
        except json.JSONDecodeError:
            pass

    # 找 { ... }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    logger.error("[Step07] 无法解析 Sonnet 返回: %s...", text[:200])
    return None


def _normalize_sonnet_output(
    parsed: dict,
    hotel_summaries: list[dict],
    total_days: int,
) -> dict:
    """
    校验并规范化 Sonnet 输出结构。

    确保 hotel_plan.primary 包含必要字段，
    如果 Sonnet 选的 hotel_id 不在候选列表中则回退。
    """
    summary_map = {h["hotel_id"]: h for h in hotel_summaries}

    hotel_plan = parsed.get("hotel_plan", {})
    primary_raw = hotel_plan.get("primary", {})
    secondary_raw = hotel_plan.get("secondary")
    switch_day = parsed.get("hotel_switch_day")

    primary = _validate_hotel_selection(primary_raw, summary_map, total_days)
    secondary = None
    if secondary_raw and isinstance(secondary_raw, dict):
        remaining_nights = total_days - (switch_day or total_days)
        if remaining_nights > 0:
            secondary = _validate_hotel_selection(
                secondary_raw,
                summary_map,
                remaining_nights,
            )

    # 如果 primary 为空，降级
    if not primary:
        logger.warning("[Step07] Sonnet 返回的 primary 无效，降级规则引擎")
        fallback = _rule_based_fallback(hotel_summaries, total_days)
        return fallback

    return {
        "hotel_plan": {
            "primary": primary,
            "secondary": secondary,
        },
        "hotel_switch_day": switch_day if secondary else None,
    }


def _validate_hotel_selection(
    raw: dict,
    summary_map: dict[str, dict],
    nights: int,
) -> dict | None:
    """校验单个酒店选择，补全缺失字段。"""
    hotel_id = raw.get("hotel_id", "")
    if not hotel_id:
        return None

    summary = summary_map.get(hotel_id)
    if not summary:
        logger.warning(
            "[Step07] Sonnet 选的 hotel_id=%s 不在候选列表中",
            hotel_id,
        )
        return None

    return {
        "hotel_id": hotel_id,
        "name": raw.get("name", summary["name"]),
        "nights": raw.get("nights", nights),
        "cost_per_night_jpy": raw.get(
            "cost_per_night_jpy",
            summary["cost_local"],
        ),
        "meals_included": raw.get(
            "meals_included",
            summary["meals_included"],
        ),
        "check_in": raw.get("check_in", summary["check_in"]),
        "check_out": raw.get("check_out", summary["check_out"]),
        "avg_commute_minutes": raw.get(
            "avg_commute_minutes",
            summary["avg_commute_minutes"],
        ),
        "why_selected": raw.get("why_selected", ""),
    }


# -- 规则引擎 fallback --------------------------------------------------------


def _rule_based_fallback(
    hotel_summaries: list[dict],
    total_days: int,
) -> dict[str, Any]:
    """
    当 Sonnet 调用失败时的规则引擎降级。

    策略：按通勤时间最短 + 评分最高选第一家酒店。
    评分公式: score = -avg_commute * 2 + google_rating * 10 + booking_score
    """
    logger.info("[Step07] 使用规则引擎 fallback 选择酒店")

    if not hotel_summaries:
        return _empty_result()

    def _score(h: dict) -> float:
        commute_penalty = h.get("avg_commute_minutes", 99) * 2
        google_bonus = (h.get("google_rating") or 0) * 10
        booking_bonus = h.get("booking_score") or 0
        grade_bonus = (4 - _GRADE_ORDER.get(h.get("grade", "C"), 3)) * 5
        breakfast_bonus = 5 if h.get("meals_included", {}).get("breakfast") else 0
        return -commute_penalty + google_bonus + booking_bonus + grade_bonus + breakfast_bonus

    ranked = sorted(hotel_summaries, key=_score, reverse=True)
    best = ranked[0]

    primary = {
        "hotel_id": best["hotel_id"],
        "name": best["name"],
        "nights": total_days,
        "cost_per_night_jpy": best["cost_local"],
        "meals_included": best["meals_included"],
        "check_in": best["check_in"],
        "check_out": best["check_out"],
        "avg_commute_minutes": best["avg_commute_minutes"],
        "why_selected": (
            f"规则选择: 通勤{best['avg_commute_minutes']}min, "
            f"google={best.get('google_rating', 'N/A')}, "
            f"grade={best.get('grade', 'N/A')}"
        ),
    }

    return {
        "hotel_plan": {
            "primary": primary,
            "secondary": None,
        },
        "hotel_switch_day": None,
        "thinking_tokens_used": 0,
    }


def _empty_result() -> dict[str, Any]:
    """返回空的酒店选择结果。"""
    return {
        "hotel_plan": {
            "primary": None,
            "secondary": None,
        },
        "hotel_switch_day": None,
        "thinking_tokens_used": 0,
    }

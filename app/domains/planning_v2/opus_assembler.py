"""
Opus 装配器 — 两步 Opus 调用替换规则拼装。

第一步：assemble_route_and_hotels
  输入：trip_constraints + policy + days.json(各城市) + hotels.json(各城市) + assembly_rules
  Opus 决策：城市顺序、每天选哪个 day 模板、每城市住哪家酒店
  输出：daily_plan（含 template_id + hotel_id）

第二步：assemble_restaurants
  输入：第一步的 daily_plan + restaurants.json(各城市) + budget_profile
  Opus 决策：每天每餐选哪家餐厅
  输出：daily_plan（补齐餐厅）

Fallback：Anthropic 不可用时自动切换阿里云 qwen-max（OpenAI 兼容接口）。
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, timedelta
from typing import Any

logger = logging.getLogger(__name__)

_ANTHROPIC_MODEL = "claude-opus-4-6"
_QWEN_MODEL = "qwen-max"
_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


# ── 公开接口 ──────────────────────────────────────────────────────────────────


async def assemble_route_and_hotels(
    constraints: dict[str, Any],
    policy: dict[str, Any],
    assembly_rules: dict[str, Any],
    city_days_map: dict[str, dict],
    city_hotels_map: dict[str, dict],
) -> dict[str, Any]:
    """
    第一步装配：Opus 决定城市顺序、日模板选择、酒店选择。

    Args:
        constraints: trip_constraints（来自表单）
        policy: policy.json 全量
        assembly_rules: assembly_rules.json 全量
        city_days_map: {city: days.json 内容}
        city_hotels_map: {city: hotels.json 内容}

    Returns:
        step1_result = {
            "city_allocation": [...],
            "daily_plans": [...],  # 含 template_id，无餐厅
            "hotel_selections": {...},  # city -> hotel_id
            "decisions": [...],
            "condition_summary": "...",
        }
    """
    # 硬筛候选池
    filtered_days = _filter_day_templates(constraints, city_days_map, policy)
    filtered_hotels = _filter_hotels(constraints, city_hotels_map, policy)

    # 筛选适用装配规则
    applicable_rules = _select_applicable_rules(constraints, assembly_rules)

    # 构建 prompt
    system_prompt = _build_step1_system_prompt(applicable_rules)
    user_prompt = _build_step1_user_prompt(
        constraints, policy, filtered_days, filtered_hotels
    )

    # 调用 Opus（失败时切阿里云）
    raw = await _call_opus(system_prompt, user_prompt)

    # 解析并补全
    result = _parse_step1_response(raw, constraints)
    return result


async def assemble_restaurants(
    daily_plans: list[dict],
    constraints: dict[str, Any],
    city_restaurants_map: dict[str, dict],
    budget_profile: dict[str, Any],
    policy: dict[str, Any],
    city_days_map: dict[str, dict] | None = None,
) -> list[dict]:
    """
    第二步装配：Opus 根据每天的模板和节奏选餐厅，同时校验第一步输出。

    Args:
        daily_plans: 第一步输出的 daily_plans
        constraints: trip_constraints
        city_restaurants_map: {city: restaurants.json 内容}
        budget_profile: 预算档位（dining_tier 等）
        policy: policy.json（餐饮硬约束）
        city_days_map: 候选模板库（供校验 template_id / core_entities）

    Returns:
        daily_plans（每天补齐 meal_selections，可能含 corrections）
    """
    # 硬筛餐厅池（营业时段 + 预算档位）
    filtered_restaurants = _filter_restaurants(
        daily_plans, city_restaurants_map, budget_profile, policy
    )

    # 硬筛候选模板（供校验用）
    filtered_days = None
    if city_days_map:
        filtered_days = _filter_day_templates(constraints, city_days_map, policy)

    system_prompt = _build_step2_system_prompt()
    user_prompt = _build_step2_user_prompt(
        daily_plans, constraints, filtered_restaurants, budget_profile, policy,
        filtered_days=filtered_days,
    )

    raw = await _call_opus(system_prompt, user_prompt)
    result = _parse_step2_response(raw, daily_plans)
    return result


# ── 辅助：人群类型推导 ──────────────────────────────────────────────────────────


def _derive_audience_type(party: dict) -> str:
    """从 party 信息推导人群类型，用于 fit_audience 过滤。"""
    children = party.get("children", 0)
    elderly = party.get("elderly", 0)
    adults = party.get("adults", 2)

    if children > 0:
        return "family"
    if elderly > 0:
        return "elderly"
    if adults == 2:
        return "couple"
    if adults >= 3:
        return "friends"
    return "default"


# ── 候选池硬筛 ────────────────────────────────────────────────────────────────


def _derive_trip_context(constraints: dict) -> dict:
    """从 constraints 推导硬筛上下文：季节、日期集合、人群。"""
    start = date.fromisoformat(constraints["dates"]["start"])
    end = date.fromisoformat(constraints["dates"]["end"])

    # 季节（按出发月份）
    month = start.month
    if month in (3, 4):
        season = "sakura"
    elif month in (5,):
        season = "spring"
    elif month in (6, 7, 8):
        season = "summer"
    elif month in (9, 10):
        season = "early_autumn"
    elif month in (11, 12):
        season = "koyo"
    else:
        season = "winter"

    # 旅行日期集合（MM-DD）
    travel_dates: set[str] = set()
    cur = start
    while cur <= end:
        travel_dates.add(cur.strftime("%m-%d"))
        cur += timedelta(days=1)

    return {
        "season": season,
        "travel_dates": travel_dates,
        "audience_type": _derive_audience_type(constraints.get("party", {})),
    }


def _eval_condition(condition: Any, ctx: dict) -> bool:
    """
    评估模板 condition 字段。返回 True = 保留在候选池。

    condition 类型：
    - None/空 → 无条件，保留
    - dict → exclude_party 检查（sagano_torokko_day）
    - str → 季节/日期/预算/运行时条件
    """
    if not condition:
        return True

    if isinstance(condition, dict):
        exclude = condition.get("exclude_party", [])
        return ctx["audience_type"] not in exclude

    cond = condition
    season = ctx["season"]
    travel_dates = ctx["travel_dates"]

    # season == 'X'
    m = re.search(r"season\s*==\s*'(\w+)'", cond)
    if m and season != m.group(1):
        return False

    # season in ['X', 'Y']
    m = re.search(r"season\s+in\s+\[([^\]]+)\]", cond)
    if m:
        allowed = re.findall(r"'(\w+)'", m.group(1))
        if season not in allowed:
            return False

    # travel_dates include M/DD（节日）
    m = re.search(r"travel_dates include (\d+)/(\d+)", cond)
    if m:
        mmdd = f"{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        if mmdd not in travel_dates:
            return False

    # visit_date == 'MM-DD'
    m = re.search(r"visit_date\s*==\s*'(\d{2}-\d{2})'", cond)
    if m and m.group(1) not in travel_dates:
        return False

    # budget in ['X', 'Y'] — 暂不筛（表单无预算档位字段），交给 Opus
    # 运行时条件（previous_day / already_scheduled / itinerary_includes）— 交给 Opus

    return True


def _filter_day_templates(
    constraints: dict,
    city_days_map: dict[str, dict],
    policy: dict,
) -> dict[str, list[dict]]:
    """硬筛 day 模板：季节/节日/人群/skip 过滤，其余交给 Opus。"""
    skip_entities = set(constraints.get("skip_entities", []))
    skip_tags = set(constraints.get("skip_tags", []))
    audience_type = _derive_audience_type(constraints.get("party", {}))
    ctx = _derive_trip_context(constraints)

    result: dict[str, list[dict]] = {}

    for city, days_data in city_days_map.items():
        templates = days_data.get("day_templates", [])
        filtered = []
        for tmpl in templates:
            asm = tmpl.get("assembly", {})
            tid = tmpl["template_id"]

            # skip_entities / skip_tags
            if tid in skip_entities:
                continue
            if any(tag in skip_tags for tag in tmpl.get("tags", [])):
                continue

            # fit_audience
            fit = tmpl.get("fit_audience", "all")
            if fit != "all" and audience_type not in (fit if isinstance(fit, list) else [fit]):
                continue

            # condition（季节/节日/运行时）
            if not _eval_condition(tmpl.get("condition"), ctx):
                continue

            filtered.append({
                "template_id": tid,
                "core_entities": tmpl.get("core_entities", []),
                "phase": asm.get("phase", "sightseeing"),
                "readable": _template_to_readable(tmpl),
            })
        result[city] = filtered

    return result


def _filter_hotels(
    constraints: dict,
    city_hotels_map: dict[str, dict],
    policy: dict,
) -> dict[str, list[dict]]:
    """硬筛酒店池：目前不做硬筛，全量给 Opus 选。"""
    result: dict[str, list[dict]] = {}
    for city, hotels_data in city_hotels_map.items():
        hotels = hotels_data.get("hotels", [])
        result[city] = [
            {
                "id": h["id"],
                "name_zh": h.get("name_zh", ""),
                "area": h.get("area", ""),
                "budget_tier": h.get("budget_tier", ""),
                "vibe_tags": h.get("vibe_tags", []),
                "facility_tags": h.get("facility_tags", []),
                "editor_note": h.get("editor_note", ""),
                "review_summary": (h.get("review") or {}).get("summary", ""),
            }
            for h in hotels
        ]
    return result


def _filter_restaurants(
    daily_plans: list[dict],
    city_restaurants_map: dict[str, dict],
    budget_profile: dict,
    policy: dict,
) -> dict[str, list[dict]]:
    """硬筛餐厅池：按预算档位过滤，给 Opus 精简候选。"""
    dining_tier = budget_profile.get("dining_tier", "local_good")
    tier_order = ["street", "local_good", "fine", "top"]
    tier_idx = tier_order.index(dining_tier) if dining_tier in tier_order else 1

    # 允许本档 + 相邻档（上下各一档）
    allowed_tiers = set()
    for i in range(max(0, tier_idx - 1), min(len(tier_order), tier_idx + 2)):
        allowed_tiers.add(tier_order[i])

    result: dict[str, list[dict]] = {}
    for city, restaurants_data in city_restaurants_map.items():
        restaurants = restaurants_data.get("restaurants", [])
        filtered = []
        for r in restaurants:
            r_tier = r.get("budget_tier", "local_good")
            if r_tier not in allowed_tiers:
                continue
            filtered.append({
                "id": r["id"],
                "name_zh": r.get("name_zh", ""),
                "cuisine": r.get("cuisine", ""),
                "area": r.get("area", ""),
                "budget_tier": r_tier,
                "meal_role": r.get("meal_role", "B"),
                "open_slots": r.get("open_slots", ["lunch", "dinner"]),
                "editor_note": r.get("editor_note", ""),
                "tabelog_rating": r.get("tabelog_rating"),
            })
        result[city] = filtered

    return result


def _select_applicable_rules(
    constraints: dict,
    assembly_rules: dict,
) -> list[dict]:
    """按 party/density/vibe 筛选适用的装配规则。"""
    party = constraints.get("party", {})
    density = constraints.get("density", "balanced")
    has_elderly = party.get("elderly", 0) > 0
    has_children = party.get("children", 0) > 0

    applicable = []
    for rule in assembly_rules.get("rules", []):
        applies_to = rule.get("applies_to", "*")
        if applies_to == "*":
            applicable.append(rule)
            continue
        # 列表匹配
        if isinstance(applies_to, list):
            match = False
            if density in applies_to:
                match = True
            if has_elderly and "elderly" in applies_to:
                match = True
            if has_children and "children" in applies_to:
                match = True
            if match:
                applicable.append(rule)

    return applicable


_PHASE_LABEL = {
    "arrival": "到达日候选",
    "departure": "离开日候选",
    "transfer": "换城日候选",
    "sightseeing": "游玩日候选",
}


def _format_templates_for_prompt(filtered_days: dict[str, list[dict]]) -> str:
    """把硬筛后的模板列表按城市+phase 分组，拼成 Opus 可读文本。"""
    parts = []
    # 先收集换城模板（跨城市，单独一节）
    transfer_templates = []

    for city, templates in filtered_days.items():
        # 按 phase 分组
        by_phase: dict[str, list[dict]] = {}
        for t in templates:
            phase = t.get("phase", "sightseeing")
            if phase == "transfer":
                transfer_templates.append(t)
                continue
            by_phase.setdefault(phase, []).append(t)

        if not by_phase:
            continue

        parts.append(f"\n### {city}\n")
        # 按固定顺序输出：arrival → sightseeing → departure
        for phase in ("arrival", "sightseeing", "departure"):
            group = by_phase.get(phase, [])
            if not group:
                continue
            parts.append(f"**{_PHASE_LABEL.get(phase, phase)}：**\n")
            for t in group:
                parts.append(t["readable"])
                parts.append("")

    # 换城模板单独一节
    if transfer_templates:
        parts.append("\n### 换城\n")
        parts.append(f"**{_PHASE_LABEL['transfer']}：**\n")
        for t in transfer_templates:
            parts.append(t["readable"])
            parts.append("")

    return "\n".join(parts)


# ── Prompt 构建 ───────────────────────────────────────────────────────────────


def _build_step1_system_prompt(applicable_rules: list[dict]) -> str:
    rules_text = "\n".join(
        f"- [{r['priority'].upper()}] {r['instruction']}"
        for r in applicable_rules
    )
    return f"""你是一个专业的日本关西旅行方案装配专家，正在为用户生成一份付费旅行手账本（国内298元标准）。

你的任务是根据用户的行程约束，从候选日模板库和酒店池中，选出最合适的组合。

装配原则（必须遵守）：
{rules_text}

输出要求：
- 严格输出 JSON，不加任何解释文字
- JSON 结构见用户 prompt 中的 output_schema
- decisions 字段写2-3句人话，解释你为什么这样排（用户可见）
- 每个 daily_plan 的 template_reason 写一句内部理由（不对用户展示）"""


def _build_step1_user_prompt(
    constraints: dict,
    policy: dict,
    filtered_days: dict[str, list[dict]],
    filtered_hotels: dict[str, list[dict]],
) -> str:
    dates = constraints.get("dates", {})
    start = dates.get("start", "")
    end = dates.get("end", "")
    party = constraints.get("party", {"adults": 2, "children": 0, "elderly": 0})
    vibe = constraints.get("vibe", "classic")
    density = constraints.get("density", "balanced")
    pre_booked = constraints.get("pre_booked", [])
    notes = constraints.get("notes", "")
    include_entities = constraints.get("include_entities", [])
    city_adjustments = constraints.get("city_adjustments", [])

    # 计算有效天数
    if start and end:
        start_d = date.fromisoformat(start)
        end_d = date.fromisoformat(end)
        total_days = (end_d - start_d).days + 1
    else:
        total_days = 7

    city_alloc_rules = policy.get("city_allocation", {})

    output_schema = {
        "city_allocation": [
            {"city": "osaka", "days": 3, "nights": 2, "role": "primary"},
            {"city": "kyoto", "days": 2, "nights": 2, "role": "primary"},
        ],
        "hotel_selections": {
            "osaka": "hotel_id_here",
            "kyoto": "hotel_id_here",
        },
        "daily_plans": [
            {
                "day": 1,
                "city": "osaka",
                "template_id": "arrival_day",
                "title": "到达大阪",
                "description": "今天轻松融入城市节奏",
                "template_reason": "内部：到达日用轻松模板，不排重量级景点",
            }
        ],
        "decisions": ["大阪在前京都在后 — 先感受城市能量，后半段慢下来"],
        "condition_summary": "2026-04-03 ~ 04-09 | 2位成人 | 经典版 | 平衡节奏",
        "addable_experiences": [
            {"id": "nara", "icon": "🦌", "label": "和小鹿散个步", "description": "奈良的大草地和古寺"}
        ],
    }

    include_line = f"- 用户指定必须包含：{json.dumps(include_entities, ensure_ascii=False)}" if include_entities else ""
    city_adj_line = f"- 城市天数调整要求：{json.dumps(city_adjustments, ensure_ascii=False)}" if city_adjustments else ""

    return f"""用户行程约束：
- 日期：{start} 至 {end}（共{total_days}天）
- 到达时段：{dates.get('arrival_slot', 'afternoon')}，出发时段：{dates.get('departure_slot', 'morning')}
- 人员：{party.get('adults', 2)}位成人，{party.get('children', 0)}位儿童，{party.get('elderly', 0)}位老人
- 风格偏好：{vibe}
- 行程节奏：{density}
- 已预订：{json.dumps(pre_booked, ensure_ascii=False) if pre_booked else '无'}
- 特殊备注：{notes or '无'}
{include_line}
{city_adj_line}

城市天数最低要求（来自 policy）：
{json.dumps(city_alloc_rules.get('city_min_days', {}), ensure_ascii=False, indent=2)}

候选日模板库（按城市）：
{_format_templates_for_prompt(filtered_days)}

候选酒店池（按城市）：
{json.dumps(filtered_hotels, ensure_ascii=False, indent=2)}

请严格按以下 JSON schema 输出：
{json.dumps(output_schema, ensure_ascii=False, indent=2)}"""


def _build_step2_system_prompt() -> str:
    return """你是一个专业的日本关西美食顾问，正在为用户的每日行程配餐。

任务：根据每天的行程主题、节奏和位置，从候选餐厅池中选出最合适的午餐和晚餐。

餐厅选择原则：
- 同一天的午餐和晚餐菜系不能重复
- 餐厅所在区域要与当天活动区域匹配（不要让用户跨城区吃饭）
- 到达日午餐选轻松随意的，不排正式体验餐
- USJ日晚餐降一档（园内吃了一天），不安排高档正餐
- 体力消耗大的一天，晚餐优先舒适环境，不排需要排队的网红店
- 行程最后一晚考虑安排有仪式感的餐厅

前置校验（配餐前先检查第一步的行程方案，发现问题直接修正）：
- 每天的 template_id 必须存在于候选模板库中，不存在则换成候选库里最接近的
- daily_plans 天数必须等于行程总天数，多了删、少了补
- 城市不应乒乓（京都→大阪→京都），发现则调整顺序
- 酒店城市必须匹配当天住宿城市
- 不同天选的模板 core_entities 不应有交集（重复景点），发现则替换其中一天
如有修正，在输出的 corrections 字段列出修改内容和原因。无修正则 corrections 为空数组。

输出要求：
- 严格输出 JSON，不加任何解释文字
- 每个 meal_selection 包含餐厅 id、meal_role（A=主角体验/B=配角日常）、选择理由（一句话）
- corrections 字段：数组，每项 {"field": "修改了什么", "reason": "为什么"}"""


def _build_step2_user_prompt(
    daily_plans: list[dict],
    constraints: dict,
    filtered_restaurants: dict[str, list[dict]],
    budget_profile: dict,
    policy: dict,
    filtered_days: dict[str, list[dict]] | None = None,
) -> str:
    dining_tier = budget_profile.get("dining_tier", "local_good")
    dining_preference = budget_profile.get("dining_preference", "taste_first")

    output_schema = [
        {
            "day": 1,
            "meal_selections": {
                "lunch": {"restaurant_id": "xxx", "meal_role": "B", "reason": "到达日轻松午餐"},
                "dinner": {"restaurant_id": "yyy", "meal_role": "A", "reason": "第一晚大阪道顿堀正式开幕"},
            },
            "corrections": [],
        }
    ]

    # 候选模板摘要（供校验用，只传 id + core_entities 省 token）
    templates_ref = ""
    if filtered_days:
        ref_data = {
            city: [{"template_id": t["template_id"], "core_entities": t["core_entities"]}
                   for t in templates]
            for city, templates in filtered_days.items()
        }
        templates_ref = f"""
候选模板库（用于校验 template_id 和 core_entities，不要选不在此列表中的 template_id）：
{json.dumps(ref_data, ensure_ascii=False, indent=2)}
"""

    return f"""用户偏好：
- 餐饮档位：{dining_tier}
- 餐饮偏好：{dining_preference}
- 人员：{constraints.get('party', {})}

每日行程（需要配餐 + 需要校验的天）：
{json.dumps(daily_plans, ensure_ascii=False, indent=2)}
{templates_ref}
候选餐厅池（按城市，已按预算档位过滤）：
{json.dumps(filtered_restaurants, ensure_ascii=False, indent=2)}

餐饮硬约束（来自 policy）：
{json.dumps(policy.get('hard_constraints', {}).get('dining', {}), ensure_ascii=False, indent=2)}

请严格按以下 JSON schema 输出，每天都要有：
{json.dumps(output_schema, ensure_ascii=False, indent=2)}"""


# ── Opus API 调用 ─────────────────────────────────────────────────────────────


async def _call_opus(system_prompt: str, user_prompt: str) -> str:
    """调用 Opus，失败时 fallback 阿里云 qwen-max。"""
    try:
        return await _call_anthropic(system_prompt, user_prompt)
    except Exception as e:
        logger.warning("Anthropic API 失败，切换阿里云: %s", e)
        return await _call_qwen(system_prompt, user_prompt)


async def _call_anthropic(system_prompt: str, user_prompt: str) -> str:
    import anthropic

    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not auth_token and not api_key:
        raise RuntimeError("ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY not set")

    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    kwargs: dict = {}
    if base_url:
        kwargs["base_url"] = base_url
    if auth_token:
        kwargs["auth_token"] = auth_token
    else:
        kwargs["api_key"] = api_key
    client = anthropic.AsyncAnthropic(**kwargs)
    message = await client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


async def _call_qwen(system_prompt: str, user_prompt: str) -> str:
    import openai

    api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY / OPENAI_API_KEY not set")

    client = openai.AsyncOpenAI(
        api_key=api_key,
        base_url=_QWEN_BASE_URL,
    )
    response = await client.chat.completions.create(
        model=_QWEN_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=4096,
    )
    return response.choices[0].message.content or ""


# ── 响应解析 ──────────────────────────────────────────────────────────────────


def _parse_step1_response(raw: str, constraints: dict) -> dict[str, Any]:
    """解析第一步 Opus 输出，容错处理。"""
    try:
        # 提取 JSON（Opus 有时会在前后加说明文字）
        text = raw.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]
        result = json.loads(text)

        # 补全必要字段
        if "condition_summary" not in result:
            dates = constraints.get("dates", {})
            result["condition_summary"] = f"{dates.get('start', '')}–{dates.get('end', '')}"
        if "decisions" not in result:
            result["decisions"] = []
        if "addable_experiences" not in result:
            result["addable_experiences"] = []

        return result
    except Exception as e:
        logger.error("第一步 Opus 响应解析失败: %s\n原始输出: %s", e, raw[:500])
        raise RuntimeError(f"Opus step1 parse error: {e}") from e


def _parse_step2_response(raw: str, daily_plans: list[dict]) -> list[dict]:
    """解析第二步 Opus 输出，将餐厅选择+校验修正合并进 daily_plans。"""
    try:
        text = raw.strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            text = text[start:end]
        meal_results = json.loads(text)

        # 按 day 号合并
        meal_by_day = {r["day"]: r.get("meal_selections", {}) for r in meal_results}
        corrections_by_day = {r["day"]: r.get("corrections", []) for r in meal_results}

        # 收集所有 corrections 并记录日志
        all_corrections = []
        for day_num, corrs in corrections_by_day.items():
            for c in corrs:
                all_corrections.append({"day": day_num, **c})
        if all_corrections:
            logger.warning("Opus 第二步校验发现并修正了问题: %s", json.dumps(all_corrections, ensure_ascii=False))

        enriched = []
        for dp in daily_plans:
            day_num = dp.get("day")
            dp_copy = dict(dp)
            if day_num in meal_by_day:
                dp_copy["meal_selections"] = meal_by_day[day_num]
            enriched.append(dp_copy)
        return enriched
    except Exception as e:
        logger.error("第二步 Opus 响应解析失败: %s\n原始输出: %s", e, raw[:500])
        raise RuntimeError(f"Opus step2 parse error: {e}") from e


# ── 辅助 ─────────────────────────────────────────────────────────────────────


_BEST_PACE_ZH = {
    "compact": "推荐紧凑·景点密集",
    "standard": "标准节奏",
    "relaxed": "推荐悠闲·慢是灵魂",
    "locked": "强度固定·无法降级",
}
_AUDIENCE_ZH = {
    "all": "所有人群",
    "couple": "情侣",
    "friends": "闺蜜/朋友",
    "family": "亲子",
    "default": "通用",
    "elderly": "长辈",
}


def _translate_audience(fit: str | list) -> str:
    if isinstance(fit, list):
        return "、".join(_AUDIENCE_ZH.get(a, a) for a in fit)
    return _AUDIENCE_ZH.get(fit, fit)


def _extract_day_mood(description: str) -> str:
    """从 description 中提取 day_mood。"""
    for part in description.split("。"):
        part = part.strip()
        if part.startswith("day_mood:") or part.startswith("day_mood："):
            return part.split(":", 1)[-1].split("：", 1)[-1].strip()
    return ""


def _slot_to_line(slot: dict) -> str:
    """把单个 slot 转成一行可读文本（第一步选模板用，不含餐厅建议）。"""
    slot_type = slot.get("type", "")
    priority = slot.get("priority", "")
    area = slot.get("area", "")
    duration = slot.get("duration_min")
    note = slot.get("note", "")
    entity = slot.get("entity_hint", "")

    # 餐 slot：只标位置，不给选餐建议
    if slot_type == "meal":
        meal_label = "午餐" if "lunch" in slot.get("slot_id", "") else "晚餐"
        area_str = f" | {area}" if area else ""
        return f"- {meal_label}{area_str}"

    # shop_info / transport：跳过或简写
    if slot_type == "shop_info":
        return ""
    if slot_type == "transport":
        # 只保留关键交通信息
        if note:
            short = note.split("。")[0]
            return f"- 交通：{short}"
        return ""

    # P1/P2/P3 景点和活动
    label = entity or slot.get("slot_id", "")
    area_str = f" | {area}" if area else ""
    dur_str = f" | {duration}min" if duration else ""
    pri_str = f"[{priority}] " if priority else ""

    # 从 note 提取一句核心判断（第一个句号前，或前60字）
    core_note = ""
    if note:
        # 去掉价格和纯事实开头，找编辑判断
        sentences = [s.strip() for s in note.replace("——", "。").split("。") if s.strip()]
        # 取最有判断力的一句（通常不是第一句的价格信息）
        for s in sentences:
            if len(s) > 8 and not s.startswith("¥") and not s.startswith("免费"):
                core_note = s
                break
        if not core_note and sentences:
            core_note = sentences[0]
        if len(core_note) > 60:
            core_note = core_note[:60]

    note_str = f" — {core_note}" if core_note else ""
    return f"- {pri_str}{label}{area_str}{dur_str}{note_str}"


def _template_to_readable(tmpl: dict) -> str:
    """把模板 JSON 转成 Opus 可读的自然语言格式（第一步选模板用）。"""
    tid = tmpl["template_id"]
    label = tmpl.get("label", "")
    description = tmpl.get("description", "")
    hotel_note = tmpl.get("hotel_area_note", "")
    asm = tmpl.get("assembly", {})
    fit = tmpl.get("fit_audience", "all")
    weather = tmpl.get("weather_sensitive", False)
    core_ents = tmpl.get("core_entities", [])
    slots = tmpl.get("slots", [])
    # 多日模板
    days = tmpl.get("days")

    # 头部
    pace_zh = _BEST_PACE_ZH.get(asm.get("best_pace", ""), asm.get("best_pace", ""))
    audience_zh = _translate_audience(fit)
    mood = _extract_day_mood(description)

    header = f"## {label} ({tid})"
    mood_line = f"情绪：{mood}" if mood else ""
    meta_parts = [pace_zh]
    if weather:
        meta_parts.append("天气敏感")
    span = asm.get("span_days")
    if span:
        meta_parts.append(f"{span}日模板")
    meta_line = " | ".join(meta_parts)

    core_line = ""
    if core_ents:
        core_line = f"灵魂景点：{'、'.join(core_ents)} | {audience_zh}"
    else:
        core_line = f"适合人群：{audience_zh}"

    # 描述（去掉 day_mood 部分，已单独提取）
    desc_clean = description
    for marker in ["day_mood:", "day_mood："]:
        if marker in desc_clean:
            # 去掉 day_mood 那一句
            parts = desc_clean.split("。")
            parts = [p for p in parts if marker not in p]
            desc_clean = "。".join(parts)
    desc_clean = desc_clean.strip().rstrip("。")

    # 行程脉络
    if days:
        # 多日模板
        slot_lines = []
        for i, day_slots in enumerate(days):
            slot_lines.append(f"\n第{i+1}天：")
            for s in day_slots:
                line = _slot_to_line(s)
                if line:
                    slot_lines.append(line)
    else:
        slot_lines = []
        for s in slots:
            line = _slot_to_line(s)
            if line:
                slot_lines.append(line)

    # 组装
    lines = [header]
    if mood_line:
        lines.append(f"{mood_line} | {meta_line}")
    else:
        lines.append(meta_line)
    lines.append(core_line)
    lines.append("")
    if desc_clean:
        lines.append(desc_clean)
    lines.append("")
    if hotel_note:
        lines.append(f"住宿提示：{hotel_note}")
        lines.append("")
    lines.append("行程脉络：")
    lines.extend(slot_lines)

    return "\n".join(lines)

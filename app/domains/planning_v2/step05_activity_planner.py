"""
step05_activity_planner.py — 主活动+锚点选择（Opus深度决策）

调用 Opus 模型，从 POI 候选池中为每天选择：
  - 1-2 个主活动（main_activities）
  - 0-1 个时间锚点（如需在特定时间到达的活动）
  - 主走廊（main_corridor）

输入：
  - cities_by_day: Step 3 的城市组合方案
  - poi_pool: Step 4 的 CandidatePool 列表
  - user_constraints: 用户约束

输出：
  {
    "daily_activities": [
      {
        "day": 1,
        "city": "osaka",
        "theme": "到达+美食探索",
        "main_activities": [
          {"entity_id": "xxx", "name": "道顿堀", "visit_minutes": 90,
           "why": "关西第一站的经典体验"}
        ],
        "time_anchors": [],
        "main_corridor": "namba_dotonbori",
        "secondary_corridors": ["shinsaibashi"],
        "intensity": "light",
      },
      ...
    ],
    "unassigned_must_visit": [],
    "thinking_tokens_used": N,
  }

API：Anthropic Claude Opus
思考强度：deep（extended thinking, budget_tokens=12000）
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from typing import Any

import anthropic

from app.core.config import settings
from app.domains.planning_v2.models import CandidatePool, CircleProfile, UserConstraints

logger = logging.getLogger(__name__)

# ── 常量 ────────────────────────────────────────────────────────────────────

_OPUS_MODEL = "claude-opus-4-6"
_MAX_TOKENS = 6000
_THINKING_BUDGET = 12000

# Grade 排序权重（用于 fallback）
_GRADE_ORDER: dict[str, int] = {"S": 0, "A": 1, "B": 2, "C": 3}


def _build_system_prompt(circle: CircleProfile) -> str:
    region = circle.region_desc
    return f"""\
你是一位经验丰富的旅行规划师，专精{region}。

任务：为每天选择 1-2 个主活动、时间锚点和主走廊。

决策原则：
1. must_visit 的地点必须安排，且放在最合适的天
2. 同一走廊的景点尽量安排在同一天（减少通勤）
3. 考虑景点的最佳游览时间（寺庙清晨、夜景傍晚等）
4. 到达日和离开日只安排 1 个轻量活动
5. 高强度天(heavy)可安排 2 个主活动，低强度天(light)最多 1 个
6. 不要重复安排同类型景点（同一天不要 2 个寺庙）
7. 每天必须指定 main_corridor，用于后续住宿和交通规划
8. 全程必须覆盖多个不同体验桶（文化遗产、自然户外、市井体验、艺术体验等），不要只选一种类型
9. 尽量避免连续 2 天以同类体验为主活动（如连续 2 天都是寺社），连续 3 天同类是严重问题
10. 用户 must_have_tags 对应的体验类型要优先安排到最合适的日期和时段
11. 每个行程留出 1-2 天的"非主流"体验（市井漫步、本地体验、咖啡小店），保证节奏松弛

输出 JSON 格式，不要任何额外文字。"""


# ── 公共接口 ─────────────────────────────────────────────────────────────────


async def plan_daily_activities(
    cities_by_day: list[dict],
    poi_pool: list[CandidatePool],
    user_constraints: UserConstraints,
    *,
    circle: CircleProfile,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    调用 Opus 从 POI 候选池中为每天选择主活动、锚点和走廊。

    Args:
        cities_by_day: Step 3 输出，每天城市信息列表。
            每项至少包含 {"day": int, "city": str}，可含 "theme", "intensity" 等。
        poi_pool: Step 4 输出的 CandidatePool 列表。
        user_constraints: Step 1 输出的用户约束。
        api_key: 可选，覆盖默认 ANTHROPIC_API_KEY。

    Returns:
        dict 包含 daily_activities, unassigned_must_visit, thinking_tokens_used。
    """

    must_visit_ids = set(user_constraints.constraints.get("must_visit", []))
    user_profile = user_constraints.user_profile or {}

    # 构建 user prompt
    user_prompt = _build_user_prompt(
        cities_by_day=cities_by_day,
        poi_pool=poi_pool,
        must_visit_ids=must_visit_ids,
        user_profile=user_profile,
    )

    # 调用 Opus
    try:
        raw_result, thinking_tokens = await _call_opus(
            user_prompt=user_prompt,
            circle=circle,
            api_key=api_key,
        )
    except Exception as exc:
        logger.error(f"[Step05] Opus 调用失败，降级到规则引擎: {exc}")
        fallback = _rule_based_fallback(
            cities_by_day=cities_by_day,
            poi_pool=poi_pool,
            must_visit_ids=must_visit_ids,
        )
        fallback["thinking_tokens_used"] = 0
        fallback["fallback_reason"] = str(exc)
        return fallback

    # 解析 JSON
    parsed = _parse_opus_response(raw_result)
    if parsed is None:
        logger.warning("[Step05] Opus 返回结果无法解析为 JSON，降级到规则引擎")
        fallback = _rule_based_fallback(
            cities_by_day=cities_by_day,
            poi_pool=poi_pool,
            must_visit_ids=must_visit_ids,
        )
        fallback["thinking_tokens_used"] = thinking_tokens
        fallback["fallback_reason"] = "json_parse_error"
        return fallback

    # 校验 must_visit 覆盖情况
    daily_activities = parsed.get("daily_activities", [])
    assigned_ids = _collect_assigned_entity_ids(daily_activities)
    unassigned = [eid for eid in must_visit_ids if eid not in assigned_ids]

    if unassigned:
        logger.warning(f"[Step05] {len(unassigned)} 个 must_visit 未被分配: {unassigned}")

    return {
        "daily_activities": daily_activities,
        "unassigned_must_visit": unassigned,
        "thinking_tokens_used": thinking_tokens,
    }


# ── Prompt 构建 ──────────────────────────────────────────────────────────────


def _build_user_prompt(
    cities_by_day: list[dict],
    poi_pool: list[CandidatePool],
    must_visit_ids: set[str],
    user_profile: dict,
) -> str:
    """构建发送给 Opus 的 user prompt，按 city 分组列出 POI 摘要。"""

    sections: list[str] = []

    # 1) 用户画像
    sections.append("## 用户画像")
    profile_fields = {
        "party_type": user_profile.get("party_type", "couple"),
        "budget_tier": user_profile.get("budget_tier", "mid"),
        "must_have_tags": user_profile.get("must_have_tags", []),
    }
    sections.append(json.dumps(profile_fields, ensure_ascii=False))

    # 2) 每日城市安排
    sections.append("\n## 每日城市安排 (cities_by_day)")
    sections.append(json.dumps(cities_by_day, ensure_ascii=False, indent=2))

    # 3) must_visit 列表
    if must_visit_ids:
        sections.append("\n## 必去景点 (must_visit)")
        # 将 must_visit 的 entity_id 匹配到名称
        pool_map = {p.entity_id: p for p in poi_pool}
        must_items = []
        for mid in must_visit_ids:
            p = pool_map.get(mid)
            if p:
                must_items.append(f"- {mid}: {p.name_zh}")
            else:
                must_items.append(f"- {mid}: (不在候选池中)")
        sections.append("\n".join(must_items))

    # 4) POI 候选池（按 city 分组，只列关键字段）
    sections.append("\n## POI 候选池（按城市分组）")
    pois_by_city = _group_pois_by_city(poi_pool, cities_by_day)
    for city, pois in pois_by_city.items():
        sections.append(f"\n### {city} ({len(pois)} POI)")
        for p in pois:
            # 每个 POI 只列关键字段以节省 token
            tags_short = p.tags[:5] if p.tags else []
            is_must = " [MUST]" if p.entity_id in must_visit_ids else ""
            sections.append(
                f"- {p.entity_id} | {p.name_zh} | {p.grade} | "
                f"tags={tags_short} | {p.visit_minutes}min{is_must}"
            )

    # 5) 输出格式说明
    sections.append("\n## 输出格式")
    sections.append(
        '返回一个 JSON 对象，结构为 {"daily_activities": [...]}。\n'
        "每天的结构:\n"
        "{\n"
        '  "day": 1,\n'
        '  "city": "osaka",\n'
        '  "theme": "到达+美食探索",\n'
        '  "main_activities": [\n'
        '    {"entity_id": "xxx", "name": "道顿堀", "visit_minutes": 90, '
        '"why": "关西第一站的经典体验"}\n'
        "  ],\n"
        '  "time_anchors": [],\n'
        '  "main_corridor": "namba_dotonbori",\n'
        '  "secondary_corridors": ["shinsaibashi"],\n'
        '  "intensity": "light"\n'
        "}\n"
        "intensity 取值: light / moderate / heavy\n"
        "time_anchors 示例: "
        '{"entity_id": "xxx", "fixed_time": "10:00", "reason": "开门时排队最短"}'
    )

    return "\n".join(sections)


def _group_pois_by_city(
    poi_pool: list[CandidatePool],
    cities_by_day: list[dict],
) -> dict[str, list[CandidatePool]]:
    """将 POI 按 city 分组。

    CandidatePool 本身没有 city_code 字段，所以通过 tags 中的城市名
    或 cities_by_day 中涉及的城市列表进行匹配。
    如果无法判断城市归属，归入 "unknown" 组。
    """
    # 收集所有涉及的城市
    all_cities = set()
    for day_info in cities_by_day:
        city = day_info.get("city", "")
        if city:
            all_cities.add(city.lower())

    grouped: dict[str, list[CandidatePool]] = defaultdict(list)

    for poi in poi_pool:
        # 尝试从 tags 中识别 city
        matched_city = None
        poi_tags_lower = {t.lower() for t in poi.tags} if poi.tags else set()
        for city in all_cities:
            if city in poi_tags_lower:
                matched_city = city
                break

        if matched_city:
            grouped[matched_city].append(poi)
        else:
            # 无法确定城市时归入 unknown
            grouped["unknown"].append(poi)

    return dict(grouped)


# ── Opus API 调用 ────────────────────────────────────────────────────────────


async def _call_opus(
    user_prompt: str,
    circle: CircleProfile,
    api_key: str | None = None,
) -> tuple[str, int]:
    """调用 Anthropic Opus，返回 (文本内容, thinking_tokens_used)。"""

    client = anthropic.AsyncAnthropic(
        api_key=api_key or settings.anthropic_api_key,
    )

    response = await client.messages.create(
        model=_OPUS_MODEL,
        max_tokens=_MAX_TOKENS,
        thinking={
            "type": "enabled",
            "budget_tokens": _THINKING_BUDGET,
        },
        system=_build_system_prompt(circle),
        messages=[{"role": "user", "content": user_prompt}],
    )

    # 提取文本内容
    text_content = ""

    for block in response.content:
        if block.type == "text":
            text_content += block.text

    # Extended thinking tokens 计入 output_tokens（Anthropic 官方计费方式）。
    # SDK 无独立 thinking_tokens 字段，output_tokens 包含 thinking + visible output。
    output_tokens = 0
    if hasattr(response, "usage") and response.usage:
        output_tokens = getattr(response.usage, "output_tokens", 0)
        logger.info(
            "[Step05] Opus 调用完成: input=%d, output=%d (includes thinking)",
            getattr(response.usage, "input_tokens", 0),
            output_tokens,
        )

    return text_content, output_tokens


# ── 响应解析 ─────────────────────────────────────────────────────────────────


def _parse_opus_response(raw_text: str) -> dict | None:
    """从 Opus 返回的文本中解析 JSON 对象。

    处理以下情况：
    - 纯 JSON 文本
    - 被 ```json ... ``` 包裹的 JSON
    - 前后有额外文字的 JSON
    """
    if not raw_text or not raw_text.strip():
        return None

    text = raw_text.strip()

    # 尝试 1：直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试 2：提取 ```json ... ``` 块
    md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if md_match:
        try:
            return json.loads(md_match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试 3：找到第一个 { 和最后一个 } 之间的内容
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    logger.error(f"[Step05] 无法解析 Opus 返回: {text[:200]}...")
    return None


def _collect_assigned_entity_ids(daily_activities: list[dict]) -> set[str]:
    """从 daily_activities 中收集所有已分配的 entity_id。"""
    assigned: set[str] = set()
    for day in daily_activities:
        for act in day.get("main_activities", []):
            eid = act.get("entity_id")
            if eid:
                assigned.add(eid)
        for anchor in day.get("time_anchors", []):
            eid = anchor.get("entity_id")
            if eid:
                assigned.add(eid)
    return assigned


# ── 规则引擎 Fallback ────────────────────────────────────────────────────────


def _rule_based_fallback(
    cities_by_day: list[dict],
    poi_pool: list[CandidatePool],
    must_visit_ids: set[str],
) -> dict[str, Any]:
    """
    当 Opus 调用失败时的规则引擎降级方案。

    策略：
    1. 先将 must_visit 分配到对应城市的天数
    2. 对每天按 grade 降序选 top-1 POI 作为主活动
    3. 到达日/离开日标记 intensity=light，其余 moderate
    """

    logger.info("[Step05] 使用规则引擎 fallback 分配每日活动")

    total_days = len(cities_by_day)

    # POI 按 entity_id 建索引
    pool_map: dict[str, CandidatePool] = {p.entity_id: p for p in poi_pool}

    # POI 按 city 分组（使用 city_code 字段，比 tag 匹配可靠）
    all_cities = set()
    for day_info in cities_by_day:
        city = day_info.get("city", "")
        if city:
            all_cities.add(city.lower())

    city_pois: dict[str, list[CandidatePool]] = defaultdict(list)
    for poi in poi_pool:
        poi_city = (poi.city_code or "").lower()
        if poi_city and poi_city in all_cities:
            city_pois[poi_city].append(poi)
        else:
            # city_code 不匹配时，尝试 tag 兜底（向后兼容旧数据）
            poi_tags_lower = {t.lower() for t in poi.tags} if poi.tags else set()
            matched = False
            for city in all_cities:
                if city in poi_tags_lower:
                    city_pois[city].append(poi)
                    matched = True
                    break
            if not matched and poi_city:
                # 有 city_code 但不在本次旅行城市列表中，跳过
                logger.debug(
                    "[Step05 Fallback] POI %s city_code=%s 不在旅行城市列表中",
                    poi.name_zh,
                    poi_city,
                )

    # 按 grade 排序
    for city in city_pois:
        city_pois[city].sort(key=lambda p: _GRADE_ORDER.get(p.grade, 99))

    # 分配
    daily_activities: list[dict] = []
    assigned_ids: set[str] = set()

    # 第一轮：分配 must_visit
    must_visit_pois = [pool_map[mid] for mid in must_visit_ids if mid in pool_map]

    for day_idx, day_info in enumerate(cities_by_day):
        day_num = day_info.get("day", day_idx + 1)
        city = day_info.get("city", "unknown").lower()
        is_first_day = day_idx == 0
        is_last_day = day_idx == total_days - 1
        intensity = "light" if (is_first_day or is_last_day) else "moderate"
        max_activities = 1 if intensity == "light" else 2

        day_result: dict[str, Any] = {
            "day": day_num,
            "city": city,
            "theme": day_info.get("theme", ""),
            "main_activities": [],
            "time_anchors": [],
            "main_corridor": "",
            "secondary_corridors": [],
            "intensity": intensity,
        }

        # 优先分配该城市的 must_visit
        for mv_poi in must_visit_pois:
            if mv_poi.entity_id in assigned_ids:
                continue
            # 检查 POI 是否属于该城市（优先 city_code，兜底 tags）
            mv_city = (mv_poi.city_code or "").lower()
            poi_tags_lower = {t.lower() for t in mv_poi.tags} if mv_poi.tags else set()
            if mv_city == city or city in poi_tags_lower or city == "unknown":
                day_result["main_activities"].append(
                    {
                        "entity_id": mv_poi.entity_id,
                        "name": mv_poi.name_zh,
                        "visit_minutes": mv_poi.visit_minutes,
                        "why": "用户指定必去",
                    }
                )
                assigned_ids.add(mv_poi.entity_id)
                if len(day_result["main_activities"]) >= max_activities:
                    break

        # 补充：如果还有空位，按 grade 降序选一个
        if len(day_result["main_activities"]) < max_activities:
            candidates = city_pois.get(city, [])
            for cand in candidates:
                if cand.entity_id not in assigned_ids:
                    day_result["main_activities"].append(
                        {
                            "entity_id": cand.entity_id,
                            "name": cand.name_zh,
                            "visit_minutes": cand.visit_minutes,
                            "why": f"grade={cand.grade} 该城市评分最高",
                        }
                    )
                    assigned_ids.add(cand.entity_id)
                    break

        # 设置 main_corridor（从选中活动的 tags 中提取走廊标签）
        if day_result["main_activities"]:
            corridor_candidates: list[str] = []
            for act in day_result["main_activities"]:
                act_poi = pool_map.get(act["entity_id"])
                if act_poi and act_poi.tags:
                    # 走廊标签通常包含地区名（如 "arashiyama", "gion", "namba"）
                    # 排除通用标签，提取地理走廊
                    for tag in act_poi.tags:
                        tag_l = tag.lower()
                        # 跳过非走廊类的通用标签
                        if tag_l in (
                            "outdoor",
                            "indoor",
                            "cultural",
                            "nature",
                            "seasonal",
                            "photo",
                            "couple",
                            "family",
                            "budget",
                            "premium",
                            "luxury",
                            "free",
                        ):
                            continue
                        # 跳过城市名本身（走廊应是城市内的细分区域）
                        if tag_l == city:
                            continue
                        corridor_candidates.append(tag_l)

            if corridor_candidates:
                # 用出现频率最高的 tag 作为 main_corridor
                from collections import Counter

                most_common = Counter(corridor_candidates).most_common(1)
                day_result["main_corridor"] = most_common[0][0]
                # 其余高频 tag 作为 secondary_corridors
                if len(corridor_candidates) > 1:
                    other_corridors = [
                        t
                        for t, _ in Counter(corridor_candidates).most_common(4)
                        if t != day_result["main_corridor"]
                    ]
                    day_result["secondary_corridors"] = other_corridors[:3]

        daily_activities.append(day_result)

    # 检查未分配的 must_visit
    unassigned = [eid for eid in must_visit_ids if eid not in assigned_ids]
    if unassigned:
        logger.warning(f"[Step05 Fallback] {len(unassigned)} 个 must_visit 未能分配: {unassigned}")

    return {
        "daily_activities": daily_activities,
        "unassigned_must_visit": unassigned,
    }

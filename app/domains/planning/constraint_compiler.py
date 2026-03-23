"""
constraint_compiler.py — 约束编译器

职责：
  把 TripProfile 中零散的字段一次编译成 PlanningConstraints 对象，
  下游模块（ranker / skeleton / filler）统一消费，不再各自解读 profile。

约束分两层：
  硬约束（MUST / BLOCK）— 不满足就 reject / skip
  软偏好（BOOST / PENALTY）— 影响排序权重

每条约束通过 ConstraintTraceItem 结构化追踪：
  编译来源 → 消费模块 → 消费动作 → 最终状态
"""
from __future__ import annotations

import logging
import uuid as _uuid
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── 版本号 ────────────────────────────────────────────────────────────────────
COMPILER_VERSION = "2.1.0"


# ── 结构化 Trace ──────────────────────────────────────────────────────────────

@dataclass
class ConstraintTraceItem:
    """一条约束的结构化追踪记录。"""
    constraint_name: str                              # e.g. "avoid_cuisines"
    source_inputs: str                                # e.g. "profile.avoid_tags=['sushi','raw']"
    compiled_value: str                               # e.g. "{'sushi','sashimi','raw'}"
    strength: str = "hard"                            # "hard" | "soft"
    intended_consumers: list[str] = field(default_factory=list)  # ["filler"]
    consumption_events: list[dict] = field(default_factory=list) # [{module, action, effect_summary, reason}]
    final_status: str = "pending"                     # "fully_consumed" | "partially_consumed" | "unconsumed" | "pending"
    ignored_reason: str = ""


# ── 约束对象 ──────────────────────────────────────────────────────────────────

@dataclass
class PlanningConstraints:
    """编译后的行程约束，所有下游模块共享。"""

    # ── 硬约束 ──────────────────────────────────────────────────────────────

    # blocked_tags: 用户拒绝的活动标签
    #   ranker 中命中即降权到 0
    blocked_tags: set[str] = field(default_factory=set)

    # blocked_clusters: 明确禁止的 cluster_id 集合
    #   skeleton 中命中即不分配
    blocked_clusters: set[str] = field(default_factory=set)

    # avoid_cuisines: 餐饮禁忌
    #   filler 中命中即 skip
    avoid_cuisines: set[str] = field(default_factory=set)

    # max_intensity: 全局最大节奏等级
    #   "light" → 0, "balanced" → 1, "dense" → 2
    max_intensity: int = 2

    # must_stay_cities: 用户要求住宿覆盖的城市 code 集合
    must_stay_cities: set[str] = field(default_factory=set)

    # must_stay_area: 用户偏好的住宿区域 (e.g. "kyoto_station")
    #   hotel_base_builder 优先匹配
    must_stay_area: str = ""

    # city_strict_day_types: 哪些 day_type 强制城市一致性（filler 用）
    city_strict_day_types: set[str] = field(default_factory=lambda: {
        "theme_park", "arrival", "departure",
    })

    # party_block_tags: 由 party_type 推导出的禁止标签
    party_block_tags: set[str] = field(default_factory=set)

    # departure_day_no_poi: 返程日是否禁止 POI
    departure_day_no_poi: bool = True

    # departure_meal_window: 返程日允许的餐次
    #   "none" → 不排任何餐；"breakfast_only" → 仅早餐；"breakfast_lunch" → 早+午
    departure_meal_window: str = "breakfast_only"

    # arrival_evening_only: 到达日是否为晚到（只有晚餐时间）
    arrival_evening_only: bool = False

    # ── 软偏好 ──────────────────────────────────────────────────────────────

    # preferred_tags_boost: tag → 加分值（ranker context_fit 叠加）
    #   must_have_tags 也放在这里（权重 10），不升级成硬约束
    preferred_tags_boost: dict[str, float] = field(default_factory=dict)

    # party_fit_penalty: 不适配 party_type 的 cluster 扣分值
    party_fit_penalty: float = 0.0

    # max_majors_per_day: 每天最多主要活动数
    max_majors_per_day: int = 1

    # ── 追踪 ────────────────────────────────────────────────────────────────
    constraint_trace: list[ConstraintTraceItem] = field(default_factory=list)

    # ── 版本 ────────────────────────────────────────────────────────────────
    compiler_version: str = COMPILER_VERSION
    run_id: str = field(default_factory=lambda: str(_uuid.uuid4())[:8])

    def trace_summary(self) -> list[str]:
        """返回人可读的 trace 摘要行列表。"""
        lines = []
        for t in self.constraint_trace:
            status = t.final_status
            consumers = ",".join(t.intended_consumers) if t.intended_consumers else "?"
            lines.append(
                f"[{t.strength}] {t.constraint_name}: "
                f"{t.source_inputs} → {t.compiled_value} "
                f"| consumers={consumers} | status={status}"
                + (f" | ignored: {t.ignored_reason}" if t.ignored_reason else "")
            )
        return lines

    def record_consumption(self, constraint_name: str, module: str,
                           action: str, effect_summary: str, reason: str = ""):
        """下游模块调用此方法记录约束消费事件。"""
        for t in self.constraint_trace:
            if t.constraint_name == constraint_name:
                t.consumption_events.append({
                    "module": module, "action": action,
                    "effect_summary": effect_summary, "reason": reason,
                })
                if t.final_status == "pending":
                    t.final_status = "partially_consumed"
                return
        # 找不到则新增一条 trace
        self.constraint_trace.append(ConstraintTraceItem(
            constraint_name=constraint_name,
            source_inputs="(runtime)",
            compiled_value="(runtime)",
            intended_consumers=[module],
            consumption_events=[{
                "module": module, "action": action,
                "effect_summary": effect_summary, "reason": reason,
            }],
            final_status="partially_consumed",
        ))


# ── 节奏映射 ──────────────────────────────────────────────────────────────────

_PACE_TO_MAX_INTENSITY: dict[str, int] = {
    "relaxed": 0,
    "moderate": 1,
    "packed": 2,
    "dense": 2,
}

_INTENSITY_LEVEL: dict[str, int] = {
    "light": 0, "relaxed": 0,
    "balanced": 1, "moderate": 1,
    "dense": 2,
}

# party_type → 自动推导的 block/penalty 规则
_PARTY_RULES: dict[str, dict] = {
    "family_multi_gen": {
        "block_unless_must_go": {"theme_park"},
        "penalty": 15.0,
        "max_intensity_override": 1,
    },
    "senior": {
        "block_unless_must_go": {"theme_park"},
        "penalty": 15.0,
        "max_intensity_override": 0,
    },
    "family_child": {
        "block_unless_must_go": set(),
        "penalty": 5.0,
        "max_intensity_override": None,
    },
}


# ── 编译入口 ──────────────────────────────────────────────────────────────────

def compile_constraints(profile) -> PlanningConstraints:
    """
    编译 TripProfile → PlanningConstraints。
    must_have_tags 只进 preferred_tags_boost（软偏好），不升级成 must_go 硬约束。
    """
    c = PlanningConstraints()
    trace = c.constraint_trace

    must_tags = set(t.lower() for t in (getattr(profile, "must_have_tags", None) or []))

    # ── 1. blocked_tags (avoid_tags → 活动标签层面) ───────────────────────
    avoid_tags = set(t.lower() for t in (getattr(profile, "avoid_tags", None) or []))
    c.blocked_tags = avoid_tags
    if avoid_tags:
        trace.append(ConstraintTraceItem(
            constraint_name="blocked_tags",
            source_inputs=f"profile.avoid_tags={sorted(avoid_tags)}",
            compiled_value=str(sorted(avoid_tags)),
            strength="hard",
            intended_consumers=["ranker", "skeleton"],
        ))

    # ── 2. blocked_clusters（从 profile.blocked_pois 或 blocked_clusters）──
    blocked_clusters = set(getattr(profile, "blocked_clusters", None) or [])
    blocked_pois = set(getattr(profile, "blocked_pois", None) or [])
    c.blocked_clusters = blocked_clusters | blocked_pois
    if c.blocked_clusters:
        trace.append(ConstraintTraceItem(
            constraint_name="blocked_clusters",
            source_inputs=f"profile.blocked_clusters={sorted(blocked_clusters)}, blocked_pois={sorted(blocked_pois)}",
            compiled_value=str(sorted(c.blocked_clusters)),
            strength="hard",
            intended_consumers=["ranker", "skeleton"],
        ))

    # ── 3. avoid_cuisines ────────────────────────────────────────────────
    _CUISINE_TAGS = {
        "sushi", "sashimi", "raw", "yakiniku", "ramen",
        "tempura", "kushikatsu", "yakitori", "takoyaki",
        "okonomiyaki", "kaiseki", "udon", "tonkatsu",
    }
    cuisine_avoids = avoid_tags & _CUISINE_TAGS
    if "raw" in avoid_tags:
        cuisine_avoids |= {"sashimi", "sushi"}
    c.avoid_cuisines = cuisine_avoids
    if cuisine_avoids:
        trace.append(ConstraintTraceItem(
            constraint_name="avoid_cuisines",
            source_inputs=f"profile.avoid_tags={sorted(avoid_tags)}",
            compiled_value=str(sorted(cuisine_avoids)),
            strength="hard",
            intended_consumers=["filler"],
        ))

    # ── 4. pace → max_intensity ──────────────────────────────────────────
    pace = (getattr(profile, "pace", None) or "moderate").lower()
    c.max_intensity = _PACE_TO_MAX_INTENSITY.get(pace, 1)
    trace.append(ConstraintTraceItem(
        constraint_name="max_intensity",
        source_inputs=f"profile.pace='{pace}'",
        compiled_value=str(c.max_intensity),
        strength="hard",
        intended_consumers=["skeleton"],
    ))

    # ── 5. must_stay_cities + must_stay_area ─────────────────────────────
    cities = getattr(profile, "cities", None) or []
    stay_cities = set()
    for city_spec in cities:
        if isinstance(city_spec, dict):
            cc = city_spec.get("city_code", "")
            if cc:
                stay_cities.add(cc.lower())
        elif isinstance(city_spec, str):
            stay_cities.add(city_spec.lower())
    c.must_stay_cities = stay_cities

    must_stay_area = (getattr(profile, "must_stay_area", None) or "").lower()
    c.must_stay_area = must_stay_area

    if stay_cities or must_stay_area:
        trace.append(ConstraintTraceItem(
            constraint_name="must_stay_area",
            source_inputs=f"profile.cities={[cs if isinstance(cs,str) else cs.get('city_code','') for cs in cities]}, must_stay_area='{must_stay_area}'",
            compiled_value=f"cities={sorted(stay_cities)}, area='{must_stay_area}'",
            strength="hard",
            intended_consumers=["skeleton", "hotel_base_builder"],
        ))

    # ── 6. party_type → party_block_tags + penalty + intensity override ──
    party = (getattr(profile, "party_type", None) or "").lower()
    rules = _PARTY_RULES.get(party)
    if rules:
        raw_blocks = rules.get("block_unless_must_go", set())
        effective_blocks = raw_blocks - must_tags
        if effective_blocks:
            c.party_block_tags = effective_blocks
            trace.append(ConstraintTraceItem(
                constraint_name="party_block_tags",
                source_inputs=f"party_type='{party}', must_have_tags={sorted(must_tags)}",
                compiled_value=f"blocked={sorted(effective_blocks)} (exempted={sorted(raw_blocks & must_tags)})",
                strength="hard",
                intended_consumers=["ranker"],
            ))

        c.party_fit_penalty = rules.get("penalty", 0.0)
        if c.party_fit_penalty:
            trace.append(ConstraintTraceItem(
                constraint_name="party_fit_penalty",
                source_inputs=f"party_type='{party}'",
                compiled_value=str(c.party_fit_penalty),
                strength="soft",
                intended_consumers=["ranker"],
            ))

        intensity_override = rules.get("max_intensity_override")
        if intensity_override is not None and intensity_override < c.max_intensity:
            old = c.max_intensity
            c.max_intensity = intensity_override
            trace.append(ConstraintTraceItem(
                constraint_name="max_intensity_party_override",
                source_inputs=f"party_type='{party}'",
                compiled_value=f"{old} → {intensity_override}",
                strength="hard",
                intended_consumers=["skeleton"],
            ))
    else:
        trace.append(ConstraintTraceItem(
            constraint_name="party_rules",
            source_inputs=f"party_type='{party}'",
            compiled_value="no rules",
            strength="soft",
            intended_consumers=[],
            final_status="unconsumed",
            ignored_reason=f"no party rules for '{party}'",
        ))

    # ── 7. preferred_tags_boost ──────────────────────────────────────────
    #   must_have_tags 只进 preferred_tags_boost（权重 10），不升级成硬约束
    #   nice_to_have_tags 进 preferred_tags_boost（权重 5）
    nice_tags = set(t.lower() for t in (getattr(profile, "nice_to_have_tags", None) or []))
    for t in nice_tags:
        c.preferred_tags_boost[t] = 5.0
    for t in must_tags:
        c.preferred_tags_boost[t] = max(c.preferred_tags_boost.get(t, 0), 10.0)

    if c.preferred_tags_boost:
        trace.append(ConstraintTraceItem(
            constraint_name="preferred_tags_boost",
            source_inputs=f"must_have_tags={sorted(must_tags)}, nice_to_have={sorted(nice_tags)}",
            compiled_value=str({k: v for k, v in sorted(c.preferred_tags_boost.items())}),
            strength="soft",
            intended_consumers=["ranker"],
        ))

    # ── 8. departure constraints ─────────────────────────────────────────
    dep_shape = (getattr(profile, "departure_day_shape", None) or "").lower()
    if dep_shape == "full_day":
        c.departure_day_no_poi = False
        c.departure_meal_window = "breakfast_lunch"
    elif dep_shape == "airport_only":
        c.departure_day_no_poi = True
        c.departure_meal_window = "none"
    else:
        # 默认: 不排 POI，只保留早餐
        c.departure_day_no_poi = True
        c.departure_meal_window = "breakfast_only"
    trace.append(ConstraintTraceItem(
        constraint_name="departure_constraints",
        source_inputs=f"departure_day_shape='{dep_shape}'",
        compiled_value=f"no_poi={c.departure_day_no_poi}, meals='{c.departure_meal_window}'",
        strength="hard",
        intended_consumers=["skeleton", "filler"],
    ))

    # ── 9. arrival constraints ───────────────────────────────────────────
    arrival_time = getattr(profile, "arrival_time", None) or ""
    arrival_shape = (getattr(profile, "arrival_shape", None) or "").lower()
    # 如果到达时间在 17:00 之后，或 arrival_shape 标记为 evening_only
    if arrival_time:
        try:
            hour = int(arrival_time.split(":")[0])
            if hour >= 17:
                c.arrival_evening_only = True
        except (ValueError, IndexError):
            pass
    if arrival_shape == "evening_only":
        c.arrival_evening_only = True

    trace.append(ConstraintTraceItem(
        constraint_name="arrival_constraints",
        source_inputs=f"arrival_time='{arrival_time}', arrival_shape='{arrival_shape}'",
        compiled_value=f"evening_only={c.arrival_evening_only}",
        strength="hard",
        intended_consumers=["skeleton", "filler"],
    ))

    # ── 日志输出 ─────────────────────────────────────────────────────────
    logger.info(
        "constraint_compiler v%s [%s]: %d constraints, %d trace items",
        COMPILER_VERSION, c.run_id, _count_active(c), len(trace),
    )
    for line in c.trace_summary():
        logger.debug("  %s", line)

    return c


def _count_active(c: PlanningConstraints) -> int:
    """统计有多少约束被激活。"""
    count = 0
    if c.blocked_tags: count += 1
    if c.blocked_clusters: count += 1
    if c.avoid_cuisines: count += 1
    if c.max_intensity < 2: count += 1
    if c.must_stay_cities: count += 1
    if c.must_stay_area: count += 1
    if c.party_block_tags: count += 1
    if c.party_fit_penalty > 0: count += 1
    if c.preferred_tags_boost: count += 1
    if c.departure_day_no_poi: count += 1
    if c.arrival_evening_only: count += 1
    return count


# ── 便捷查询方法 ──────────────────────────────────────────────────────────────

def intensity_name_to_level(name: str) -> int:
    """intensity 名称 → 数值等级。"""
    return _INTENSITY_LEVEL.get(name.lower(), 1)


def is_intensity_allowed(intensity_name: str, constraints: PlanningConstraints) -> bool:
    """判断给定的 intensity 是否在约束允许范围内。"""
    return intensity_name_to_level(intensity_name) <= constraints.max_intensity


def max_allowed_intensity_name(constraints: PlanningConstraints) -> str:
    """返回约束允许的最高 intensity 名称。"""
    for name, level in [("dense", 2), ("balanced", 1), ("light", 0)]:
        if level <= constraints.max_intensity:
            return name
    return "light"

"""
micro_route_builder.py — 半日微路线候选生成器

将"排点"升级为"排半日微路线"：
  - 输入: 已排名的活动簇、约束、当天属性
  - 输出: 5~20 条合法 micro-routes（半日或日内路线包）

每条 micro-route 包含:
  primary cluster + 1~3 secondary candidates + meal style/corridor
  + day_type compatibility + intensity score + vibe tags + blocked conflicts
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.planning.major_activity_ranker import RankedMajor
    from app.domains.planning.constraint_compiler import PlanningConstraints

logger = logging.getLogger(__name__)

# ── 走廊 → 推荐次要 cluster 映射（静态知识，从 seed 数据提取） ──────────────
# 同一走廊 / 相邻走廊的 cluster 自然组成半日路线

_CORRIDOR_CLUSTER_AFFINITY: dict[str, list[str]] = {
    "fushimi": [
        "kyo_fushimi_inari", "kyo_fushimi_sake_town",
        "kyo_fushimi_momoyama_history",
    ],
    "arashiyama": [
        "kyo_arashiyama_sagano", "kyo_upper_arashiyama_niche",
    ],
    "higashiyama": [
        "kyo_higashiyama_gion_classic", "kyo_kaiseki_gion_evening",
        "kyo_eikando_shinnyodo",
    ],
    "philosopher_path": [
        "kyo_philosopher_path_nanzen", "kyo_eikando_shinnyodo",
    ],
    "kinugasa": [
        "kyo_kinkakuji_kinugasa", "kyo_daitokuji_zen_complex",
    ],
    "gion": [
        "kyo_higashiyama_gion_classic", "kyo_kaiseki_gion_evening",
        "kyo_night_sakura_gion",
    ],
    "namba": [
        "osa_dotonbori_minami_food", "osa_shinsekai_tenno",
        "osa_ramen_street_food",
    ],
    "sakurajima": [
        "osa_usj_themepark",
    ],
    "osakajo": [
        "osa_osaka_castle_tenmabashi", "osa_nakanoshima_temma",
    ],
    "nara_park": [
        "kyo_nara_day_trip", "nara_deep_kasuga_kofuku",
        "nara_family_deer_park",
    ],
    "uji": [
        "kyo_uji_day_trip", "kyo_wisteria_byodoin",
    ],
    "zen_garden": [
        "kyo_zen_garden_circuit", "kyo_saihoji_moss_temple",
    ],
    "gosho": [
        "kyo_nijo_nishijin", "kyo_garden_imperial_circuit",
    ],
    "nishikyo": [
        "kyo_katsura_modern_arch",
    ],
    "kobe_kitano": [
        "kobe_kitano_nankinmachi", "arima_onsen_day_trip",
    ],
}

# 走廊 → 推荐餐饮风格
_CORRIDOR_MEAL_STYLE: dict[str, str] = {
    "fushimi": "route_meal",       # 参道小吃
    "arashiyama": "route_meal",    # 岚山荞麦面
    "higashiyama": "destination_meal",  # 祇园怀石
    "gion": "destination_meal",
    "namba": "route_meal",         # 道顿堀街头
    "sakurajima": "park_meal",     # USJ 园内
    "nara_park": "route_meal",
    "uji": "route_meal",          # 宇治抹茶
    "zen_garden": "quick",
    "kinugasa": "quick",
    "osakajo": "route_meal",
    "kobe_kitano": "destination_meal",
}

# cluster_id → vibe tags（从 profile_fit / must_have_tags 推断）
_CLUSTER_VIBE_TAGS: dict[str, set[str]] = {
    "kyo_fushimi_inari": {"culture", "photo", "first_timer"},
    "kyo_arashiyama_sagano": {"nature", "photo", "first_timer"},
    "kyo_higashiyama_gion_classic": {"culture", "history", "first_timer"},
    "kyo_philosopher_path_nanzen": {"culture", "garden", "zen"},
    "kyo_kinkakuji_kinugasa": {"culture", "history", "first_timer"},
    "kyo_zen_garden_circuit": {"zen", "garden", "culture"},
    "kyo_garden_imperial_circuit": {"garden", "culture", "niche"},
    "kyo_nara_day_trip": {"culture", "family", "first_timer"},
    "kyo_uji_day_trip": {"culture", "food", "niche"},
    "kyo_kaiseki_gion_evening": {"food", "culture", "luxury"},
    "kyo_nishiki_gourmet": {"food", "local"},
    "kyo_sakura_photo_circuit": {"photo", "sakura", "seasonal"},
    "kyo_night_sakura_gion": {"photo", "sakura", "nightlife"},
    "kyo_daitokuji_zen_complex": {"zen", "garden", "niche"},
    "kyo_saihoji_moss_temple": {"zen", "garden", "niche"},
    "kyo_katsura_modern_arch": {"architecture", "niche", "design"},
    "kyo_ando_architecture": {"architecture", "design", "niche"},
    "osa_usj_themepark": {"theme_park", "family", "couple"},
    "osa_dotonbori_minami_food": {"food", "nightlife", "first_timer"},
    "osa_shinsekai_tenno": {"food", "local", "culture"},
    "osa_osaka_castle_tenmabashi": {"history", "culture", "first_timer"},
    "osa_kaiyukan_tempozan": {"family", "kids", "aquarium"},
    "osa_ramen_street_food": {"food", "local"},
    "osa_nakanoshima_temma": {"architecture", "culture", "niche"},
    "nara_deep_kasuga_kofuku": {"culture", "history", "zen"},
    "nara_family_deer_park": {"family", "kids", "nature"},
    "kobe_kitano_nankinmachi": {"culture", "food", "niche"},
    "arima_onsen_day_trip": {"onsen", "relaxation", "senior"},
    "miho_museum_day_trip": {"architecture", "art", "niche"},
}

# day_type → intensity 默认值
_DAY_TYPE_INTENSITY: dict[str, float] = {
    "arrival": 0.5,
    "departure": 0.3,
    "theme_park": 1.8,
    "normal": 1.0,
}

# party_type → fit scores
_PARTY_FIT_DEFAULTS: dict[str, dict[str, float]] = {
    "couple": {"couple": 1.0, "family": 0.6, "senior": 0.5, "friends": 0.8, "solo": 0.7},
    "family": {"couple": 0.5, "family": 1.0, "senior": 0.7, "friends": 0.5, "solo": 0.4},
    "senior": {"couple": 0.4, "family": 0.6, "senior": 1.0, "friends": 0.4, "solo": 0.5},
    "friends": {"couple": 0.7, "family": 0.4, "senior": 0.3, "friends": 1.0, "solo": 0.8},
    "solo": {"couple": 0.6, "family": 0.3, "senior": 0.4, "friends": 0.7, "solo": 1.0},
}

# intensity name → numeric level
_INTENSITY_LEVEL = {"light": 0, "balanced": 1, "dense": 2}


@dataclass
class MicroRoute:
    """半日微路线候选"""
    route_id: str = ""
    corridor: str = ""
    primary_cluster_id: str = ""
    primary_name: str = ""
    secondary_candidates: list[str] = field(default_factory=list)
    meal_style: str = "route_meal"
    meal_corridor: str = ""
    day_type_compat: list[str] = field(default_factory=lambda: ["normal"])
    intensity_score: float = 1.0
    vibe_tags: set[str] = field(default_factory=set)
    blocked_conflicts: set[str] = field(default_factory=set)
    party_fit: dict[str, float] = field(default_factory=dict)
    quality_score: float = 0.0  # from RankedMajor.major_score


@dataclass
class MicroRoutePool:
    """单天的 micro-route 候选池"""
    day_index: int = 0
    corridor: str = ""
    routes: list[MicroRoute] = field(default_factory=list)
    selected_route: Optional[MicroRoute] = None
    trace: list[str] = field(default_factory=list)


def build_micro_route_candidates(
    all_ranked: list,
    constraints,
    day_type: str = "normal",
    corridor: str = "",
    party_type: str = "couple",
    intensity_cap: str = "dense",
    day_index: int = 0,
) -> MicroRoutePool:
    """
    为一天（或半天）生成 micro-route 候选。

    策略：
    1. 从 all_ranked 中筛选与 corridor 匹配或可用的 clusters
    2. 每个合格 cluster 生成一条 micro-route
    3. micro-route 的 secondary_candidates 从同走廊亲和 clusters 中填充
    4. 过滤掉被 blocked 的、超出 intensity_cap 的
    5. 按 quality_score + party_fit 排序
    """
    pool = MicroRoutePool(day_index=day_index, corridor=corridor)

    blocked_clusters = getattr(constraints, "blocked_clusters", set()) or set()
    blocked_tags = getattr(constraints, "blocked_tags", set()) or set()
    intensity_cap_level = _INTENSITY_LEVEL.get(intensity_cap, 2)

    # 当天 intensity 基线
    base_intensity = _DAY_TYPE_INTENSITY.get(day_type, 1.0)

    for ranked in all_ranked:
        cid = ranked.cluster_id
        name = ranked.name_zh
        pcorr = ranked.primary_corridor

        # 跳过 blocked
        if cid in blocked_clusters:
            continue
        if ranked.precheck_status in ("fail", "blocked"):
            continue

        # 跳过非本走廊（如果指定了走廊）
        # 宽松匹配：只在 corridor 有明确亲和组时才过滤
        if corridor and pcorr and pcorr != corridor:
            affinity = _CORRIDOR_CLUSTER_AFFINITY.get(corridor, [])
            if affinity and cid not in affinity:
                continue
            # 如果走廊无亲和组定义，不过滤（允许跨走廊候选）

        # 计算 vibe tags
        vibe = set(_CLUSTER_VIBE_TAGS.get(cid, set()))
        # 添加 cluster profile_fit 作为额外 vibe
        cluster_profile_fit = set()
        if hasattr(ranked, "explain") and hasattr(ranked.explain, "profile_fit_tags"):
            cluster_profile_fit = set(ranked.explain.profile_fit_tags or [])
        vibe |= cluster_profile_fit

        # blocked_conflicts: 此 route 的 vibe 与 blocked_tags 的交集
        conflicts = vibe & blocked_tags

        # intensity score
        dur = getattr(ranked, "default_duration", "full_day") or "full_day"
        if "full" in dur:
            intensity = base_intensity * 1.5
        elif "half" in dur:
            intensity = base_intensity * 0.8
        else:
            intensity = base_intensity * 0.5

        # intensity cap 过滤
        if intensity > (intensity_cap_level + 1) * 1.0:
            continue

        # day_type 兼容
        compat = ["normal"]
        if "half" in dur or "quarter" in dur:
            compat.extend(["arrival", "departure"])
        if any(t in vibe for t in {"theme_park"}):
            compat = ["theme_park", "normal"]

        if day_type not in compat and day_type != "normal":
            # 宽松匹配：normal 总是兼容
            if day_type not in compat:
                continue

        # secondary candidates: 同走廊亲和 clusters（排除自己和 blocked）
        route_corridor = pcorr or corridor
        affinity_clusters = _CORRIDOR_CLUSTER_AFFINITY.get(route_corridor, [])
        secondaries = [
            sc for sc in affinity_clusters
            if sc != cid and sc not in blocked_clusters
        ][:3]

        # meal
        meal_style = _CORRIDOR_MEAL_STYLE.get(route_corridor, "route_meal")
        meal_corridor = route_corridor

        # party fit
        pfit = dict(_PARTY_FIT_DEFAULTS.get(party_type, {}))
        # 对 senior: 如果有 nightlife / theme_park tag → 降低 fit
        if "senior" in pfit:
            if "nightlife" in vibe:
                pfit["senior"] = max(0, pfit.get("senior", 0.5) - 0.3)
            if "theme_park" in vibe:
                pfit["senior"] = max(0, pfit.get("senior", 0.5) - 0.2)
        # 对 family: 如果有 kids / family tag → 提升
        if "family" in vibe:
            pfit["family"] = min(1.0, pfit.get("family", 0.5) + 0.2)

        route = MicroRoute(
            route_id=uuid.uuid4().hex[:8],
            corridor=route_corridor,
            primary_cluster_id=cid,
            primary_name=name,
            secondary_candidates=secondaries,
            meal_style=meal_style,
            meal_corridor=meal_corridor,
            day_type_compat=compat,
            intensity_score=intensity,
            vibe_tags=vibe,
            blocked_conflicts=conflicts,
            party_fit=pfit,
            quality_score=ranked.major_score,
        )
        pool.routes.append(route)

    # 排序：quality_score DESC → party_fit[party_type] DESC → conflicts ASC
    pool.routes.sort(key=lambda r: (
        -r.quality_score,
        -r.party_fit.get(party_type, 0.5),
        len(r.blocked_conflicts),
    ))

    # 裁剪到 20 条
    pool.routes = pool.routes[:20]

    pool.trace.append(
        f"day{day_index} [{day_type}] corridor={corridor}: "
        f"{len(pool.routes)} micro-routes built from {len(all_ranked)} ranked clusters"
    )

    return pool


def select_best_micro_route(
    pool: MicroRoutePool,
    day_mode: str = "",
    mode_boosted_tags: set[str] = frozenset(),
    mode_suppressed_tags: set[str] = frozenset(),
    already_used_clusters: set[str] = frozenset(),
) -> Optional[MicroRoute]:
    """
    从 pool 中选最佳 micro-route。

    选择逻辑:
    1. 过滤掉已使用的 primary_cluster_id
    2. day_mode boosted_tags 加分
    3. day_mode suppressed_tags 减分
    4. 取第一个（已排序的最高分）
    """
    candidates = []
    for r in pool.routes:
        if r.primary_cluster_id in already_used_clusters:
            continue
        # 只在冲突数 >= 2 时跳过（1 个标签重叠可能是误伤）
        if len(r.blocked_conflicts) >= 2:
            continue

        # day_mode gating score
        mode_score = 0.0
        if mode_boosted_tags:
            overlap = r.vibe_tags & mode_boosted_tags
            mode_score += len(overlap) * 5.0
        if mode_suppressed_tags:
            suppress_overlap = r.vibe_tags & mode_suppressed_tags
            mode_score -= len(suppress_overlap) * 10.0

        candidates.append((r.quality_score + mode_score, r))

    if not candidates:
        return None

    candidates.sort(key=lambda x: -x[0])
    best = candidates[0][1]
    pool.selected_route = best
    pool.trace.append(
        f"selected micro-route: {best.primary_name} "
        f"(corridor={best.corridor}, score={candidates[0][0]:.1f}, "
        f"vibe={sorted(best.vibe_tags)[:5]})"
    )
    return best

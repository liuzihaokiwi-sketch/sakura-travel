"""
day_mode.py — 单日气质锁定（Vibe Lock）

在 skeleton 生成后，为每天推导一个 day_mode，锁定当天主气质。

day_mode 的作用：
  - 锁定当天主气质标签
  - 压低跳戏标签（防止"老人 + 二次元" / "建筑庭园 + 夜店美食街"）
  - 影响 secondary_filler / meal_flex_filler 的候选排序
  - 输出 trace: day_mode 如何推导、屏蔽了哪些 tag
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.planning.route_skeleton_builder import DayFrame
    from app.domains.planning.constraint_compiler import PlanningConstraints

logger = logging.getLogger(__name__)

# ── day_mode 定义 ─────────────────────────────────────────────────────────────
# 每个 mode 有 boosted_tags（加强）和 suppressed_tags（压低）

_MODE_DEFINITIONS: dict[str, dict] = {
    "arrival_light": {
        "boosted": {"photo", "local", "food"},
        "suppressed": {"nightlife", "theme_park", "hiking", "dense"},
        "description": "到达日轻松，简单打卡+在地美食",
    },
    "departure_light": {
        "boosted": {"food", "local", "shopping"},
        "suppressed": {"nightlife", "theme_park", "hiking", "culture", "dense"},
        "description": "返程日收尾，住宿周边轻量活动",
    },
    "theme_park_full": {
        "boosted": {"theme_park", "family", "couple"},
        "suppressed": {"culture", "zen", "garden", "architecture", "niche"},
        "description": "主题公园全天，晚餐回住宿周边",
    },
    "culture_deep": {
        "boosted": {"culture", "history", "temple", "zen"},
        "suppressed": {"nightlife", "theme_park", "food_street", "kids"},
        "description": "文化深度游，寺庙/神社/历史街区",
    },
    "garden_zen": {
        "boosted": {"garden", "zen", "nature", "relaxation"},
        "suppressed": {"nightlife", "food_street", "theme_park", "kids", "shopping"},
        "description": "庭园禅意，枯山水/苔寺/竹林",
    },
    "food_local": {
        "boosted": {"food", "local", "market"},
        "suppressed": {"zen", "architecture", "niche", "theme_park"},
        "description": "在地美食为主线，市场/食堂/名店",
    },
    "classic_first_trip": {
        "boosted": {"first_timer", "photo", "culture"},
        "suppressed": {"niche", "design", "architecture"},
        "description": "经典初访线路，必打卡景点",
    },
    "niche_design": {
        "boosted": {"niche", "design", "architecture", "art"},
        "suppressed": {"first_timer", "theme_park", "kids"},
        "description": "小众设计/建筑线路",
    },
    "sakura_photo": {
        "boosted": {"sakura", "photo", "nature", "seasonal"},
        "suppressed": {"nightlife", "food_street", "theme_park"},
        "description": "樱花摄影线路",
    },
    "family_relaxed": {
        "boosted": {"family", "kids", "nature", "aquarium"},
        "suppressed": {"nightlife", "zen", "niche", "luxury"},
        "description": "家庭亲子轻松游",
    },
    "city_walk": {
        "boosted": {"local", "shopping", "food", "culture"},
        "suppressed": {"theme_park", "hiking"},
        "description": "城市漫步，逛街+散策",
    },
    "onsen_relaxation": {
        "boosted": {"onsen", "relaxation", "nature", "senior"},
        "suppressed": {"nightlife", "theme_park", "hiking", "kids"},
        "description": "温泉休闲线路",
    },
}

# day_type → 强制 mode 映射
_FORCED_MODES: dict[str, str] = {
    "arrival": "arrival_light",
    "departure": "departure_light",
    "theme_park": "theme_park_full",
}

# cluster_id 关键词 → 推荐 mode
_DRIVER_MODE_HINTS: list[tuple[list[str], str]] = [
    (["zen", "garden", "moss", "daitoku"], "garden_zen"),
    (["sakura", "cherry", "foliage"], "sakura_photo"),
    (["food", "gourmet", "nishiki", "dotonbori", "ramen", "street_food"], "food_local"),
    (["architecture", "ando", "katsura", "modern", "museum"], "niche_design"),
    (["usj", "themepark", "theme_park", "disney"], "theme_park_full"),
    (["family", "kids", "deer", "aquarium", "kaiyukan"], "family_relaxed"),
    (["onsen", "arima"], "onsen_relaxation"),
    (["fushimi_inari", "kinkakuji", "arashiyama", "higashiyama", "nara_day"], "classic_first_trip"),
    (["philosopher", "nanzen", "eikando"], "culture_deep"),
    (["gion", "kaiseki"], "culture_deep"),
]


@dataclass
class DayModeResult:
    """单天 day_mode 推导结果"""
    day_index: int = 0
    mode: str = "city_walk"           # fallback default
    boosted_tags: set[str] = field(default_factory=set)
    suppressed_tags: set[str] = field(default_factory=set)
    reason: str = ""
    driver_cluster: str = ""          # 推导依据的 main_driver


def infer_day_mode(
    frame,
    constraints=None,
    profile_tags: set[str] = frozenset(),
    party_type: str = "couple",
) -> DayModeResult:
    """
    为单天推导 day_mode。

    优先级：
    1. day_type 强制映射（arrival → arrival_light, departure → departure_light, theme_park → theme_park_full）
    2. main_driver cluster_id 关键词匹配 → mode hint
    3. profile_tags（用户偏好标签）投票 → 票数最多的 mode
    4. party_type 修正（senior → 压低 nightlife; family → boost kids）
    5. fallback: city_walk
    """
    result = DayModeResult(
        day_index=frame.day_index if hasattr(frame, "day_index") else 0,
        driver_cluster=frame.main_driver if hasattr(frame, "main_driver") else "",
    )

    day_type = frame.day_type if hasattr(frame, "day_type") else "normal"
    driver = (frame.main_driver or "").lower() if hasattr(frame, "main_driver") else ""
    driver_name = (frame.main_driver_name or "").lower() if hasattr(frame, "main_driver_name") else ""

    # ── 1. 强制映射 ──
    if day_type in _FORCED_MODES:
        mode = _FORCED_MODES[day_type]
        result.mode = mode
        result.reason = f"day_type={day_type} → forced mode"
        defn = _MODE_DEFINITIONS.get(mode, {})
        result.boosted_tags = set(defn.get("boosted", set()))
        result.suppressed_tags = set(defn.get("suppressed", set()))
        return result

    # ── 2. driver 关键词匹配 ──
    matched_mode = ""
    for keywords, mode in _DRIVER_MODE_HINTS:
        if any(kw in driver or kw in driver_name for kw in keywords):
            matched_mode = mode
            break

    # ── 3. profile_tags 投票 ──
    if not matched_mode and profile_tags:
        mode_scores: dict[str, float] = {}
        for mode_name, defn in _MODE_DEFINITIONS.items():
            if mode_name in _FORCED_MODES.values():
                continue  # 跳过强制 modes
            boosted = set(defn.get("boosted", set()))
            overlap = profile_tags & boosted
            if overlap:
                mode_scores[mode_name] = len(overlap)
        if mode_scores:
            matched_mode = max(mode_scores, key=mode_scores.get)

    # ── 4. party_type 修正 ──
    if not matched_mode:
        if party_type == "senior":
            matched_mode = "garden_zen"
        elif party_type == "family":
            matched_mode = "family_relaxed"
        else:
            matched_mode = "city_walk"

    # ── 5. 应用 mode ──
    result.mode = matched_mode
    defn = _MODE_DEFINITIONS.get(matched_mode, {})
    result.boosted_tags = set(defn.get("boosted", set()))
    result.suppressed_tags = set(defn.get("suppressed", set()))

    # party_type 额外压低
    if party_type == "senior":
        result.suppressed_tags |= {"nightlife", "theme_park", "hiking"}
    elif party_type == "family":
        result.suppressed_tags |= {"nightlife", "luxury", "niche"}

    # constraints blocked_tags 也加入 suppressed
    if constraints:
        blocked = getattr(constraints, "blocked_tags", set()) or set()
        result.suppressed_tags |= blocked

    result.reason = (
        f"driver={driver or 'none'}, "
        f"profile_tags={sorted(profile_tags)[:5]}, "
        f"party={party_type}"
    )

    return result


def apply_day_mode_gating(
    mode_result: DayModeResult,
    candidate_tags: set[str],
) -> tuple[float, set[str]]:
    """
    对候选项的标签做 day_mode gating。

    Returns:
        (boost_multiplier, actually_suppressed_tags)
        - boost_multiplier > 1.0 表示加分
        - boost_multiplier < 1.0 表示降权
        - actually_suppressed_tags: 被实际命中的 suppressed tags
    """
    boost = 1.0

    # boosted tags 交集 → 加分
    boosted_overlap = candidate_tags & mode_result.boosted_tags
    if boosted_overlap:
        boost += len(boosted_overlap) * 0.15  # 每命中一个 +15%

    # suppressed tags 交集 → 降权
    suppressed_overlap = candidate_tags & mode_result.suppressed_tags
    if suppressed_overlap:
        boost -= len(suppressed_overlap) * 0.25  # 每命中一个 -25%

    boost = max(0.1, boost)  # 下限 10%

    return boost, suppressed_overlap


def infer_all_day_modes(
    frames: list,
    constraints=None,
    profile_tags: set[str] = frozenset(),
    party_type: str = "couple",
) -> list[DayModeResult]:
    """为所有天推导 day_mode。"""
    results = []
    for frame in frames:
        result = infer_day_mode(frame, constraints, profile_tags, party_type)
        results.append(result)
    return results

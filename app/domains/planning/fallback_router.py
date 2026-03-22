"""
fallback_router.py — 分阶段降级兼容层

当城市圈数据不完整时，按阶段精确降级到旧路径，
而不是一刀切全部回落旧模板。

降级规则：
  F-01  无 circle data        → 整体回落旧模板路径
  F-02  有 circle, major < 阈值 → 回落 major selection，用旧模板天主题
  F-03  有 skeleton, meals 不足 → 只回落餐厅 filler
  F-04  有 vNext payload, renderer section 缺 → 用旧 section adapter
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class FallbackLevel(str, Enum):
    """降级级别，从最深（全部回落）到最浅（仅 section adapter）。"""
    FULL_LEGACY = "full_legacy"         # 整体走旧模板
    MAJOR_LEGACY = "major_legacy"       # 只有 major 选择回落
    FILLER_LEGACY = "filler_legacy"     # 只有次要/餐厅回落
    SECTION_ADAPTER = "section_adapter" # 只有渲染 section 回落
    NONE = "none"                       # 不降级，全新链路


@dataclass
class FallbackDecision:
    level: FallbackLevel = FallbackLevel.NONE
    reasons: list[str] = field(default_factory=list)
    legacy_template_code: Optional[str] = None  # F-01/F-02 时需要的旧模板

    @property
    def use_legacy_assembler(self) -> bool:
        return self.level == FallbackLevel.FULL_LEGACY

    @property
    def use_legacy_major_selection(self) -> bool:
        return self.level in (FallbackLevel.FULL_LEGACY, FallbackLevel.MAJOR_LEGACY)

    @property
    def use_legacy_filler(self) -> bool:
        return self.level in (
            FallbackLevel.FULL_LEGACY,
            FallbackLevel.MAJOR_LEGACY,
            FallbackLevel.FILLER_LEGACY,
        )

    @property
    def use_section_adapter(self) -> bool:
        return self.level == FallbackLevel.SECTION_ADAPTER


def evaluate_fallback(
    circle_found: bool,
    cluster_count: int,
    selected_major_count: int,
    min_major_threshold: int = 2,
    skeleton_built: bool = False,
    meal_coverage_ratio: float = 1.0,
    min_meal_coverage: float = 0.5,
    payload_version: Optional[str] = None,
) -> FallbackDecision:
    """
    评估当前数据完整性，决定降级级别。

    Args:
        circle_found: 是否找到匹配的城市圈
        cluster_count: 城市圈内活跃活动簇数
        selected_major_count: 已选中的主要活动数
        min_major_threshold: 最少需要的主要活动数
        skeleton_built: 骨架是否成功构建
        meal_coverage_ratio: 餐厅覆盖率（0-1）
        min_meal_coverage: 最低餐厅覆盖率
        payload_version: report payload 版本
    """
    decision = FallbackDecision()

    # F-01: 完全没有城市圈数据
    if not circle_found:
        decision.level = FallbackLevel.FULL_LEGACY
        decision.reasons.append("F-01: 无匹配城市圈数据")
        return decision

    # F-02: 城市圈有了，但活动簇不足 / major 选不够
    if cluster_count < min_major_threshold:
        decision.level = FallbackLevel.MAJOR_LEGACY
        decision.reasons.append(
            f"F-02: 活动簇数量 {cluster_count} < 阈值 {min_major_threshold}"
        )
        return decision

    if selected_major_count < min_major_threshold:
        decision.level = FallbackLevel.MAJOR_LEGACY
        decision.reasons.append(
            f"F-02: 选中主要活动 {selected_major_count} < 阈值 {min_major_threshold}"
        )
        return decision

    # F-03: 骨架有了，但餐厅覆盖不足
    if skeleton_built and meal_coverage_ratio < min_meal_coverage:
        decision.level = FallbackLevel.FILLER_LEGACY
        decision.reasons.append(
            f"F-03: 餐厅覆盖率 {meal_coverage_ratio:.1%} < {min_meal_coverage:.0%}"
        )
        return decision

    # F-04: payload 版本不是 vNext，需要 section adapter
    if payload_version and payload_version not in ("v2", "vNext"):
        decision.level = FallbackLevel.SECTION_ADAPTER
        decision.reasons.append(
            f"F-04: payload version {payload_version} 需要 section adapter"
        )
        return decision

    # 全部通过，不降级
    decision.level = FallbackLevel.NONE
    return decision


def resolve_legacy_template_code(
    city_codes: list[str],
    duration_days: int,
    theme: str = "",
) -> Optional[str]:
    """
    根据城市和天数，尝试匹配一个旧路线模板 code。

    这是 fallback 时用的——新链路有数据时不走这里。
    """
    # 简化匹配逻辑：基于现有 8 个模板
    city = city_codes[0] if city_codes else ""

    _TEMPLATE_MAP = {
        ("tokyo", 3): "tokyo_classic_3d",
        ("tokyo", 5): "tokyo_classic_5d",
        ("tokyo", 7): "tokyo_classic_7d",
        ("kyoto", 4): "kansai_classic_4d",
        ("kyoto", 6): "kansai_classic_6d",
        ("kyoto", 7): "kansai_classic_7d",
        ("osaka", 4): "kansai_classic_4d",
        ("osaka", 6): "kansai_classic_6d",
        ("osaka", 7): "kansai_classic_7d",
    }

    # 精确匹配
    key = (city, duration_days)
    if key in _TEMPLATE_MAP:
        return _TEMPLATE_MAP[key]

    # 近似匹配（差 1 天）
    for delta in (1, -1, 2, -2):
        near_key = (city, duration_days + delta)
        if near_key in _TEMPLATE_MAP:
            return _TEMPLATE_MAP[near_key]

    return None

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FallbackLevel(str, Enum):
    FULL_LEGACY = "full_legacy"
    MAJOR_LEGACY = "major_legacy"
    FILLER_LEGACY = "filler_legacy"
    SECTION_ADAPTER = "section_adapter"
    NONE = "none"


@dataclass
class FallbackDecision:
    level: FallbackLevel = FallbackLevel.NONE
    reasons: list[str] = field(default_factory=list)
    legacy_template_code: Optional[str] = None

    @property
    def use_legacy_assembler(self) -> bool:
        return False

    @property
    def use_legacy_major_selection(self) -> bool:
        return False

    @property
    def use_legacy_filler(self) -> bool:
        return False

    @property
    def use_section_adapter(self) -> bool:
        return False

    @property
    def requires_explicit_failure(self) -> bool:
        return self.level != FallbackLevel.NONE


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
    decision = FallbackDecision()

    if not circle_found:
        decision.level = FallbackLevel.FULL_LEGACY
        decision.reasons.append("F-01: no matched city-circle data")
        return decision

    if cluster_count < min_major_threshold:
        decision.level = FallbackLevel.MAJOR_LEGACY
        decision.reasons.append(f"F-02: cluster_count {cluster_count} < {min_major_threshold}")
        return decision

    if selected_major_count < min_major_threshold:
        decision.level = FallbackLevel.MAJOR_LEGACY
        decision.reasons.append(
            f"F-02: selected_major_count {selected_major_count} < {min_major_threshold}"
        )
        return decision

    if skeleton_built and meal_coverage_ratio < min_meal_coverage:
        decision.level = FallbackLevel.FILLER_LEGACY
        decision.reasons.append(
            f"F-03: meal_coverage_ratio {meal_coverage_ratio:.1%} < {min_meal_coverage:.0%}"
        )
        return decision

    if payload_version and payload_version not in ("v2", "vNext"):
        decision.level = FallbackLevel.SECTION_ADAPTER
        decision.reasons.append(f"F-04: payload version {payload_version} requires section adapter")
        return decision

    decision.level = FallbackLevel.NONE
    return decision


def resolve_legacy_template_code(
    city_codes: list[str],
    duration_days: int,
    theme: str = "",
) -> Optional[str]:
    del theme
    city = city_codes[0] if city_codes else ""
    template_map = {
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

    key = (city, duration_days)
    if key in template_map:
        return template_map[key]

    for delta in (1, -1, 2, -2):
        near_key = (city, duration_days + delta)
        if near_key in template_map:
            return template_map[near_key]

    return None


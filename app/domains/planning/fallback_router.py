from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FallbackLevel(str, Enum):
    NO_CIRCLE_DATA = "no_circle_data"
    INSUFFICIENT_CLUSTERS = "insufficient_clusters"
    INSUFFICIENT_MAJORS = "insufficient_majors"
    LOW_MEAL_COVERAGE = "low_meal_coverage"
    PAYLOAD_INCOMPATIBLE = "payload_incompatible"
    NONE = "none"


@dataclass
class FallbackDecision:
    level: FallbackLevel = FallbackLevel.NONE
    reasons: list[str] = field(default_factory=list)
    failure_code: Optional[str] = None

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
        decision.level = FallbackLevel.NO_CIRCLE_DATA
        decision.reasons.append("F-01: no matched city-circle data")
        return decision

    if cluster_count < min_major_threshold:
        decision.level = FallbackLevel.INSUFFICIENT_CLUSTERS
        decision.reasons.append(f"F-02: cluster_count {cluster_count} < {min_major_threshold}")
        return decision

    if selected_major_count < min_major_threshold:
        decision.level = FallbackLevel.INSUFFICIENT_MAJORS
        decision.reasons.append(
            f"F-02: selected_major_count {selected_major_count} < {min_major_threshold}"
        )
        return decision

    if skeleton_built and meal_coverage_ratio < min_meal_coverage:
        decision.level = FallbackLevel.LOW_MEAL_COVERAGE
        decision.reasons.append(
            f"F-03: meal_coverage_ratio {meal_coverage_ratio:.1%} < {min_meal_coverage:.0%}"
        )
        return decision

    if payload_version and payload_version not in ("v2", "vNext"):
        decision.level = FallbackLevel.PAYLOAD_INCOMPATIBLE
        decision.reasons.append(f"F-04: payload version {payload_version} requires section adapter")
        return decision

    decision.level = FallbackLevel.NONE
    return decision

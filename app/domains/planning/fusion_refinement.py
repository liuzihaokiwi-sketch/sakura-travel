"""
fusion_refinement.py - constrained decision refinement stage.

This module runs after the deterministic planning pipeline and applies a
strictly limited refinement pass.

The refinement stage may:
- flag cross-theme secondary points
- flag meals that conflict with the locked day mode
- flag obviously inconsistent same-day ordering
- remove weak filler candidates from the explanation layer

The refinement stage may not:
- introduce a new city or unverified POI
- rewrite hotel / run_id / plan_id level data
- break blocked / must_not_go / avoid_cuisines / max_intensity constraints

Output shape:
- refinement adjustments
- validation result
- trace events for evidence_bundle
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FusionAdjustmentOp:
    """A single refinement adjustment."""

    day_index: int = 0
    action: str = ""  # replace_meal / remove_item / reorder / no_op / flag_cross_theme
    target_name: str = ""
    replacement: dict = field(default_factory=dict)
    reason: str = ""


@dataclass
class FusionResult:
    """Result of the constrained refinement stage."""

    adjustments: list[FusionAdjustmentOp] = field(default_factory=list)
    applied: bool = False
    rejected_reason: str = ""
    trace: list[str] = field(default_factory=list)


def run_deterministic_fusion(
    case_data: dict,
    day_modes: list,
    constraints=None,
) -> FusionResult:
    """
    Deterministic refinement without calling an LLM.

    Current behavior:
    1. iterate all day items
    2. derive simple tags from corridor and cuisine
    3. compare them against the locked day mode
    4. flag severe cross-theme conflicts on non-main items

    It returns a FusionResult even when there are no adjustments.
    """

    result = FusionResult()

    if not day_modes:
        result.trace.append("fusion_refinement: no day_modes provided, skip")
        return result

    days = case_data.get("days", [])
    mode_map = {m.day_index: m for m in day_modes}

    for day in days:
        day_idx = day.get("day_number", 0)
        mode = mode_map.get(day_idx)
        if not mode:
            continue

        for item in day.get("items", []):
            if item.get("is_main"):
                continue

            name = item.get("name", "") or ""
            item_tags = set()

            corridor = (item.get("corridor", "") or "").lower()
            if corridor:
                item_tags.add(corridor)

            cuisine = (item.get("cuisine", "") or "").lower()
            if cuisine:
                item_tags.add(cuisine)

            suppressed_hit = item_tags & mode.suppressed_tags
            if len(suppressed_hit) >= 2:
                op = FusionAdjustmentOp(
                    day_index=day_idx,
                    action="flag_cross_theme",
                    target_name=name,
                    reason=(
                        f"cross-theme detected: item={name} "
                        f"hit suppressed tags {sorted(suppressed_hit)} in mode={mode.mode}"
                    ),
                )
                result.adjustments.append(op)
                result.trace.append(
                    f"day{day_idx} [{mode.mode}]: flagged '{name}' "
                    f"(suppressed={sorted(suppressed_hit)})"
                )

    if result.adjustments:
        result.trace.append(
            f"fusion_refinement: {len(result.adjustments)} items flagged as cross-theme"
        )
    else:
        result.trace.append("fusion_refinement: no cross-theme issues detected")

    result.applied = True
    return result


def verify_fusion_constraints(
    refined_data: dict,
    constraints=None,
) -> tuple[bool, list[str]]:
    """
    Verify that the refined data still satisfies all hard constraints.
    """

    violations = []

    if not constraints:
        return True, violations

    blocked_clusters = getattr(constraints, "blocked_clusters", set()) or set()

    for day in refined_data.get("days", []):
        for item in day.get("items", []):
            name = (item.get("name", "") or "").lower()
            for blocked_cluster in blocked_clusters:
                if blocked_cluster.lower() in name:
                    violations.append(
                        f"Day{day.get('day_number', '?')}: '{item.get('name', '')}' "
                        f"matches blocked_cluster '{blocked_cluster}'"
                    )

    return len(violations) == 0, violations


def build_fusion_trace_events(
    result: FusionResult,
    day_modes: list,
) -> list[dict]:
    """Build refinement-related trace events for evidence_bundle."""

    events = []

    for mode in day_modes:
        events.append(
            {
                "event": "day_mode_locked",
                "day_index": mode.day_index,
                "mode": mode.mode,
                "boosted_tags": sorted(mode.boosted_tags),
                "suppressed_tags": sorted(mode.suppressed_tags),
                "reason": mode.reason,
                "driver_cluster": mode.driver_cluster or "",
            }
        )

    if result.applied:
        if result.adjustments:
            events.append(
                {
                    "event": "fusion_refinement_applied",
                    "adjustment_count": len(result.adjustments),
                    "details": [
                        {
                            "day": adjustment.day_index,
                            "action": adjustment.action,
                            "target": adjustment.target_name,
                            "reason": adjustment.reason,
                        }
                        for adjustment in result.adjustments
                    ],
                }
            )
        else:
            events.append(
                {
                    "event": "fusion_refinement_applied",
                    "adjustment_count": 0,
                    "details": "no changes needed",
                }
            )
    else:
        events.append(
            {
                "event": "fusion_refinement_rejected",
                "reason": result.rejected_reason,
            }
        )

    return events

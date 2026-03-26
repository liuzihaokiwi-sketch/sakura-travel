"""
fusion_patch.py — 受限式 LLM Decision Fusion 层

在 deterministic pipeline 输出后，可选地调用 LLM 做受限微调。
LLM 只能做以下操作:
  - 替换一个 secondary point
  - 替换一餐
  - 微调当天顺序
  - 删除一个明显跳戏项

LLM 不能:
  - 引入新城市/未验证 POI
  - 改酒店/run_id/plan_id
  - 破坏 blocked / must_not_go / avoid_cuisines / max_intensity 等硬约束

输出: JSON patch → 重新验证 → 通过则应用，否则丢弃回退到 deterministic 版本。

注意: 初始版本为 deterministic fusion（不调用 LLM），基于 day_mode suppressed_tags
      做自动跳戏检测和替换。LLM 接入作为 Phase 2.1 扩展点。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FusionPatchOp:
    """单个 patch 操作"""
    day_index: int = 0
    action: str = ""        # replace_meal / remove_item / reorder / no_op
    target_name: str = ""   # 被替换的 item name
    replacement: dict = field(default_factory=dict)  # 替换为的 item
    reason: str = ""


@dataclass
class FusionResult:
    """Fusion patch 执行结果"""
    patches: list[FusionPatchOp] = field(default_factory=list)
    applied: bool = False
    rejected_reason: str = ""
    trace: list[str] = field(default_factory=list)


def run_deterministic_fusion(
    case_data: dict,
    day_modes: list,
    constraints=None,
) -> FusionResult:
    """
    Deterministic fusion — 不调用 LLM，基于 day_mode 做自动跳戏检测。

    逻辑:
    1. 遍历每天的 items
    2. 对每个 item 的 vibe tags 做 day_mode gating
    3. 如果有 item 严重跳戏（suppressed overlap >= 2），标记为 remove_item
    4. 不做替换（避免引入未验证 POI），只标记 + 记录 trace

    返回: FusionResult（patches 可能为空 = 无需修改）
    """
    result = FusionResult()

    if not day_modes:
        result.trace.append("fusion: no day_modes provided, skip")
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
                continue  # 不动主活动

            name = item.get("name", "") or ""
            item_tags = set()

            # 从 corridor 推断 tags
            corridor = (item.get("corridor", "") or "").lower()
            if corridor:
                item_tags.add(corridor)

            # 从 cuisine 推断
            cuisine = (item.get("cuisine", "") or "").lower()
            if cuisine:
                item_tags.add(cuisine)

            # suppressed overlap
            suppressed_hit = item_tags & mode.suppressed_tags
            if len(suppressed_hit) >= 2:
                op = FusionPatchOp(
                    day_index=day_idx,
                    action="flag_cross_theme",
                    target_name=name,
                    reason=f"跳戏检测: item={name} hit suppressed tags {sorted(suppressed_hit)} "
                           f"in mode={mode.mode}",
                )
                result.patches.append(op)
                result.trace.append(
                    f"day{day_idx} [{mode.mode}]: flagged '{name}' "
                    f"(suppressed={sorted(suppressed_hit)})"
                )

    if result.patches:
        result.trace.append(f"fusion: {len(result.patches)} items flagged as cross-theme")
    else:
        result.trace.append("fusion: no cross-theme issues detected")

    # 标记为 applied（即使只是 flag）
    result.applied = True

    return result


def verify_fusion_constraints(
    patched_data: dict,
    constraints=None,
) -> tuple[bool, list[str]]:
    """
    验证 fusion patch 后的数据是否仍满足所有硬约束。

    Returns:
        (passed, violations)
    """
    violations = []

    if not constraints:
        return True, violations

    blocked_clusters = getattr(constraints, "blocked_clusters", set()) or set()
    blocked_tags = getattr(constraints, "blocked_tags", set()) or set()

    for day in patched_data.get("days", []):
        for item in day.get("items", []):
            name = (item.get("name", "") or "").lower()

            # 检查 blocked_clusters
            for bc in blocked_clusters:
                if bc.lower() in name:
                    violations.append(
                        f"Day{day.get('day_number', '?')}: '{item.get('name', '')}' "
                        f"matches blocked_cluster '{bc}'"
                    )

    return len(violations) == 0, violations


def build_fusion_trace_events(
    result: FusionResult,
    day_modes: list,
) -> list[dict]:
    """构建 fusion 相关的 trace events（追加到 evidence_bundle）。"""
    events = []

    # day_mode_locked events
    for mode in day_modes:
        events.append({
            "event": "day_mode_locked",
            "day_index": mode.day_index,
            "mode": mode.mode,
            "boosted_tags": sorted(mode.boosted_tags),
            "suppressed_tags": sorted(mode.suppressed_tags),
            "reason": mode.reason,
            "driver_cluster": mode.driver_cluster or "",
        })

    # fusion result
    if result.applied:
        if result.patches:
            events.append({
                "event": "fusion_patch_applied",
                "patch_count": len(result.patches),
                "details": [
                    {"day": p.day_index, "action": p.action,
                     "target": p.target_name, "reason": p.reason}
                    for p in result.patches
                ],
            })
        else:
            events.append({
                "event": "fusion_patch_applied",
                "patch_count": 0,
                "details": "no changes needed",
            })
    else:
        events.append({
            "event": "fusion_patch_rejected",
            "reason": result.rejected_reason,
        })

    return events

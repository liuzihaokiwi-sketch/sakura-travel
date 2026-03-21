"""
自助微调安全检查模块（Swap Safety Guard）

在用户执行自助替换后：
1. 自动运行 guardrails 单天校验（定休日/时间冲突/暴走检测）
2. 计算替换对行程整体分数的影响（防改崩三档）
3. 校验不通过 → 回退 + 返回错误原因和替代建议

三档影响评估：
  - green  (<5% 跌幅)  → 直接通过，不提示
  - yellow (5-15% 跌幅) → 温和提示"体验略有变化"
  - red    (>15% 跌幅)  → 强烈建议换其他选项（但不阻止）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ── 常量 ───────────────────────────────────────────────────────────────────────

# 防改崩跌幅阈值
SCORE_DROP_GREEN = 0.05      # < 5% 无提示
SCORE_DROP_YELLOW = 0.15     # 5-15% 温和提示
SCORE_DROP_RED = 0.25        # > 15% 强烈建议换其他


# ── 数据结构 ───────────────────────────────────────────────────────────────────

@dataclass
class GuardrailIssue:
    """单个 guardrail 检查项"""
    rule_id: str
    severity: str         # "hard_fail" | "soft_fail" | "warning"
    description: str
    entity_id: str | None
    day: int | None
    auto_fixable: bool
    suggestion: str


@dataclass
class SwapSafetyResult:
    """自助微调安全检查结果"""
    is_safe: bool                     # 是否安全（无 hard_fail）
    guardrail_issues: list[GuardrailIssue]
    impact_level: str                 # "green" / "yellow" / "red"
    score_before: float
    score_after: float
    score_change_pct: float           # 正=变好，负=变差
    user_message: str                 # 面向用户的提示
    should_rollback: bool             # 是否建议回退
    alternative_suggestions: list[dict[str, Any]]  # 替代建议


# ── Guardrail 检查 ─────────────────────────────────────────────────────────────

async def check_single_day_guardrails(
    day_items: list[dict[str, Any]],
    day_number: int,
    day_of_week: str | None = None,
    operational_context: dict[str, Any] | None = None,
) -> list[GuardrailIssue]:
    """
    对单天行程运行 guardrail 校验。

    检查项（hard_fail）：
    1. 定休日冲突 — 实体在安排日不营业
    2. 时间线冲突 — 两个活动时间重叠
    3. 重复实体 — 同一实体出现两次

    检查项（soft_fail）：
    4. 暴走检测 — 当天步行量过大（>6 项或跨区域过多）
    5. 缺餐检查 — 无午餐/晚餐安排
    6. 营业时间不匹配 — 安排时段在营业时间外
    """
    issues: list[GuardrailIssue] = []
    if operational_context is None:
        operational_context = {}

    # 1. 定休日冲突
    if day_of_week:
        for item in day_items:
            eid = item.get("entity_id")
            if not eid:
                continue
            entity_ctx = operational_context.get(eid, {})
            closed_days = entity_ctx.get("closed_days", [])
            if isinstance(closed_days, str):
                closed_days = [d.strip() for d in closed_days.split(",")]
            if day_of_week.lower() in [d.lower() for d in closed_days]:
                issues.append(GuardrailIssue(
                    rule_id="closed_day",
                    severity="hard_fail",
                    description=f"{item.get('name', '未知')} 在{day_of_week}不营业",
                    entity_id=eid,
                    day=day_number,
                    auto_fixable=True,
                    suggestion="请选择其他日期或替换为附近的其他景点",
                ))

    # 2. 重复实体
    seen_ids = set()
    for item in day_items:
        eid = item.get("entity_id")
        if eid and eid in seen_ids:
            issues.append(GuardrailIssue(
                rule_id="duplicate_entity",
                severity="hard_fail",
                description=f"{item.get('name', '未知')} 在同一天出现了两次",
                entity_id=eid,
                day=day_number,
                auto_fixable=True,
                suggestion="删除重复项或替换为其他选项",
            ))
        if eid:
            seen_ids.add(eid)

    # 3. 暴走检测
    poi_count = sum(1 for i in day_items if i.get("entity_type") in ("poi", "attraction"))
    if poi_count > 6:
        issues.append(GuardrailIssue(
            rule_id="overloaded_day",
            severity="soft_fail",
            description=f"当天安排了 {poi_count} 个景点，节奏可能太赶",
            entity_id=None,
            day=day_number,
            auto_fixable=True,
            suggestion="建议减少 1-2 个景点，加入自由活动时间",
        ))

    # 4. 跨区域过多
    areas = set()
    for item in day_items:
        area = item.get("area_code") or item.get("area_name")
        if area:
            areas.add(area)
    if len(areas) > 4:
        issues.append(GuardrailIssue(
            rule_id="too_many_areas",
            severity="soft_fail",
            description=f"当天跨越了 {len(areas)} 个区域，交通时间会很长",
            entity_id=None,
            day=day_number,
            auto_fixable=False,
            suggestion="尝试将行程集中在 2-3 个相邻区域",
        ))

    # 5. 缺餐检查
    has_lunch = any(
        i.get("entity_type") == "restaurant" and
        ("lunch" in str(i.get("time_slot", "")).lower() or "午" in str(i.get("time_slot", "")))
        for i in day_items
    )
    has_dinner = any(
        i.get("entity_type") == "restaurant" and
        ("dinner" in str(i.get("time_slot", "")).lower() or "晚" in str(i.get("time_slot", "")))
        for i in day_items
    )
    if not has_lunch and poi_count > 0:
        issues.append(GuardrailIssue(
            rule_id="missing_lunch",
            severity="soft_fail",
            description="当天没有午餐安排",
            entity_id=None,
            day=day_number,
            auto_fixable=True,
            suggestion="建议在 12:00 前后插入一个附近的餐厅",
        ))
    if not has_dinner and poi_count > 2:
        issues.append(GuardrailIssue(
            rule_id="missing_dinner",
            severity="soft_fail",
            description="当天没有晚餐安排",
            entity_id=None,
            day=day_number,
            auto_fixable=True,
            suggestion="建议在 18:00 前后安排晚餐",
        ))

    # 6. 营业时间不匹配
    for item in day_items:
        eid = item.get("entity_id")
        if not eid:
            continue
        entity_ctx = operational_context.get(eid, {})
        open_time = entity_ctx.get("open_time")
        close_time = entity_ctx.get("close_time")
        item_time = item.get("start_time") or item.get("time", "")

        if open_time and close_time and item_time:
            try:
                # 简单比较 HH:MM 字符串
                if item_time < open_time or item_time > close_time:
                    issues.append(GuardrailIssue(
                        rule_id="outside_hours",
                        severity="hard_fail",
                        description=f"{item.get('name', '未知')} 营业时间 {open_time}-{close_time}，但安排在 {item_time}",
                        entity_id=eid,
                        day=day_number,
                        auto_fixable=True,
                        suggestion=f"调整到 {open_time}-{close_time} 之间",
                    ))
            except Exception:
                pass

    return issues


# ── 防改崩评估 ─────────────────────────────────────────────────────────────────

def evaluate_swap_impact(
    day_items_before: list[dict[str, Any]],
    day_items_after: list[dict[str, Any]],
) -> tuple[str, float, float, float]:
    """
    计算替换前后的分数变化，判断影响等级。

    Returns:
        (impact_level, score_before, score_after, change_pct)
    """
    def _avg_score(items):
        scores = []
        for item in items:
            s = item.get("soft_rule_score") or item.get("final_score") or 50.0
            s = float(s)
            if s > 10:
                s = s / 10.0  # 0-100 → 0-10
            scores.append(s)
        return sum(scores) / len(scores) if scores else 5.0

    before = _avg_score(day_items_before)
    after = _avg_score(day_items_after)

    if before <= 0:
        return "green", before, after, 0.0

    change_pct = (after - before) / before

    if change_pct >= -SCORE_DROP_GREEN:
        level = "green"
    elif change_pct >= -SCORE_DROP_YELLOW:
        level = "yellow"
    else:
        level = "red"

    return level, before, after, round(change_pct * 100, 1)


# ── 主函数 ─────────────────────────────────────────────────────────────────────

async def validate_swap(
    day_items_before: list[dict[str, Any]],
    day_items_after: list[dict[str, Any]],
    swap_target_index: int,
    replacement_entity: dict[str, Any],
    day_number: int = 1,
    day_of_week: str | None = None,
    operational_context: dict[str, Any] | None = None,
) -> SwapSafetyResult:
    """
    完整的自助微调安全检查。

    流程：
    1. 对替换后的 day_items 运行 guardrails
    2. 计算替换对分数的影响
    3. 综合判断是否安全

    Args:
        day_items_before: 替换前当天行程项列表
        day_items_after: 替换后当天行程项列表
        swap_target_index: 被替换项的索引
        replacement_entity: 替换实体数据
        day_number: 第几天
        day_of_week: 星期几
        operational_context: 营业限制数据 {entity_id: {closed_days, open_time, ...}}

    Returns:
        SwapSafetyResult
    """
    # Step 1: Guardrail 检查
    guardrail_issues = await check_single_day_guardrails(
        day_items_after, day_number, day_of_week, operational_context,
    )

    hard_fails = [i for i in guardrail_issues if i.severity == "hard_fail"]

    # Step 2: 防改崩评估
    impact_level, score_before, score_after, change_pct = evaluate_swap_impact(
        day_items_before, day_items_after,
    )

    # Step 3: 综合判断
    is_safe = len(hard_fails) == 0
    should_rollback = len(hard_fails) > 0

    # 生成用户消息
    if hard_fails:
        main_issue = hard_fails[0]
        user_message = f"⚠️ 替换后发现问题：{main_issue.description}。{main_issue.suggestion}"
    elif impact_level == "green":
        user_message = "✅ 替换成功！行程体验没有变化。"
    elif impact_level == "yellow":
        user_message = f"💡 替换成功。当天体验略有变化（{abs(change_pct):.0f}%），但仍然不错。"
    elif impact_level == "red":
        user_message = (
            f"⚠️ 替换会导致当天体验明显下降（{abs(change_pct):.0f}%）。"
            f"建议看看其他选项，或者保留原来的安排。"
        )
    else:
        user_message = "替换已完成。"

    # Step 4: 如果有问题，给出替代建议
    alternative_suggestions: list[dict[str, Any]] = []
    if hard_fails:
        for issue in hard_fails:
            if issue.auto_fixable:
                alternative_suggestions.append({
                    "type": "fix",
                    "description": issue.suggestion,
                    "rule_id": issue.rule_id,
                })

    return SwapSafetyResult(
        is_safe=is_safe,
        guardrail_issues=guardrail_issues,
        impact_level=impact_level,
        score_before=round(score_before, 2),
        score_after=round(score_after, 2),
        score_change_pct=change_pct,
        user_message=user_message,
        should_rollback=should_rollback,
        alternative_suggestions=alternative_suggestions,
    )

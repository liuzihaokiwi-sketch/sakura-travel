"""
chapter_planner.py — 章节规划器（L3-03）

输入：PlanningOutput
输出：list[ChapterPlan]

章节划分规则：
  - 所有报告：ch_frontmatter（封面 → 动态注意事项）
  - 3-5 天：不拆章节，所有天放一个 ch_days
  - 6-8 天：如果跨 2 个城市圈，按圈拆 ch_{circle_id}
  - 9-14 天：必须按城市圈拆章节，每圈一个 chapter
  - 所有报告：ch_appendix

依赖：planning_output.PlanningOutput
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.domains.rendering.planning_output import PlanningOutput


@dataclass
class ChapterPlan:
    chapter_id: str                # "ch_frontmatter" / "ch_kansai" / "ch_tokyo" / "ch_appendix"
    chapter_type: str              # "frontmatter" / "circle" / "days" / "special" / "appendix"
    title: str
    subtitle: Optional[str] = None
    goal: Optional[str] = None
    mood: Optional[str] = None
    covered_days: list[int] = field(default_factory=list)
    primary_circle_id: Optional[str] = None
    trigger_reason: Optional[str] = None
    importance: str = "high"       # "high" / "medium" / "low"


def plan_chapters(payload: PlanningOutput) -> list[ChapterPlan]:
    """
    根据行程长度和城市圈分布决定章节结构。

    Args:
        payload: PlanningOutput，必须含 meta.total_days + days + circles + day_circle_map

    Returns:
        有序的 ChapterPlan 列表，始终以 ch_frontmatter 开头，ch_appendix 结尾
    """
    total_days = payload.meta.total_days
    chapters: list[ChapterPlan] = []

    # ── 1. 前置章节（永远存在） ───────────────────────────────────────────
    chapters.append(ChapterPlan(
        chapter_id="ch_frontmatter",
        chapter_type="frontmatter",
        title="行程概览",
        subtitle="路线设计 · 酒店策略 · 预约提醒",
        goal="在出发前掌握全局：路线逻辑、住宿安排、必订事项",
        mood="清晰",
        covered_days=[],
        trigger_reason="所有报告固定生成",
        importance="high",
    ))

    # ── 2. 主体章节：按行程长度 + 城市圈决定拆分方式 ──────────────────────
    circles = payload.circles or []
    day_circle_map: dict[int, str] = {
        int(k): v for k, v in (payload.day_circle_map or {}).items()
    }

    # 单圈或 ≤5 天 → 不拆章节，全天放一个 ch_days
    if len(circles) <= 1 or total_days <= 5:
        all_days = [d.day_index for d in payload.days]
        circle = circles[0] if circles else None
        chapters.append(ChapterPlan(
            chapter_id="ch_days",
            chapter_type="days",
            title=circle.name_zh if circle else "行程详情",
            subtitle=f"共 {total_days} 天",
            goal="每天的详细执行计划",
            mood="探索",
            covered_days=all_days,
            primary_circle_id=circle.circle_id if circle else None,
            trigger_reason=f"≤5天或单圈行程，不拆章节",
            importance="high",
        ))

    # 多圈 6-8 天 → 按圈拆，但每圈可能只占部分天数
    elif 6 <= total_days <= 8:
        _append_circle_chapters(chapters, payload, circles, day_circle_map, "6-8天多圈行程")

    # 多圈 9-14 天 → 必须按圈拆
    else:
        _append_circle_chapters(chapters, payload, circles, day_circle_map, "9-14天行程按圈拆章节")

    # ── 3. 附录章节（永远存在） ───────────────────────────────────────────
    chapters.append(ChapterPlan(
        chapter_id="ch_appendix",
        chapter_type="appendix",
        title="附录",
        subtitle="出发准备 · 补充景点 · 应急信息",
        goal="收录所有无法归入具体天的实用信息",
        mood="实用",
        covered_days=[],
        trigger_reason="所有报告固定生成",
        importance="medium",
    ))

    return chapters


def _append_circle_chapters(
    chapters: list[ChapterPlan],
    payload: PlanningOutput,
    circles: list,
    day_circle_map: dict[int, str],
    trigger_reason: str,
) -> None:
    """
    为多圈行程按城市圈追加 chapter。

    - 如果有 day_circle_map，按圈分组天数
    - 如果没有 day_circle_map，均分天数到各圈
    """
    all_day_indices = [d.day_index for d in payload.days]

    if day_circle_map:
        # 按 day_circle_map 分组
        circle_days: dict[str, list[int]] = {}
        for day_idx in all_day_indices:
            cid = day_circle_map.get(day_idx)
            if cid:
                circle_days.setdefault(cid, []).append(day_idx)
            else:
                # 未映射的天归入第一个圈
                first_cid = circles[0].circle_id if circles else "unknown"
                circle_days.setdefault(first_cid, []).append(day_idx)
    else:
        # 没有 day_circle_map：均分天数
        circle_days = {}
        chunk = max(1, len(all_day_indices) // max(1, len(circles)))
        for i, circle in enumerate(circles):
            start = i * chunk
            end = start + chunk if i < len(circles) - 1 else len(all_day_indices)
            circle_days[circle.circle_id] = all_day_indices[start:end]

    # 按 circles 顺序添加章节（保证顺序稳定）
    for circle in circles:
        days_in_circle = sorted(circle_days.get(circle.circle_id, []))
        if not days_in_circle:
            continue

        # 从 payload.chapter_summaries 中找对应 goal/mood
        cs = next(
            (s for s in payload.chapter_summaries if s.chapter_id == f"ch_{circle.circle_id}"),
            None,
        )

        chapters.append(ChapterPlan(
            chapter_id=f"ch_{circle.circle_id}",
            chapter_type="circle",
            title=circle.name_zh,
            subtitle=f"第 {min(days_in_circle)}-{max(days_in_circle)} 天",
            goal=cs.goal if cs else f"深度探索{circle.name_zh}",
            mood=cs.mood if cs else "探索",
            covered_days=days_in_circle,
            primary_circle_id=circle.circle_id,
            trigger_reason=trigger_reason,
            importance="high",
        ))

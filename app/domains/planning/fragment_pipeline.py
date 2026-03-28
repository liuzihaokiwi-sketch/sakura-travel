"""
Fragment-Aware Generation Pipeline — 片段库接入生成管线 (H10)

对应文档 §9 步骤 5-8：
  profile norm → 片段复用 → 硬规则 → 软规则 → AI 补充 → 质量门控

本模块在生成管线中插入片段复用层。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.detail_forms import DetailForm
from app.domains.planning.fragment_reuse import (
    HitTier,
    ReusePlan,
    ReuseRequest,
    find_reusable_fragments,
)

logger = logging.getLogger(__name__)


# ── Step 5: Profile Normalization ─────────────────────────────────────────────

@dataclass
class PlanningProfile:
    """标准化用户画像 — 生成管线内部统一数据结构"""
    city_codes: list[str]
    duration_days: int
    theme_family: Optional[str] = None
    party_type: Optional[str] = None
    budget_level: Optional[str] = None
    budget_focus: Optional[str] = None
    pace: Optional[str] = None
    season_tag: Optional[str] = None
    must_visit: list[str] = field(default_factory=list)
    avoid_tags: list[str] = field(default_factory=list)
    arrival_airport: Optional[str] = None
    departure_airport: Optional[str] = None
    has_jr_pass: Optional[bool] = None
    user_wish_text: Optional[str] = None
    # 原始表单 ID（审计用）
    detail_form_id: Optional[uuid.UUID] = None
    submission_id: Optional[str] = None


async def normalize_profile(
    session: AsyncSession,
    submission_id: str,
) -> PlanningProfile:
    """
    从 detail_forms 读取用户填写数据，标准化为 PlanningProfile。
    如果 detail_form 不存在（比如旧订单），从 quiz_submissions 构造最小画像。
    """
    from sqlalchemy import select, text

    # 尝试从 detail_forms 读取
    stmt = select(DetailForm).where(DetailForm.submission_id == submission_id)
    result = await session.execute(stmt)
    form = result.scalar_one_or_none()

    if form and form.is_complete:
        # 完整表单 → 丰富画像
        cities = form.cities or []
        city_codes = [c.get("city_code", "tokyo") for c in cities] if cities else ["tokyo"]

        # 推断季节
        season_tag = _infer_season(form.travel_start_date)

        profile = PlanningProfile(
            city_codes=city_codes,
            duration_days=form.duration_days or 5,
            theme_family=form.theme_family,
            party_type=form.party_type,
            budget_level=form.budget_level,
            budget_focus=form.budget_focus,
            pace=form.pace,
            season_tag=season_tag,
            must_visit=form.must_visit_places or [],
            avoid_tags=form.avoid_tags or [],
            arrival_airport=form.arrival_airport,
            departure_airport=form.departure_airport,
            has_jr_pass=form.has_jr_pass,
            user_wish_text=form.free_text_wishes,
            detail_form_id=form.form_id,
            submission_id=submission_id,
        )
        logger.info("profile normalized from detail_form: cities=%s theme=%s", city_codes, form.theme_family)
        return profile

    # Fallback：从 quiz_submissions 构造最小画像
    row = await session.execute(
        text("SELECT destination, style FROM quiz_submissions WHERE id = :id"),
        {"id": submission_id},
    )
    quiz = row.fetchone()
    if quiz:
        dest = quiz[0] or "tokyo"
        style = quiz[1] or "classic"

        # quiz style → theme_family 映射
        style_map = {
            "经典不踩坑": "classic_first",
            "性价比更高": "classic_first",
            "奢华体验": "couple_aesthetic",
            "小众深玩": "culture_deep",
            "情侣氛围": "couple_aesthetic",
            "亲子轻松": "family_easy",
        }

        dest_map = {
            "东京": ["tokyo"],
            "京都": ["kyoto"],
            "大阪": ["osaka"],
            "关西": ["osaka", "kyoto"],
            "北海道": ["hokkaido"],
        }

        profile = PlanningProfile(
            city_codes=dest_map.get(dest, [dest.lower()]),
            duration_days=5,  # 默认
            theme_family=style_map.get(style, "classic_first"),
            submission_id=submission_id,
        )
        logger.info("profile normalized from quiz: dest=%s style=%s", dest, style)
        return profile

    # 最后 fallback
    logger.warning("no data found for submission %s, using default profile", submission_id)
    return PlanningProfile(city_codes=["tokyo"], duration_days=5, submission_id=submission_id)


def _infer_season(date_str: Optional[str]) -> Optional[str]:
    """从日期推断季节标签"""
    if not date_str:
        return None
    try:
        month = int(date_str.split("-")[1])
    except (IndexError, ValueError):
        return None

    if month == 4:
        return "cherry_blossom"
    if month in (3, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


# ── Step 6-8: Fragment-Aware Assembly ─────────────────────────────────────────

@dataclass
class FragmentAwareContext:
    """传递给 assembler 的片段复用上下文"""
    profile: PlanningProfile
    reuse_plan: Optional[ReusePlan]
    skeleton_hints: dict[int, dict]  # day_index → {fragments, slot_assignments}
    generation_mode: str  # "fragment_first" | "template_only" | "hybrid"


async def prepare_fragment_context(
    session: AsyncSession,
    profile: PlanningProfile,
) -> FragmentAwareContext:
    """
    执行片段复用流程，准备 assembler 需要的上下文。

    流程：
    1. 构建 ReuseRequest
    2. 调用 find_reusable_fragments
    3. 将结果转化为 skeleton_hints（按天分组）
    4. 确定 generation_mode
    """
    # Step 1: 构建 ReuseRequest
    reuse_req = ReuseRequest(
        city_codes=profile.city_codes,
        theme_family=profile.theme_family,
        party_type=profile.party_type,
        budget_level=profile.budget_level,
        season_tag=profile.season_tag,
        duration_days=profile.duration_days,
        user_wish_text=profile.user_wish_text,
    )

    # Step 2: 执行片段复用
    reuse_plan = await find_reusable_fragments(session, reuse_req)

    # Step 3: 转化为 skeleton_hints
    skeleton_hints: dict[int, dict] = {}
    for frag in reuse_plan.fragments_adopted:
        day = frag.day_index_hint if frag.day_index_hint is not None else 0
        if day not in skeleton_hints:
            skeleton_hints[day] = {"fragments": [], "slots_filled": []}

        skeleton_hints[day]["fragments"].append({
            "fragment_id": str(frag.fragment_id),
            "fragment_type": frag.fragment_type,
            "title": frag.title,
            "hit_tier": frag.hit_tier.value,
            "final_score": round(frag.final_score, 3),
            "body_skeleton": frag.body_skeleton,
            "body_prose": frag.body_prose,
            "duration_slot": frag.duration_slot,
        })

        if frag.duration_slot:
            skeleton_hints[day]["slots_filled"].append(frag.duration_slot)

    # Step 4: 确定 generation_mode
    stats = reuse_plan.stats
    adopted_count = stats.get("adopted_count", 0)
    gap_count = stats.get("gap_count", 0)
    total_slots = profile.duration_days * 3  # morning/afternoon/evening

    if adopted_count == 0:
        mode = "template_only"
    elif gap_count <= total_slots * 0.3:
        mode = "fragment_first"
    else:
        mode = "hybrid"

    logger.info(
        "fragment_context: mode=%s adopted=%d gaps=%d total_slots=%d",
        mode, adopted_count, gap_count, total_slots,
    )

    return FragmentAwareContext(
        profile=profile,
        reuse_plan=reuse_plan,
        skeleton_hints=skeleton_hints,
        generation_mode=mode,
    )


# ── 主入口：供 generate_trip job 调用 ─────────────────────────────────────────

async def run_fragment_aware_pipeline(
    session: AsyncSession,
    submission_id: str,
) -> FragmentAwareContext:
    """
    完整的片段感知管线入口。

    1. normalize_profile
    2. prepare_fragment_context (含 find_reusable_fragments)
    3. 返回 FragmentAwareContext 供 assembler 使用

    调用方式（在 generate_trip.py 中）：
        ctx = await run_fragment_aware_pipeline(session, submission_id)
        # ctx.skeleton_hints 传给决策链
        # ctx.generation_mode 决定生成策略
    """
    profile = await normalize_profile(session, submission_id)
    context = await prepare_fragment_context(session, profile)
    return context

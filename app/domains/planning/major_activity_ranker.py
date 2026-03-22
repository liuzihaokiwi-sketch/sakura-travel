"""
major_activity_ranker.py — 主要活动排序器（Phase 2 决策链第 2 步）

输入：
  - circle_id（已选城市圈）
  - TripProfile（标准化画像）
  - EligibilityResult（已通过资格过滤的簇 ID 集合）
  - PrecheckResult（前置风险检查结果）

输出：
  - 选中的主要活动列表（按优先级排序）
  - 每个活动的评分明细
  - trace

评分公式（risk 不参与评分，作为 gate + metadata）：
  major_score = base_quality_score * 0.55 + context_fit_score * 0.45

容量规则：
  - 到达日/离开日各按 0.5 个 major 容量
  - 中间日按 1.0 个 major 容量
  - 半日型活动占 0.5 容量，全日型占 1.0 容量
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import TripProfile
from app.db.models.city_circles import ActivityCluster, CircleEntityRole
from app.db.models.derived import EntityScore
from app.db.models.soft_rules import EntitySoftScore

logger = logging.getLogger(__name__)


# ── 权重 ──────────────────────────────────────────────────────────────────────

W_BASE_QUALITY = 0.55
W_CONTEXT_FIT = 0.45


# ── 输出结构 ──────────────────────────────────────────────────────────────────

@dataclass
class MajorExplain:
    """E4: 结构化 explain — 每个 major 同步产出。"""
    why_selected: str = ""
    why_not_selected: str = ""
    expected_tradeoff: str = ""
    fallback_hint: str = ""


@dataclass
class RankedMajor:
    cluster_id: str
    name_zh: str
    level: str                            # S / A / B
    major_score: float = 0.0
    base_quality_score: float = 0.0
    context_fit_score: float = 0.0
    precheck_status: str = "pass"         # pass / fail / warn
    live_risk_level: str = "low"          # low / medium / high
    capacity_units: float = 1.0           # 0.5 或 1.0
    default_duration: str = "full_day"
    primary_corridor: str = ""
    anchor_entity_ids: list[uuid.UUID] = field(default_factory=list)
    selected: bool = False
    selection_reason: str = ""
    explain: MajorExplain = field(default_factory=MajorExplain)


@dataclass
class MajorRankingResult:
    selected_majors: list[RankedMajor] = field(default_factory=list)
    all_ranked: list[RankedMajor] = field(default_factory=list)
    capacity_total: float = 0.0
    capacity_used: float = 0.0
    trace: list[str] = field(default_factory=list)


# ── 主入口 ────────────────────────────────────────────────────────────────────

async def rank_major_activities(
    session: AsyncSession,
    circle_id: str,
    profile: TripProfile,
    passed_cluster_ids: set[str],
    precheck_failed_entity_ids: set[uuid.UUID] = frozenset(),
    override_resolver: "OverrideResolver | None" = None,
) -> MajorRankingResult:
    """
    对通过资格过滤的活动簇进行排序，按容量上限选出主要活动。
    如果传入 override_resolver，会在 context_fit 分上叠加运营干预的 weight_delta。
    """
    result = MajorRankingResult()

    # 1. 计算容量
    days = profile.duration_days or 5
    # 到达日 + 离开日各 0.5, 中间日各 1.0
    capacity = max(1.0, (days - 2) * 1.0 + 0.5 + 0.5)
    result.capacity_total = capacity
    result.trace.append(f"capacity: {capacity} major units for {days} days")

    # 2. 加载通过过滤的活动簇
    if not passed_cluster_ids:
        result.trace.append("无通过过滤的活动簇")
        return result

    clusters_q = await session.execute(
        select(ActivityCluster).where(
            and_(
                ActivityCluster.cluster_id.in_(passed_cluster_ids),
                ActivityCluster.circle_id == circle_id,
                ActivityCluster.is_active == True,
            )
        )
    )
    clusters = clusters_q.scalars().all()

    if not clusters:
        result.trace.append("无活跃活动簇")
        return result

    # 3. 加载每个簇的锚点实体 ID
    roles_q = await session.execute(
        select(CircleEntityRole).where(
            and_(
                CircleEntityRole.circle_id == circle_id,
                CircleEntityRole.cluster_id.in_([c.cluster_id for c in clusters]),
                CircleEntityRole.is_cluster_anchor == True,
            )
        )
    )
    roles = roles_q.scalars().all()
    cluster_anchors: dict[str, list[uuid.UUID]] = {}
    for role in roles:
        if role.cluster_id:
            cluster_anchors.setdefault(role.cluster_id, []).append(role.entity_id)

    # 4. 加载锚点实体的评分
    all_anchor_ids = [eid for ids in cluster_anchors.values() for eid in ids]
    base_scores = await _load_base_quality_scores(session, all_anchor_ids)
    context_scores = await _load_context_fit_scores(session, all_anchor_ids, profile)

    # 5. 逐簇评分
    for cluster in clusters:
        ranked = _score_cluster(
            cluster,
            cluster_anchors.get(cluster.cluster_id, []),
            base_scores,
            context_scores,
            precheck_failed_entity_ids,
            profile,
        )

        # L4-02: 运营干预 weight_delta 接入
        if override_resolver is not None:
            anchor_ids = cluster_anchors.get(cluster.cluster_id, [])
            total_delta = 0.0
            for eid in anchor_ids:
                total_delta += override_resolver.get_weight_delta(str(eid))
            if total_delta != 0.0:
                ranked.context_fit_score = min(100.0, max(0.0, ranked.context_fit_score + total_delta))
                ranked.major_score = round(
                    ranked.base_quality_score * W_BASE_QUALITY +
                    ranked.context_fit_score * W_CONTEXT_FIT,
                    2,
                )
                result.trace.append(
                    f"operator_boost: cluster={cluster.cluster_id} delta={total_delta:+.1f} "
                    f"new_score={ranked.major_score:.1f}"
                )

        result.all_ranked.append(ranked)

    # 6. 排序
    # S 级且 default_selected=True 的优先，然后按分数排
    result.all_ranked.sort(key=lambda r: (
        r.precheck_status == "pass",  # pass 优先
        r.level == "S",               # S 级优先
        r.major_score,                # 分高优先
    ), reverse=True)

    # 7. 按容量贪心选取 + E4: explain
    used = 0.0
    for ranked in result.all_ranked:
        if ranked.precheck_status == "fail":
            ranked.selection_reason = "precheck_failed"
            ranked.explain = MajorExplain(
                why_not_selected=f"{ranked.name_zh} 未通过前置风险检查(precheck_failed)",
                fallback_hint="可在行程前重新检查该活动的开放状态",
            )
            continue
        if used + ranked.capacity_units > capacity + 0.01:
            ranked.selection_reason = "over_capacity"
            ranked.explain = MajorExplain(
                why_not_selected=f"{ranked.name_zh} 因容量不足未入选"
                                 f"(需 {ranked.capacity_units}, 剩余 {capacity - used:.1f})",
                expected_tradeoff=f"如需加入需移除其他活动释放 {ranked.capacity_units} 容量单位",
            )
            continue
        ranked.selected = True
        ranked.selection_reason = "selected"
        ranked.explain = MajorExplain(
            why_selected=f"{ranked.name_zh}: "
                         f"base_quality={ranked.base_quality_score:.0f}, "
                         f"context_fit={ranked.context_fit_score:.0f}, "
                         f"综合={ranked.major_score:.1f}",
            expected_tradeoff=f"占用 {ranked.capacity_units} 容量单位",
        )
        used += ranked.capacity_units
        result.selected_majors.append(ranked)

    result.capacity_used = used
    result.trace.append(
        f"selected {len(result.selected_majors)} majors, "
        f"capacity {used:.1f}/{capacity:.1f}"
    )

    return result


# ── 评分 ──────────────────────────────────────────────────────────────────────

def _score_cluster(
    cluster: ActivityCluster,
    anchor_entity_ids: list[uuid.UUID],
    base_scores: dict[uuid.UUID, float],
    context_scores: dict[uuid.UUID, float],
    precheck_failed: set[uuid.UUID],
    profile: TripProfile,
) -> RankedMajor:
    """对单个活动簇打分。"""
    ranked = RankedMajor(
        cluster_id=cluster.cluster_id,
        name_zh=cluster.name_zh,
        level=cluster.level or "A",
        default_duration=cluster.default_duration or "full_day",
        primary_corridor=cluster.primary_corridor or "",
        anchor_entity_ids=anchor_entity_ids,
    )

    # 容量单位
    dur = (cluster.default_duration or "full_day").lower()
    if "half" in dur or "quarter" in dur:
        ranked.capacity_units = 0.5
    else:
        ranked.capacity_units = 1.0

    # precheck 状态：锚点实体中有任何一个被 precheck 拦截则标记
    if anchor_entity_ids:
        failed_anchors = set(anchor_entity_ids) & precheck_failed
        if failed_anchors:
            ranked.precheck_status = "fail"
        elif any(eid in precheck_failed for eid in anchor_entity_ids):
            ranked.precheck_status = "warn"

    # base_quality: 取锚点实体的最高分（代表簇的品质上界）
    if anchor_entity_ids:
        bq_scores = [base_scores.get(eid, 50.0) for eid in anchor_entity_ids]
        ranked.base_quality_score = max(bq_scores) if bq_scores else 50.0
    else:
        # 无锚点实体，用等级推断
        ranked.base_quality_score = {"S": 85.0, "A": 70.0, "B": 55.0}.get(cluster.level, 50.0)

    # context_fit: 取锚点实体 context 分的加权平均
    if anchor_entity_ids:
        cf_scores = [context_scores.get(eid, 50.0) for eid in anchor_entity_ids]
        ranked.context_fit_score = sum(cf_scores) / len(cf_scores)
    else:
        ranked.context_fit_score = 50.0

    # 画像加成
    profile_fit_tags = set(t.lower() for t in (cluster.profile_fit or []))
    user_tags = set(t.lower() for t in (profile.must_have_tags or []))
    if profile_fit_tags and user_tags:
        overlap = len(profile_fit_tags & user_tags)
        if overlap > 0:
            ranked.context_fit_score = min(100.0, ranked.context_fit_score + overlap * 5)

    # party_type 匹配
    party = (profile.party_type or "").lower()
    if party in profile_fit_tags:
        ranked.context_fit_score = min(100.0, ranked.context_fit_score + 8)

    # 归一化到 0-100
    ranked.base_quality_score = min(100.0, max(0.0, ranked.base_quality_score))
    ranked.context_fit_score = min(100.0, max(0.0, ranked.context_fit_score))

    # 总分
    ranked.major_score = round(
        ranked.base_quality_score * W_BASE_QUALITY +
        ranked.context_fit_score * W_CONTEXT_FIT,
        2,
    )

    return ranked


# ── 数据加载 ──────────────────────────────────────────────────────────────────

async def _load_base_quality_scores(
    session: AsyncSession,
    entity_ids: list[uuid.UUID],
) -> dict[uuid.UUID, float]:
    """从 entity_scores 加载基础品质分。"""
    if not entity_ids:
        return {}
    q = await session.execute(
        select(EntityScore).where(
            and_(
                EntityScore.entity_id.in_(entity_ids),
                EntityScore.score_profile == "general",
            )
        )
    )
    return {
        s.entity_id: float(s.final_score or s.base_score or 50)
        for s in q.scalars().all()
    }


async def _load_context_fit_scores(
    session: AsyncSession,
    entity_ids: list[uuid.UUID],
    profile: TripProfile,
) -> dict[uuid.UUID, float]:
    """从 entity_soft_scores 加载上下文适配分。"""
    if not entity_ids:
        return {}
    q = await session.execute(
        select(EntitySoftScore).where(
            EntitySoftScore.entity_id.in_(entity_ids),
        )
    )
    # 取 overall_score 或计算均值
    result: dict[uuid.UUID, float] = {}
    for ss in q.scalars().all():
        # EntitySoftScore 有多个维度分，取综合
        overall = getattr(ss, "overall_score", None)
        if overall is not None:
            result[ss.entity_id] = float(overall)
        else:
            # fallback: 取所有维度的均值
            dims = getattr(ss, "dimension_scores", None) or {}
            if dims:
                vals = [v for v in dims.values() if isinstance(v, (int, float))]
                result[ss.entity_id] = sum(vals) / len(vals) if vals else 50.0
            else:
                result[ss.entity_id] = 50.0

    return result

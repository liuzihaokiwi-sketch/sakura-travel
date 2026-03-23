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
from app.domains.planning.constraint_compiler import PlanningConstraints

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
    capacity_units: float = 1.0           # 0.5 或 1.0（兼容保留，展示用）
    default_duration: str = "full_day"    # 展示标签，内部调度用 activity_load_minutes
    primary_corridor: str = ""
    anchor_entity_ids: list[uuid.UUID] = field(default_factory=list)
    selected: bool = False
    selection_reason: str = ""
    explain: MajorExplain = field(default_factory=MajorExplain)
    # ── 分钟级时长（内部编排）────────────────────────────────────────────────
    # base 值：core_visit + queue_buffer（不含 photo/meal，由日骨架按用户画像叠加）
    activity_load_minutes: int = 0        # 标准用户的活动占用分钟数（已含排队缓冲）
    core_visit_minutes: int = 0           # 纯游玩分钟（不含任何缓冲）
    photo_buffer_minutes: int = 0         # 摄影用户额外耗时
    fatigue_weight: float = 1.0           # 体力消耗系数，带老人/小孩时做折扣用
    queue_risk_level: str = "low"         # none / low / medium / high


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
    constraints: "PlanningConstraints | None" = None,
) -> MajorRankingResult:
    """
    对通过资格过滤的活动簇进行排序，按容量上限选出主要活动。
    如果传入 override_resolver，会在 context_fit 分上叠加运营干预的 weight_delta。
    如果传入 constraints，使用编译后的约束（硬约束 + 软偏好）代替直接读 profile。
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
            constraints=constraints,
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
    # 优先级：precheck pass > S+default_selected（必去）> 其余按分数
    # S+default_selected 代表"必去经典线"，分数再高的 A 级也不应排前面
    cluster_map: dict[str, ActivityCluster] = {c.cluster_id: c for c in clusters}

    # must_have_tags 只做软偏好 boost；这里仅用于判断 theme_park 请求
    user_tags_set = set(t.lower() for t in (profile.must_have_tags or []))
    has_theme_park_request = "theme_park" in user_tags_set

    def _sort_key(r: RankedMajor):
        c = cluster_map.get(r.cluster_id)
        is_must_go = bool(c and c.default_selected and (c.level or "") == "S")
        # 用户明确要主题公园时，USJ 类 cluster 也视为必去
        if has_theme_park_request and c:
            fits = set(t.lower() for t in (c.profile_fit or []))
            if "theme_park" in fits and (c.level or "") == "S":
                is_must_go = True
        return (
            r.precheck_status == "pass",  # pass 优先
            is_must_go,                   # S+default/用户指定 必去优先
            r.major_score,                # 分高优先
        )

    result.all_ranked.sort(key=_sort_key, reverse=True)

    # 7. MMR 多样性约束：同走廊最多入选 N 个（普通用户 N=2，小众用户 N=1）
    # 防止同一走廊 cluster 吃掉全部容量（如 higashiyama + arashiyama 各有多个簇）
    user_tags_for_mmr = set(t.lower() for t in (profile.must_have_tags or []))
    NICHE_MMR_TAGS = {"architecture","zen","sakura","autumn","niche","gourmet","history","family_child"}
    is_niche_for_mmr = bool(user_tags_for_mmr & NICHE_MMR_TAGS)
    max_per_corridor = 1 if is_niche_for_mmr else 2
    corridor_count: dict[str, int] = {}

    # 8. 按容量贪心选取 + MMR 走廊去重 + E4: explain
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
        # MMR：S+default 的经典线不受走廊上限限制（必须进）
        c_obj = cluster_map.get(ranked.cluster_id)
        is_must = bool(c_obj and c_obj.default_selected and (c_obj.level or "") == "S")
        corr = ranked.primary_corridor or "_none_"
        if not is_must and corridor_count.get(corr, 0) >= max_per_corridor:
            ranked.selection_reason = "mmr_corridor_limit"
            ranked.explain = MajorExplain(
                why_not_selected=f"{ranked.name_zh} 被 MMR 走廊去重排除（{corr} 已选 {max_per_corridor} 个）",
                fallback_hint="可延长行程天数或调整偏好以包含此线路",
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
        corridor_count[corr] = corridor_count.get(corr, 0) + 1
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
    constraints: "PlanningConstraints | None" = None,
) -> RankedMajor:
    """对单个活动簇打分。优先使用 constraints 中的编译约束。"""
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

    profile_fit_tags = set(t.lower() for t in (cluster.profile_fit or []))
    # ── constraints-aware: 优先从编译约束读取 ──
    user_tags = set(t.lower() for t in (profile.must_have_tags or []))
    party = (profile.party_type or "").lower()
    user_pace = (profile.pace or "moderate").lower()
    avoid_tags = constraints.blocked_tags if constraints else set(t.lower() for t in (profile.avoid_tags or []))

    # blocked_clusters 硬过滤：cluster_id 在黑名单中直接归零
    if constraints and constraints.blocked_clusters:
        if cluster.cluster_id in constraints.blocked_clusters:
            ranked.context_fit_score = 0.0
            ranked.base_quality_score = 0.0
            if constraints:
                constraints.record_consumption(
                    "blocked_clusters", "ranker", "hard_block",
                    f"cluster {cluster.cluster_id} zeroed",
                )
            return ranked

    # ── 是否是小众/专属 profile ──────────────────────────────────────────────
    # 用户画像里含有明确的专属偏好标签（非通用旅游者）
    NICHE_PROFILE_TAGS = {
        "architecture", "zen", "sakura", "autumn", "foliage", "wisteria",
        "niche", "gourmet", "sake", "design", "art", "history",
        "family_child", "elderly", "ramen", "night", "romantic",
    }
    user_niche_tags = user_tags & NICHE_PROFILE_TAGS
    is_niche_user = len(user_niche_tags) >= 1

    # ── P1: default_selected 核心簇保底加分 ──────────────────────────────────
    # 仅对"通用旅游者"保留强加分；小众用户降低热门经典线的霸榜力
    if cluster.default_selected and cluster.level == "S":
        if is_niche_user:
            # 小众用户：热门线仅加 +10（保底不消失，但不再统治）
            ranked.context_fit_score = min(100.0, ranked.context_fit_score + 10)
        else:
            ranked.context_fit_score = min(100.0, ranked.context_fit_score + 25)
    elif cluster.default_selected and cluster.level == "A":
        ranked.context_fit_score = min(100.0, ranked.context_fit_score + 10)

    # ── P2: 兴趣精准匹配加分（profile_match_bonus）──────────────────────────
    # 专属 cluster 的 must_have_tags 与用户 tags 精准命中 → 大幅加分
    cluster_must_tags = set(t.lower() for t in (cluster.must_have_tags or []))
    if cluster_must_tags and user_tags:
        must_overlap = cluster_must_tags & user_tags
        if must_overlap:
            # 精准命中：每个必需 tag 加 15 分（比普通 tag 命中更强）
            ranked.context_fit_score = min(100.0, ranked.context_fit_score + len(must_overlap) * 15)

    # 普通 profile_fit 命中加分
    if profile_fit_tags and user_tags:
        overlap = len(profile_fit_tags & user_tags)
        if overlap > 0:
            ranked.context_fit_score = min(100.0, ranked.context_fit_score + overlap * 6)

    # party_type 匹配
    if party in profile_fit_tags:
        ranked.context_fit_score = min(100.0, ranked.context_fit_score + 8)

    # ── P3: upgrade_triggers ────────────────────────────────────────────────
    triggers = cluster.upgrade_triggers or {}
    trigger_tags = set(t.lower() for t in (triggers.get("tags") or []))
    trigger_parties = set(t.lower() for t in (triggers.get("party_types") or []))
    if trigger_tags and user_tags and (trigger_tags & user_tags):
        boost = len(trigger_tags & user_tags) * 12
        ranked.context_fit_score = min(100.0, ranked.context_fit_score + boost)
    if party and trigger_parties and party in trigger_parties:
        ranked.context_fit_score = min(100.0, ranked.context_fit_score + 10)

    # ── P4: 通用热门线对小众用户的惩罚（generic_cluster_penalty）──────────
    # 没有 must_have_tags 或 must_have_tags 为通用 tag 的簇，
    # 在小众 profile 下扣分，避免热门线吃光容量
    GENERIC_CLUSTERS = {
        "kyo_higashiyama_gion_classic", "kyo_arashiyama_sagano",
        "kyo_fushimi_inari", "odc_dotonbori_food", "osa_dotonbori_minami_food",
    }
    if is_niche_user and cluster.cluster_id in GENERIC_CLUSTERS:
        # 小众用户：每个专属 niche tag 扣 5 分，最多扣 20
        penalty = min(20.0, len(user_niche_tags) * 5)
        ranked.context_fit_score = max(0.0, ranked.context_fit_score - penalty)

    # ── P5: 画像不匹配时降权/排除 ───────────────────────────────────────────
    if user_pace == "relaxed" and "theme_park" in profile_fit_tags:
        if "theme_park" not in user_tags:
            ranked.context_fit_score = 0.0
            ranked.base_quality_score = max(0.0, ranked.base_quality_score - 40)

    # ── P5b: party_block_tags 硬约束（从 constraints 获取）──────────────────
    if constraints and constraints.party_block_tags and profile_fit_tags:
        party_block_hit = constraints.party_block_tags & profile_fit_tags
        if party_block_hit:
            ranked.context_fit_score = 0.0
            ranked.base_quality_score = max(0.0, ranked.base_quality_score - 40)
            logger.debug(
                "cluster %s blocked by party_block_tags %s",
                cluster.cluster_id, sorted(party_block_hit),
            )

    # ── P5c: party_fit_penalty（从 constraints 获取）────────────────────────
    if constraints and constraints.party_fit_penalty > 0:
        # 不匹配 party 的 cluster 扣分（profile_fit 里没有 party_type）
        if party and party not in profile_fit_tags:
            ranked.context_fit_score = max(
                0.0, ranked.context_fit_score - constraints.party_fit_penalty
            )

    # ── P5d: preferred_tags_boost（从 constraints 获取）─────────────────────
    if constraints and constraints.preferred_tags_boost and profile_fit_tags:
        for tag, boost_val in constraints.preferred_tags_boost.items():
            if tag in profile_fit_tags:
                ranked.context_fit_score = min(100.0, ranked.context_fit_score + boost_val)

    # avoid_tags 命中 → 大幅降权
    if avoid_tags and profile_fit_tags:
        avoid_overlap = len(avoid_tags & profile_fit_tags)
        if avoid_overlap > 0:
            ranked.context_fit_score = max(0.0, ranked.context_fit_score - avoid_overlap * 20)

    # 用户拒绝实体（reject_entity_ids / avoid_pois）中包含簇的锚点 → 直接降权
    reject_pois = set((getattr(profile, "reject_entity_ids", None) or []))
    if reject_pois and anchor_entity_ids:
        hit = reject_pois & set(str(e) for e in anchor_entity_ids)
        if hit:
            ranked.context_fit_score = 0.0
            ranked.base_quality_score = max(0.0, ranked.base_quality_score - 50)

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

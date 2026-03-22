"""
eligibility_gate.py — 资格过滤门（Phase 1 前置过滤）

在城市圈选择和主要活动排序之前，清掉已知不能参与本次行程的实体/活动簇。
这是 pass/fail 门控，不打分。

过滤规则 (EG-xxx)：
  EG-001  永久关闭 / 长期停业
  EG-002  不在本次候选城市圈的城市范围内
  EG-003  超预算上限（如果有明确上限）
  EG-004  同行条件明确不符（如轮椅不可达、有小孩但是酒吧）
  EG-005  季节不对（如冬季选了夏季限定活动簇）
  EG-006  用户明确 avoid 的标签命中
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional, Sequence

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase, EntityTag
from app.db.models.city_circles import ActivityCluster, CircleEntityRole
from app.db.models.soft_rules import EntityOperatingFact

logger = logging.getLogger(__name__)


# ── 过滤结果 ──────────────────────────────────────────────────────────────────

@dataclass
class GateVerdict:
    entity_id: uuid.UUID
    passed: bool
    fail_codes: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.passed


@dataclass
class ClusterGateVerdict:
    cluster_id: str
    passed: bool
    fail_codes: list[str] = field(default_factory=list)
    failed_entity_count: int = 0
    total_entity_count: int = 0


@dataclass
class EligibilityResult:
    """完整过滤结果，包含实体级和簇级。"""
    entity_verdicts: dict[uuid.UUID, GateVerdict] = field(default_factory=dict)
    cluster_verdicts: dict[str, ClusterGateVerdict] = field(default_factory=dict)
    total_filtered: int = 0
    trace: list[str] = field(default_factory=list)

    @property
    def passed_entity_ids(self) -> set[uuid.UUID]:
        return {eid for eid, v in self.entity_verdicts.items() if v.passed}

    @property
    def passed_cluster_ids(self) -> set[str]:
        return {cid for cid, v in self.cluster_verdicts.items() if v.passed}


# ── 用户画像上下文 ────────────────────────────────────────────────────────────

@dataclass
class EligibilityContext:
    """从 TripProfile 提取的过滤所需信号。"""
    circle_id: str
    city_codes: list[str]               # 圈内所有城市（base + extension）
    avoid_tags: list[str] = field(default_factory=list)
    party_type: str = "couple"
    has_elderly: bool = False
    has_children: bool = False
    children_ages: list[int] = field(default_factory=list)
    budget_total_cny: Optional[int] = None
    travel_month: Optional[int] = None   # 1-12, 用于季节判断
    wheelchair_needed: bool = False


# ── 季节映射 ──────────────────────────────────────────────────────────────────

_MONTH_TO_SEASON: dict[int, str] = {
    1: "winter", 2: "winter", 3: "spring", 4: "spring",
    5: "spring", 6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn", 12: "winter",
}


# ── 核心过滤逻辑 ──────────────────────────────────────────────────────────────

async def run_eligibility_gate(
    session: AsyncSession,
    ctx: EligibilityContext,
    override_resolver: "OverrideResolver | None" = None,
) -> EligibilityResult:
    """
    对指定城市圈内的所有活动簇和关联实体执行资格过滤。
    如果传入 override_resolver，会额外应用运营干预（block）。

    Returns:
        EligibilityResult 包含每个实体和簇的 pass/fail 判定。
    """
    result = EligibilityResult()

    # 1. 加载城市圈内所有活动簇
    clusters_q = await session.execute(
        select(ActivityCluster).where(
            and_(
                ActivityCluster.circle_id == ctx.circle_id,
                ActivityCluster.is_active == True,
            )
        )
    )
    clusters = clusters_q.scalars().all()

    if not clusters:
        result.trace.append(f"circle={ctx.circle_id} 无活跃活动簇")
        return result

    cluster_ids = [c.cluster_id for c in clusters]

    # 2. 加载所有角色映射 + 关联实体
    roles_q = await session.execute(
        select(CircleEntityRole).where(
            CircleEntityRole.circle_id == ctx.circle_id
        )
    )
    roles = roles_q.scalars().all()
    entity_ids = list({r.entity_id for r in roles})

    if not entity_ids:
        result.trace.append(f"circle={ctx.circle_id} 无关联实体")
        return result

    # 3. 批量加载实体
    entities_q = await session.execute(
        select(EntityBase).where(EntityBase.entity_id.in_(entity_ids))
    )
    entity_map: dict[uuid.UUID, EntityBase] = {
        e.entity_id: e for e in entities_q.scalars().all()
    }

    # 4. 批量加载实体标签（用于 avoid 检查）
    tags_q = await session.execute(
        select(EntityTag).where(
            EntityTag.entity_id.in_(entity_ids),
            EntityTag.tag_namespace.in_(["category", "theme", "audience"]),
        )
    )
    entity_tags: dict[uuid.UUID, set[str]] = {}
    for tag in tags_q.scalars().all():
        entity_tags.setdefault(tag.entity_id, set()).add(
            tag.tag_value.lower() if tag.tag_value else ""
        )

    # 5. 批量加载运营事实（用于永久关闭检查）
    facts_q = await session.execute(
        select(EntityOperatingFact).where(
            EntityOperatingFact.entity_id.in_(entity_ids)
        )
    )
    entity_facts: dict[uuid.UUID, list] = {}
    for fact in facts_q.scalars().all():
        entity_facts.setdefault(fact.entity_id, []).append(fact)

    # 5b. 从 OverrideResolver 批量获取被 block 的 entity_id（L4-02 接入）
    operator_blocked_ids: set[str] = set()
    if override_resolver is not None:
        try:
            operator_blocked_ids = override_resolver.get_all_blocked_entity_ids()
            if operator_blocked_ids:
                result.trace.append(
                    f"operator_block: {len(operator_blocked_ids)} 个实体被运营干预屏蔽"
                )
        except Exception as exc:
            logger.warning("[EligibilityGate] OverrideResolver 查询失败（忽略）: %s", exc)

    # 6. 逐实体过滤
    for eid in entity_ids:
        entity = entity_map.get(eid)
        verdict = _check_entity(entity, eid, ctx, entity_tags.get(eid, set()),
                                entity_facts.get(eid, []))

        # L4-02: 运营干预 block 覆盖（优先级最高）
        if not verdict.passed is False and str(eid) in operator_blocked_ids:
            verdict.passed = False
            verdict.fail_codes.append("EG-OVR_OPERATOR_BLOCK")

        result.entity_verdicts[eid] = verdict
        if not verdict.passed:
            result.total_filtered += 1

    # 7. 簇级过滤——基于实体过滤结果 + 簇自身属性
    cluster_map = {c.cluster_id: c for c in clusters}
    # 构建 cluster → entity_ids 映射
    cluster_entities: dict[str, list[uuid.UUID]] = {}
    for role in roles:
        if role.cluster_id:
            cluster_entities.setdefault(role.cluster_id, []).append(role.entity_id)

    for cid in cluster_ids:
        cluster = cluster_map[cid]
        c_eids = cluster_entities.get(cid, [])
        c_verdict = _check_cluster(
            cluster, c_eids, result.entity_verdicts, ctx,
        )
        result.cluster_verdicts[cid] = c_verdict

    passed_clusters = sum(1 for v in result.cluster_verdicts.values() if v.passed)
    result.trace.append(
        f"eligibility_gate: {len(entity_ids)} entities checked, "
        f"{result.total_filtered} filtered; "
        f"{passed_clusters}/{len(cluster_ids)} clusters passed"
    )

    return result


# ── 实体级检查 ────────────────────────────────────────────────────────────────

def _check_entity(
    entity: Optional[EntityBase],
    entity_id: uuid.UUID,
    ctx: EligibilityContext,
    tags: set[str],
    facts: list,
) -> GateVerdict:
    """对单个实体执行 EG-001~006 检查。"""
    fails: list[str] = []

    if entity is None:
        return GateVerdict(entity_id=entity_id, passed=False, fail_codes=["EG-000_NOT_FOUND"])

    # EG-001: 永久关闭 / 长期停业
    if not entity.is_active:
        fails.append("EG-001_INACTIVE")
    for fact in facts:
        status = (fact.fact_value or "").lower() if hasattr(fact, "fact_value") else ""
        fact_key = (fact.fact_key or "").lower() if hasattr(fact, "fact_key") else ""
        if fact_key == "status" and status in ("permanently_closed", "long_term_closed"):
            fails.append("EG-001_CLOSED")
            break

    # EG-002: 城市范围
    if entity.city_code and entity.city_code not in ctx.city_codes:
        fails.append("EG-002_OUT_OF_CIRCLE")

    # EG-003: 超预算（粗略检查，只对酒店/餐厅类有意义）
    # 此处暂不实现细粒度预算检查，因为需要 snapshot 支撑

    # EG-004: 同行条件
    if ctx.wheelchair_needed and "not_wheelchair_accessible" in tags:
        fails.append("EG-004_ACCESSIBILITY")
    if ctx.has_children and ctx.children_ages:
        min_age = min(ctx.children_ages) if ctx.children_ages else 99
        if "adults_only" in tags or "bar" in tags or "nightclub" in tags:
            if min_age < 18:
                fails.append("EG-004_CHILD_UNSAFE")
    if ctx.has_elderly and "extreme_physical" in tags:
        fails.append("EG-004_ELDERLY_UNSAFE")

    # EG-005: 季节检查（entity 级别的季节标签）
    if ctx.travel_month:
        season = _MONTH_TO_SEASON.get(ctx.travel_month)
        if "seasonal_only" in tags and season:
            # 检查实体的 best_season 标签
            season_tags = {t for t in tags if t.startswith("season:")}
            if season_tags and f"season:{season}" not in season_tags:
                fails.append("EG-005_SEASON_MISMATCH")

    # EG-006: 用户 avoid 标签
    if ctx.avoid_tags:
        avoid_set = {t.lower() for t in ctx.avoid_tags}
        hit = tags & avoid_set
        if hit:
            fails.append(f"EG-006_AVOID_TAG:{','.join(hit)}")

    return GateVerdict(entity_id=entity_id, passed=len(fails) == 0, fail_codes=fails)


# ── 簇级检查 ──────────────────────────────────────────────────────────────────

def _check_cluster(
    cluster: ActivityCluster,
    entity_ids: list[uuid.UUID],
    entity_verdicts: dict[uuid.UUID, GateVerdict],
    ctx: EligibilityContext,
) -> ClusterGateVerdict:
    """簇级过滤：锚点实体被过滤则整个簇不可用，非锚点容忍部分损失。"""
    fails: list[str] = []
    total = len(entity_ids)
    failed_count = sum(1 for eid in entity_ids if not entity_verdicts.get(eid, GateVerdict(eid, True)).passed)

    # 季节检查
    if ctx.travel_month:
        season = _MONTH_TO_SEASON.get(ctx.travel_month, "")
        seasonality = cluster.seasonality or []
        if seasonality and "all_year" not in seasonality and season not in seasonality:
            fails.append("EG-005_CLUSTER_SEASON")

    # 如果超过 50% 的实体被过滤，整个簇不可用
    if total > 0 and failed_count / total > 0.5:
        fails.append("EG-007_MAJORITY_FILTERED")

    return ClusterGateVerdict(
        cluster_id=cluster.cluster_id,
        passed=len(fails) == 0,
        fail_codes=fails,
        failed_entity_count=failed_count,
        total_entity_count=total,
    )

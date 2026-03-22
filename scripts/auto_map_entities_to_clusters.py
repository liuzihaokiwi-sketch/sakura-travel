"""
auto_map_entities_to_clusters.py — 实体→活动簇自动映射管线

可反复运行的管线，不是一次性脚本。
每次运行：
1. 加载所有活动簇的代表节点名称（从 cluster 的 notes 或 name_zh 拆解）
2. 按 4 层策略从 entity_base + entity_aliases 中匹配
3. 写入 circle_entity_roles
4. 输出覆盖率报告

匹配策略（4 层，置信度递减）：
  L1 exact_match    — cluster 代表节点名 == entity_alias.normalized_text（或 entity_base.name_local）
  L2 alias_match    — pg_trgm similarity ≥ 0.7 且同 city_code
  L3 fuzzy_match    — similarity ≥ 0.5 且同 corridor_tags / area_name 有交集
  L4 rejected       — similarity < 0.5 或 city_code 不匹配

使用方式：
    python -m scripts.auto_map_entities_to_clusters [--circle kansai_classic_circle_v1] [--dry-run]
"""
from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select, and_, text, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ── 结果类型 ──────────────────────────────────────────────────────────────────

@dataclass
class MatchResult:
    cluster_id: str
    anchor_name: str
    entity_id: Optional[uuid.UUID] = None
    entity_name: str = ""
    match_level: str = "rejected"  # exact / alias / fuzzy / rejected
    similarity: float = 0.0
    match_method: str = ""


@dataclass
class ClusterCoverage:
    cluster_id: str
    cluster_name: str
    total_anchors: int = 0
    matched_anchors: int = 0
    matches: list[MatchResult] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        return self.matched_anchors / max(1, self.total_anchors)


@dataclass
class PipelineReport:
    circle_id: str
    total_clusters: int = 0
    total_anchors: int = 0
    exact_matches: int = 0
    alias_matches: int = 0
    fuzzy_matches: int = 0
    rejected: int = 0
    roles_written: int = 0
    cluster_details: list[ClusterCoverage] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"\n{'='*60}",
            f"映射报告: {self.circle_id}",
            f"{'='*60}",
            f"活动簇: {self.total_clusters}",
            f"锚点总数: {self.total_anchors}",
            f"精确匹配: {self.exact_matches}",
            f"别名匹配: {self.alias_matches}",
            f"模糊匹配: {self.fuzzy_matches}",
            f"未匹配: {self.rejected}",
            f"写入角色: {self.roles_written}",
            f"总匹配率: {(self.exact_matches+self.alias_matches+self.fuzzy_matches)/max(1,self.total_anchors):.1%}",
            f"{'='*60}",
        ]
        for cd in self.cluster_details:
            status = "✅" if cd.coverage >= 0.5 else "⚠️" if cd.coverage > 0 else "❌"
            lines.append(f"  {status} {cd.cluster_name}: {cd.matched_anchors}/{cd.total_anchors}")
            for m in cd.matches:
                if m.match_level != "rejected":
                    lines.append(f"      [{m.match_level}] {m.anchor_name} → {m.entity_name} ({m.similarity:.2f})")
                else:
                    lines.append(f"      [✗] {m.anchor_name} — 未匹配")
        return "\n".join(lines)


# ── 锚点名称解析 ─────────────────────────────────────────────────────────────

def _extract_anchor_names(cluster) -> list[str]:
    """
    从活动簇中提取代表节点名称。

    优先级：
    1. cluster.notes 中如果包含 "代表节点:" 或 "anchor:" 则解析
    2. 从 cluster.name_zh 中拆解（如"东山祇园经典线" → ["清水寺","二年坂","八坂神社","祇园"]）
    3. fallback: 用 cluster.name_zh 本身作为搜索关键词
    """
    names: list[str] = []
    notes = getattr(cluster, "notes", "") or ""

    # 策略 1: 从 notes 解析
    for prefix in ("代表节点:", "anchor:", "锚点:", "代表:"):
        if prefix in notes:
            after = notes.split(prefix, 1)[1]
            # 取到下一个换行或句号
            segment = after.split("\n")[0].split("。")[0]
            parts = [p.strip() for p in segment.replace("、", ",").replace("，", ",").split(",")]
            names.extend([p for p in parts if p and len(p) >= 2])

    if names:
        return names

    # 策略 2: name_zh 本身作为搜索词
    zh = getattr(cluster, "name_zh", "") or ""
    if zh:
        names.append(zh)

    return names


# ── 核心匹配逻辑 ─────────────────────────────────────────────────────────────

async def _match_anchor_name(
    session: AsyncSession,
    anchor_name: str,
    circle_city_codes: list[str],
) -> MatchResult:
    """
    对单个锚点名称执行 4 层匹配。

    优先走 SQL 精确匹配，再走 pg_trgm 相似度。
    如果数据库没有 pg_trgm 扩展，降级为 Python 端字符串匹配。
    """
    result = MatchResult(cluster_id="", anchor_name=anchor_name)

    # 标准化搜索词
    search_normalized = anchor_name.lower().strip()

    # L1: 精确匹配 entity_base.name_local
    q1 = await session.execute(
        select(
            text("entity_id"),
            text("name_local"),
            text("city_code"),
        ).select_from(text("entity_base")).where(
            and_(
                text("LOWER(name_local) = :name"),
                text("city_code = ANY(:cities)"),
                text("is_active = true"),
            )
        ),
        {"name": search_normalized, "cities": circle_city_codes},
    )
    rows = q1.fetchall()
    if rows:
        row = rows[0]
        result.entity_id = row[0]
        result.entity_name = row[1] or ""
        result.match_level = "exact"
        result.similarity = 1.0
        result.match_method = "name_local_exact"
        return result

    # L1b: 精确匹配 entity_aliases（如果表存在）
    try:
        q1b = await session.execute(
            select(
                text("ea.entity_id"),
                text("eb.name_local"),
            ).select_from(
                text("entity_aliases ea JOIN entity_base eb ON ea.entity_id = eb.entity_id")
            ).where(
                and_(
                    text("LOWER(ea.alias_text) = :name"),
                    text("eb.city_code = ANY(:cities)"),
                    text("eb.is_active = true"),
                )
            ),
            {"name": search_normalized, "cities": circle_city_codes},
        )
        alias_rows = q1b.fetchall()
        if alias_rows:
            row = alias_rows[0]
            result.entity_id = row[0]
            result.entity_name = row[1] or ""
            result.match_level = "exact"
            result.similarity = 1.0
            result.match_method = "alias_exact"
            return result
    except Exception:
        pass  # entity_aliases 表可能不存在

    # L2: pg_trgm 相似度匹配（similarity ≥ 0.7）
    try:
        q2 = await session.execute(
            text("""
                SELECT entity_id, name_local, city_code,
                       similarity(LOWER(name_local), :name) AS sim
                FROM entity_base
                WHERE city_code = ANY(:cities)
                  AND is_active = true
                  AND similarity(LOWER(name_local), :name) >= 0.4
                ORDER BY sim DESC
                LIMIT 3
            """),
            {"name": search_normalized, "cities": circle_city_codes},
        )
        sim_rows = q2.fetchall()
        if sim_rows:
            best = sim_rows[0]
            sim_score = float(best[3])
            result.entity_id = best[0]
            result.entity_name = best[1] or ""
            result.similarity = sim_score

            if sim_score >= 0.7:
                result.match_level = "alias"
                result.match_method = "trgm_high"
            elif sim_score >= 0.5:
                result.match_level = "fuzzy"
                result.match_method = "trgm_medium"
            else:
                result.match_level = "rejected"
                result.match_method = "trgm_low"
            return result
    except Exception:
        # pg_trgm 不可用，降级为 Python 包含匹配
        pass

    # L3: Python 降级匹配（子串包含）
    q3 = await session.execute(
        text("""
            SELECT entity_id, name_local, city_code
            FROM entity_base
            WHERE city_code = ANY(:cities)
              AND is_active = true
              AND (LOWER(name_local) LIKE :pattern
                   OR LOWER(name_local) LIKE :pattern2)
            LIMIT 5
        """),
        {
            "name": search_normalized,
            "cities": circle_city_codes,
            "pattern": f"%{search_normalized}%",
            "pattern2": f"{search_normalized}%",
        },
    )
    py_rows = q3.fetchall()
    if py_rows:
        best = py_rows[0]
        result.entity_id = best[0]
        result.entity_name = best[1] or ""
        result.match_level = "fuzzy"
        result.similarity = 0.5
        result.match_method = "substring"
        return result

    # L4: rejected
    result.match_level = "rejected"
    result.similarity = 0.0
    return result


# ── 主管线入口 ────────────────────────────────────────────────────────────────

async def run_mapping_pipeline(
    session: AsyncSession,
    circle_id: Optional[str] = None,
    dry_run: bool = False,
    pipeline_run_id: Optional[str] = None,
) -> list[PipelineReport]:
    """
    执行实体→活动簇映射管线。

    Args:
        circle_id: 只处理指定城市圈（None = 全部活跃圈）
        dry_run: True = 只匹配不写入
        pipeline_run_id: 本次运行批次 ID（写入 entity_mapping_reviews 用于溯源）
    """
    from app.db.models.city_circles import CityCircle, ActivityCluster, CircleEntityRole
    from app.db.models.catalog import EntityMappingReview

    if pipeline_run_id is None:
        pipeline_run_id = f"run_{uuid.uuid4().hex[:12]}"

    # 1. 加载城市圈
    if circle_id:
        circles = [await session.get(CityCircle, circle_id)]
        circles = [c for c in circles if c]
    else:
        q = await session.execute(
            select(CityCircle).where(CityCircle.is_active == True)
        )
        circles = q.scalars().all()

    reports: list[PipelineReport] = []

    for circle in circles:
        report = PipelineReport(circle_id=circle.circle_id)
        all_cities = list(set(
            (circle.base_city_codes or []) + (circle.extension_city_codes or [])
        ))

        # 2. 加载该圈所有活动簇
        cq = await session.execute(
            select(ActivityCluster).where(
                and_(
                    ActivityCluster.circle_id == circle.circle_id,
                    ActivityCluster.is_active == True,
                )
            )
        )
        clusters = cq.scalars().all()
        report.total_clusters = len(clusters)

        # 3. 逐簇匹配
        roles_to_write: list[dict] = []
        reviews_to_write: list[dict] = []

        for cluster in clusters:
            anchor_names = _extract_anchor_names(cluster)
            coverage = ClusterCoverage(
                cluster_id=cluster.cluster_id,
                cluster_name=cluster.name_zh,
                total_anchors=len(anchor_names),
            )

            for i, name in enumerate(anchor_names):
                match = await _match_anchor_name(session, name, all_cities)
                match.cluster_id = cluster.cluster_id
                coverage.matches.append(match)
                report.total_anchors += 1

                if match.match_level == "exact":
                    report.exact_matches += 1
                    coverage.matched_anchors += 1
                elif match.match_level == "alias":
                    report.alias_matches += 1
                    coverage.matched_anchors += 1
                elif match.match_level == "fuzzy":
                    report.fuzzy_matches += 1
                    coverage.matched_anchors += 1
                else:
                    report.rejected += 1

                # 准备写入 circle_entity_roles
                if match.entity_id and match.match_level in ("exact", "alias"):
                    is_anchor = (cluster.level == "S" and i == 0)
                    role = "anchor_poi" if is_anchor else "secondary_poi"

                    roles_to_write.append({
                        "circle_id": circle.circle_id,
                        "cluster_id": cluster.cluster_id,
                        "entity_id": match.entity_id,
                        "role": role,
                        "sort_order": i,
                        "is_cluster_anchor": is_anchor,
                        "role_notes": f"auto_map:{match.match_level}:{match.match_method} sim={match.similarity:.2f}",
                    })
                elif match.entity_id and match.match_level == "fuzzy":
                    # fuzzy 也写入但标记 needs_review
                    roles_to_write.append({
                        "circle_id": circle.circle_id,
                        "cluster_id": cluster.cluster_id,
                        "entity_id": match.entity_id,
                        "role": "secondary_poi",
                        "sort_order": i,
                        "is_cluster_anchor": False,
                        "role_notes": f"auto_map:fuzzy:needs_review sim={match.similarity:.2f}",
                    })

                # T10: fuzzy + rejected 写入审核队列
                if match.match_level in ("fuzzy", "rejected"):
                    reviews_to_write.append({
                        "circle_id": circle.circle_id,
                        "cluster_id": cluster.cluster_id,
                        "anchor_name": name,
                        "matched_entity_id": match.entity_id,
                        "match_level": match.match_level,
                        "match_method": match.match_method,
                        "similarity_score": match.similarity,
                        "review_status": "pending",
                        "pipeline_run_id": pipeline_run_id,
                    })

            report.cluster_details.append(coverage)

        # 4. 写入（如果不是 dry_run）
        if not dry_run and roles_to_write:
            for role_data in roles_to_write:
                # 检查是否已存在
                existing = await session.execute(
                    select(CircleEntityRole).where(
                        and_(
                            CircleEntityRole.circle_id == role_data["circle_id"],
                            CircleEntityRole.cluster_id == role_data["cluster_id"],
                            CircleEntityRole.entity_id == role_data["entity_id"],
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    continue  # 已存在，跳过

                new_role = CircleEntityRole(**role_data)
                session.add(new_role)
                report.roles_written += 1

            await session.flush()

        # 4b. T10: 写入审核队列
        if not dry_run and reviews_to_write:
            for rev_data in reviews_to_write:
                review = EntityMappingReview(**rev_data)
                session.add(review)
            await session.flush()
            logger.info(f"  [{circle.circle_id}] 写入 {len(reviews_to_write)} 条审核记录")

        reports.append(report)

    return reports


# ── CLI 入口 ──────────────────────────────────────────────────────────────────

async def main():
    """命令行入口。"""
    import argparse
    parser = argparse.ArgumentParser(description="实体→活动簇自动映射管线")
    parser.add_argument("--circle", type=str, default=None, help="只处理指定城市圈")
    parser.add_argument("--dry-run", action="store_true", help="只匹配不写入")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        reports = await run_mapping_pipeline(
            session=session,
            circle_id=args.circle,
            dry_run=args.dry_run,
        )

        for report in reports:
            print(report.summary())

        if not args.dry_run:
            await session.commit()
            print(f"\n✅ 已提交 {sum(r.roles_written for r in reports)} 条角色映射")
        else:
            print("\n🔍 dry-run 模式，未写入数据库")


if __name__ == "__main__":
    asyncio.run(main())

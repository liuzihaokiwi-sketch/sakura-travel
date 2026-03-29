"""
sync_entity_gaps.py — 从 anchor_entities 字段出发：找缺口 + 定向生成 + 绑定

三合一脚本，读取 ActivityCluster.anchor_entities（已由 populate_anchor_entities.py 填充），
然后：
  1. 对比 DB entity_base 找出缺失实体
  2. 用 AI 定向生成缺失实体
  3. 自动建立 circle_entity_roles 绑定

用法：
    # 全量执行（找缺口 + 生成 + 绑定）
    python scripts/sync_entity_gaps.py

    # 只处理某个城市圈
    python scripts/sync_entity_gaps.py --circle kansai_classic_circle

    # 只分析不生成（看缺什么）
    python scripts/sync_entity_gaps.py --analyze-only

    # 只补 S/A 级活动簇的实体
    python scripts/sync_entity_gaps.py --min-level A

    # 限制生成数量（测试用）
    python scripts/sync_entity_gaps.py --limit 10

    # 跳过生成，只做绑定（实体已在 DB 里，只缺 circle_entity_roles）
    python scripts/sync_entity_gaps.py --bind-only
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

REPORT_DIR = Path(__file__).resolve().parents[1] / "data" / "seed" / "cluster_entity_pipeline"


def _normalize_name(text: str) -> str:
    text = (text or "").strip().lower()
    if not text:
        return ""
    return re.sub(r"[\s\-\·\.\(\)（）_/・,，'\"`]+", "", text)


# ── Step 1: 从 anchor_entities 收集需求，对比 DB 找缺口 ─────────────────────

async def analyze_gaps(session, circle_id: str | None, min_level: str) -> dict:
    """读取 anchor_entities，对比 entity_base，返回匹配/缺失分析。"""
    from sqlalchemy import select, text
    from app.db.models.city_circles import ActivityCluster

    level_filter = {"S": ["S"], "A": ["S", "A"], "B": ["S", "A", "B"]}
    allowed_levels = level_filter.get(min_level, ["S", "A", "B"])

    q = select(ActivityCluster).where(
        ActivityCluster.is_active == True,
        ActivityCluster.anchor_entities != None,
        ActivityCluster.level.in_(allowed_levels),
    )
    if circle_id:
        q = q.where(ActivityCluster.circle_id == circle_id)

    result = await session.execute(q)
    clusters = list(result.scalars().all())
    logger.info("加载了 %d 个有 anchor_entities 的活动簇 (level in %s)",
                len(clusters), allowed_levels)

    # 预加载 entity_base 名称索引
    rows = await session.execute(
        text("SELECT entity_id, name_zh, city_code, entity_type FROM entity_base WHERE is_active = true")
    )
    db_entities = rows.fetchall()
    name_index: dict[str, list[dict]] = {}
    for eid, name, city, etype in db_entities:
        if name:
            payload = {
                "entity_id": str(eid), "name_zh": name,
                "city_code": city, "entity_type": etype,
            }
            name_index.setdefault(name.lower(), []).append(payload)
            normalized = _normalize_name(name)
            if normalized and normalized != name.lower():
                name_index.setdefault(normalized, []).append(payload)

    alias_rows = await session.execute(
        text("""
            SELECT ea.alias_text, ea.normalized_text, eb.entity_id, eb.name_zh, eb.city_code, eb.entity_type
            FROM entity_aliases ea
            JOIN entity_base eb ON eb.entity_id = ea.entity_id
            WHERE eb.is_active = true
        """)
    )
    for alias_text, normalized_text, eid, name, city, etype in alias_rows.fetchall():
        payload = {
            "entity_id": str(eid), "name_zh": name,
            "city_code": city, "entity_type": etype,
        }
        for key in (alias_text, normalized_text, _normalize_name(alias_text or "")):
            if key:
                name_index.setdefault(key.lower(), []).append(payload)

    logger.info("DB 中 %d 个活跃实体", len(db_entities))

    matched = []
    missing = []
    cluster_summary = []

    for cluster in clusters:
        entities = cluster.anchor_entities or []
        c_matched = 0
        c_missing = 0

        for ent in entities:
            name = ent.get("name", "")
            city = ent.get("city_code", cluster.city_code)
            etype = ent.get("type", "poi")
            role = ent.get("role", "secondary")

            if not name:
                continue

            found = _find_entity(name, city, name_index)

            if found:
                matched.append({
                    "name": name, "entity_id": found["entity_id"],
                    "entity_name_zh": found["name_zh"],
                    "match_type": found["match_type"],
                    "cluster_id": cluster.cluster_id,
                    "circle_id": cluster.circle_id,
                    "role": role, "type": etype,
                })
                c_matched += 1
            else:
                missing.append({
                    "name": name, "type": etype, "role": role,
                    "city_code": city,
                    "cluster_id": cluster.cluster_id,
                    "circle_id": cluster.circle_id,
                    "cluster_level": cluster.level,
                })
                c_missing += 1

        cluster_summary.append({
            "cluster_id": cluster.cluster_id,
            "level": cluster.level,
            "name_zh": cluster.name_zh,
            "total": len(entities),
            "matched": c_matched,
            "missing": c_missing,
        })

    # 去重 missing（同名+同城市只生成一次）
    seen = set()
    deduped_missing = []
    for m in missing:
        key = (m["name"], m["city_code"])
        if key not in seen:
            seen.add(key)
            # 聚合所有引用该实体的簇
            m["all_cluster_ids"] = [
                x["cluster_id"] for x in missing
                if x["name"] == m["name"] and x["city_code"] == m["city_code"]
            ]
            deduped_missing.append(m)

    # 按优先级排序：S 级簇的 anchor > S 级 secondary > A 级 > B 级
    level_score = {"S": 30, "A": 20, "B": 10}
    role_score = {"anchor": 5, "secondary": 0}
    deduped_missing.sort(key=lambda x: -(
        level_score.get(x["cluster_level"], 0) + role_score.get(x["role"], 0)
    ))

    total = len(matched) + len(deduped_missing)
    return {
        "total_entities_needed": total,
        "matched": len(matched),
        "missing": len(deduped_missing),
        "match_rate": f"{len(matched)/max(1,total):.0%}",
        "matched_list": matched,
        "missing_list": deduped_missing,
        "cluster_summary": cluster_summary,
    }


def _find_entity(name: str, city_code: str, name_index: dict) -> dict | None:
    """在名称索引中查找实体，返回匹配信息或 None。"""
    name_lower = name.lower()
    normalized = _normalize_name(name)

    # L1: 精确匹配
    for key, match_type in ((name_lower, "exact"), (normalized, "normalized_exact")):
        if key and key in name_index:
            hits = name_index[key]
            same_city = [h for h in hits if h["city_code"] == city_code]
            if same_city:
                return {**same_city[0], "match_type": match_type}
            return {**hits[0], "match_type": f"{match_type}_diff_city"}

    # L2: 包含匹配（DB 名包含搜索名）
    for db_name, hits in name_index.items():
        if name_lower in db_name and len(name_lower) >= 2:
            same_city = [h for h in hits if h["city_code"] == city_code]
            if same_city:
                return {**same_city[0], "match_type": "contains"}

    # L3: 反向包含（搜索名包含 DB 名）
    for db_name, hits in name_index.items():
        if db_name in name_lower and len(db_name) >= 2:
            same_city = [h for h in hits if h["city_code"] == city_code]
            if same_city:
                return {**same_city[0], "match_type": "reverse_contains"}

    return None


# ── Step 2: 定向生成缺失实体 ────────────────────────────────────────────────

async def generate_missing(session, missing_list: list, limit: int | None, delay: float) -> dict:
    """用 AI 定向生成缺失实体。"""
    from app.domains.catalog.ai_generator import generate_entity_by_name
    from app.domains.catalog.upsert import upsert_entity
    from sqlalchemy import text

    candidates = missing_list[:limit] if limit else missing_list
    stats = {"attempted": 0, "succeeded": 0, "failed": 0, "skipped": 0, "generated": []}

    for i, ent in enumerate(candidates, 1):
        name = ent["name"]
        city = ent["city_code"]
        etype = ent["type"]
        stats["attempted"] += 1

        logger.info("  [%d/%d] %s (%s, %s)", i, len(candidates), name, city, etype)

        # 防重
        existing = await session.execute(
            text("SELECT entity_id FROM entity_base WHERE name_zh = :n AND city_code = :c AND is_active = true LIMIT 1"),
            {"n": name, "c": city},
        )
        if existing.fetchone():
            logger.info("    已存在，跳过")
            stats["skipped"] += 1
            continue

        try:
            data = await generate_entity_by_name(name_zh=name, city_code=city, entity_type=etype)
        except Exception as exc:
            logger.error("    AI 生成失败: %s", exc)
            stats["failed"] += 1
            await asyncio.sleep(delay)
            continue

        if not data or not data.get("name_zh"):
            logger.warning("    AI 返回空")
            stats["failed"] += 1
            await asyncio.sleep(delay)
            continue

        if not data.get("lat") or not data.get("lng"):
            logger.warning("    缺坐标，跳过")
            stats["failed"] += 1
            await asyncio.sleep(delay)
            continue

        try:
            entity = await upsert_entity(session=session, entity_type=etype, data=data)
            await session.flush()
            await session.commit()
            stats["succeeded"] += 1
            stats["generated"].append({
                "name": name, "entity_id": str(entity.entity_id),
                "city_code": city, "type": etype,
            })
            logger.info("    写入成功: %s", entity.entity_id)
        except Exception as exc:
            logger.error("    Upsert 失败: %s", exc)
            stats["failed"] += 1
            await session.rollback()

        await asyncio.sleep(delay)

    return stats


# ── Step 3: 自动绑定 circle_entity_roles ────────────────────────────────────

async def bind_roles(session, circle_id: str | None, min_level: str) -> dict:
    """从 anchor_entities 读取，匹配 entity_base，写入 circle_entity_roles。"""
    from sqlalchemy import select, text, and_
    from app.db.models.city_circles import ActivityCluster, CircleEntityRole

    level_filter = {"S": ["S"], "A": ["S", "A"], "B": ["S", "A", "B"]}
    allowed_levels = level_filter.get(min_level, ["S", "A", "B"])

    q = select(ActivityCluster).where(
        ActivityCluster.is_active == True,
        ActivityCluster.anchor_entities != None,
        ActivityCluster.level.in_(allowed_levels),
    )
    if circle_id:
        q = q.where(ActivityCluster.circle_id == circle_id)

    result = await session.execute(q)
    clusters = list(result.scalars().all())

    # 名称索引
    rows = await session.execute(
        text("SELECT entity_id, name_zh, city_code FROM entity_base WHERE is_active = true")
    )
    name_index: dict[str, list[dict]] = {}
    for eid, name, city in rows.fetchall():
        if name:
            payload = {"entity_id": eid, "name_zh": name, "city_code": city}
            name_index.setdefault(name.lower(), []).append(payload)
            normalized = _normalize_name(name)
            if normalized and normalized != name.lower():
                name_index.setdefault(normalized, []).append(payload)

    alias_rows = await session.execute(
        text("""
            SELECT ea.alias_text, ea.normalized_text, eb.entity_id, eb.name_zh, eb.city_code
            FROM entity_aliases ea
            JOIN entity_base eb ON eb.entity_id = ea.entity_id
            WHERE eb.is_active = true
        """)
    )
    for alias_text, normalized_text, eid, name, city in alias_rows.fetchall():
        payload = {"entity_id": eid, "name_zh": name, "city_code": city}
        for key in (alias_text, normalized_text, _normalize_name(alias_text or "")):
            if key:
                name_index.setdefault(key.lower(), []).append(payload)

    stats = {"checked": 0, "created": 0, "existed": 0, "not_found": 0}
    planned_keys: set[tuple[str, str, object, str]] = set()

    role_map = {
        ("poi", "anchor"): "anchor_poi",
        ("poi", "secondary"): "secondary_poi",
        ("restaurant", "anchor"): "meal_destination",
        ("restaurant", "secondary"): "meal_route",
        ("hotel", "anchor"): "hotel_anchor",
        ("hotel", "secondary"): "hotel_anchor",
    }

    for cluster in clusters:
        for i, ent in enumerate(cluster.anchor_entities or []):
            name = ent.get("name", "")
            city = ent.get("city_code", cluster.city_code)
            etype = ent.get("type", "poi")
            role_key = ent.get("role", "secondary")
            stats["checked"] += 1

            found = _find_entity(name, city, name_index)
            if not found:
                stats["not_found"] += 1
                continue

            entity_id = found["entity_id"]
            role_value = role_map.get((etype, role_key), "secondary_poi")
            dedupe_key = (cluster.circle_id, cluster.cluster_id, entity_id, role_value)

            if dedupe_key in planned_keys:
                stats["existed"] += 1
                continue

            # 检查已存在
            existing = await session.execute(
                select(CircleEntityRole.role_id).where(and_(
                    CircleEntityRole.circle_id == cluster.circle_id,
                    CircleEntityRole.cluster_id == cluster.cluster_id,
                    CircleEntityRole.entity_id == entity_id,
                    CircleEntityRole.role == role_value,
                )).limit(1)
            )
            if existing.first():
                stats["existed"] += 1
                continue

            new_role = CircleEntityRole(
                circle_id=cluster.circle_id,
                cluster_id=cluster.cluster_id,
                entity_id=entity_id,
                role=role_value,
                sort_order=i,
                is_cluster_anchor=(role_key == "anchor" and i == 0),
                role_notes=f"auto_bind:from_anchor_entities",
            )
            session.add(new_role)
            planned_keys.add(dedupe_key)
            stats["created"] += 1

    await session.commit()
    return stats


# ── 主入口 ──────────────────────────────────────────────────────────────────

async def run(
    circle_id: str | None = None,
    min_level: str = "B",
    limit: int | None = None,
    delay: float = 1.5,
    analyze_only: bool = False,
    bind_only: bool = False,
):
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # Step 1: 分析
        logger.info("=" * 60)
        logger.info("Step 1: 分析 anchor_entities vs entity_base")
        logger.info("=" * 60)

        gaps = await analyze_gaps(session, circle_id, min_level)

        logger.info("  需要: %d 个实体", gaps["total_entities_needed"])
        logger.info("  已有: %d (%s)", gaps["matched"], gaps["match_rate"])
        logger.info("  缺失: %d", gaps["missing"])

        # 打印缺失 TOP 20
        if gaps["missing_list"]:
            logger.info("\n  缺失 TOP 20:")
            for m in gaps["missing_list"][:20]:
                logger.info("    [%s/%s] %s (%s) — %s",
                             m["cluster_level"], m["role"],
                             m["name"], m["city_code"], m["cluster_id"])

        # 保存分析报告
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = REPORT_DIR / f"gaps_report_{ts}.json"
        report_path.write_text(json.dumps(gaps, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        logger.info("\n  报告: %s", report_path)

        if analyze_only:
            logger.info("\n[--analyze-only] 分析完成")
            return

        if bind_only:
            # 跳到 Step 3
            logger.info("=" * 60)
            logger.info("Step 3: 绑定 circle_entity_roles (--bind-only)")
            logger.info("=" * 60)
            bind_stats = await bind_roles(session, circle_id, min_level)
            logger.info("  检查: %d, 新建: %d, 已有: %d, 未匹配: %d",
                         bind_stats["checked"], bind_stats["created"],
                         bind_stats["existed"], bind_stats["not_found"])
            return

        # Step 2: 生成缺失实体
        if gaps["missing_list"]:
            logger.info("=" * 60)
            logger.info("Step 2: 定向生成缺失实体")
            logger.info("=" * 60)
            gen_stats = await generate_missing(session, gaps["missing_list"], limit, delay)
            logger.info("  成功: %d, 失败: %d, 已存在: %d",
                         gen_stats["succeeded"], gen_stats["failed"], gen_stats["skipped"])
        else:
            logger.info("\n没有缺失实体，跳过生成")

        # Step 3: 绑定
        logger.info("=" * 60)
        logger.info("Step 3: 绑定 circle_entity_roles")
        logger.info("=" * 60)
        bind_stats = await bind_roles(session, circle_id, min_level)
        logger.info("  检查: %d, 新建: %d, 已有: %d, 未匹配: %d",
                     bind_stats["checked"], bind_stats["created"],
                     bind_stats["existed"], bind_stats["not_found"])

        # 汇总
        logger.info("=" * 60)
        logger.info("完成")
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="从 anchor_entities 出发：找缺口 → 定向生成 → 绑定 circle_entity_roles")
    parser.add_argument("--circle", help="只处理指定城市圈")
    parser.add_argument("--min-level", default="B", choices=["S", "A", "B"],
                        help="最低处理等级（默认 B = 全部）")
    parser.add_argument("--limit", type=int, help="最多生成 N 个缺失实体")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="AI 调用间隔秒数")
    parser.add_argument("--analyze-only", action="store_true",
                        help="只分析缺口，不生成不绑定")
    parser.add_argument("--bind-only", action="store_true",
                        help="跳过生成，只做 circle_entity_roles 绑定")
    args = parser.parse_args()

    asyncio.run(run(
        circle_id=args.circle,
        min_level=args.min_level,
        limit=args.limit,
        delay=args.delay,
        analyze_only=args.analyze_only,
        bind_only=args.bind_only,
    ))


if __name__ == "__main__":
    main()

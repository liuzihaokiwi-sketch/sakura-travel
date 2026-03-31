"""
T4: core_visit_minutes 补充
从 cluster anchor 实体的 typical_duration_min 取最大值;
如果 anchor 没有 duration → 按 capacity_units 推算 (1.0→180, 0.5→90)

运行: python scripts/t4_fill_core_visit_minutes.py [--dry-run]
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# capacity_units → 推算分钟数
CAPACITY_TO_MINUTES = {
    1.0: 180,
    0.75: 135,
    0.5: 90,
    0.25: 60,
}
DEFAULT_MINUTES = 60  # 无任何信息时的兜底


def capacity_to_minutes(capacity: float | None) -> int:
    if capacity is None:
        return DEFAULT_MINUTES
    # 找最近的 key
    for threshold in sorted(CAPACITY_TO_MINUTES.keys(), reverse=True):
        if capacity >= threshold:
            return CAPACITY_TO_MINUTES[threshold]
    return DEFAULT_MINUTES


async def main(dry_run: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        r_before = await session.execute(text("""
            SELECT COUNT(*) FROM activity_clusters
            WHERE core_visit_minutes IS NULL AND is_active=true
        """))
        null_count = r_before.scalar()
        print(f"Before: {null_count} clusters with NULL core_visit_minutes")

        # 拉所有需要填的 clusters
        r_clusters = await session.execute(text("""
            SELECT
                ac.cluster_id::text,
                ac.name_zh,
                ac.anchor_entities,
                ac.capacity_units
            FROM activity_clusters ac
            WHERE ac.is_active = true
              AND (ac.core_visit_minutes IS NULL OR ac.core_visit_minutes = 0)
        """))
        clusters = r_clusters.fetchall()
        print(f"Clusters to fill: {len(clusters)}")

        updated = 0
        for cluster_id, cluster_name, anchor_entities, capacity_units in clusters:
            minutes = None

            # 1. 从 circle_entity_roles 查 anchor poi 的 typical_duration_min 取最大值
            r_dur = await session.execute(text("""
                SELECT MAX(p.typical_duration_min)
                FROM circle_entity_roles cer
                JOIN pois p ON p.entity_id = cer.entity_id
                WHERE cer.cluster_id = :cid
                  AND cer.is_cluster_anchor = true
                  AND p.typical_duration_min IS NOT NULL
                  AND p.typical_duration_min > 0
            """), {"cid": cluster_id})
            max_dur = r_dur.scalar()
            if max_dur and max_dur > 0:
                minutes = int(max_dur)

            # 2. 无 anchor duration → 按 capacity_units 推算
            if not minutes:
                minutes = capacity_to_minutes(float(capacity_units) if capacity_units else None)

            source = "circle_entity_roles" if max_dur else "capacity"
            print(f"  {cluster_name}: {minutes} min (from {source})")

            if not dry_run:
                await session.execute(text("""
                    UPDATE activity_clusters
                    SET core_visit_minutes = :minutes
                    WHERE cluster_id = :cid
                """), {"minutes": minutes, "cid": cluster_id})
            updated += 1

        if not dry_run:
            await session.commit()

        print(f"\nResult: updated={updated} clusters")

        # 验证
        r_after = await session.execute(text("""
            SELECT COUNT(*) FROM activity_clusters
            WHERE (core_visit_minutes IS NULL OR core_visit_minutes = 0) AND is_active=true
        """))
        remaining_zero = r_after.scalar()

        if remaining_zero == 0:
            print("[PASS] Verification: all active clusters have core_visit_minutes > 0")
        else:
            print(f"[WARN] Verification: {remaining_zero} clusters still have 0/NULL")

        print("\n[OK] T4 DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))

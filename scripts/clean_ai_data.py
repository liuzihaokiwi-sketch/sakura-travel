"""
A2: 清除 AI 生成数据
- entity_base 中 trust_status='ai_generated' 的 208 条标记为 is_active=False
- 确认剩余 unverified 数据的质量（坐标在北海道 bbox 内、有名称）
- 不删除数据，保留审计记录

运行：python scripts/clean_ai_data.py
运行（dry run）：python scripts/clean_ai_data.py --dry-run
"""
import asyncio
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

# 北海道 + 附近城市 bounding box（稍微放宽一些）
# 北海道: lat 41.3~45.6, lng 139.3~145.9
JAPAN_BBOX = {"lat_min": 24.0, "lat_max": 46.0, "lng_min": 122.0, "lng_max": 146.0}


async def main(dry_run: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        # ── 1. 统计当前状态 ────────────────────────────────────────────────
        r = await session.execute(text(
            "SELECT trust_status, is_active, COUNT(*) "
            "FROM entity_base GROUP BY trust_status, is_active "
            "ORDER BY trust_status, is_active"
        ))
        print("=== Before ===")
        rows = r.fetchall()
        for row in rows:
            print(f"  trust_status={row[0]:<20} is_active={str(row[1]):<5} count={row[2]}")

        # ── 2. 标记 ai_generated → is_active=False ─────────────────────────
        r_count = await session.execute(text(
            "SELECT COUNT(*) FROM entity_base "
            "WHERE trust_status='ai_generated' AND is_active=true"
        ))
        ai_active_count = r_count.scalar()
        print(f"\nFound {ai_active_count} active ai_generated entities to deactivate")

        if not dry_run and ai_active_count > 0:
            result = await session.execute(text(
                "UPDATE entity_base SET is_active = false "
                "WHERE trust_status = 'ai_generated' AND is_active = true"
            ))
            await session.commit()
            print(f"  Deactivated {result.rowcount} ai_generated entities")

        # ── 3. 检查 unverified 数据质量 ────────────────────────────────────
        r_uv = await session.execute(text(
            "SELECT "
            "  COUNT(*) AS total, "
            "  COUNT(lat) AS has_lat, "
            "  COUNT(name_zh) AS has_name_zh, "
            "  SUM(CASE WHEN lat IS NOT NULL AND lat BETWEEN :lat_min AND :lat_max "
            "           AND lng IS NOT NULL AND lng BETWEEN :lng_min AND :lng_max "
            "      THEN 1 ELSE 0 END) AS in_bbox "
            "FROM entity_base "
            "WHERE trust_status = 'unverified' AND is_active = true"
        ), JAPAN_BBOX)
        uv = r_uv.fetchone()
        print(f"\n=== Unverified data quality ===")
        print(f"  total:       {uv[0]}")
        print(f"  has_lat:     {uv[1]}")
        print(f"  has_name_zh: {uv[2]}")
        print(f"  in_jp_bbox:  {uv[3]}")

        # 找出坐标异常的
        r_bad = await session.execute(text(
            "SELECT entity_id, name_zh, city_code, lat, lng "
            "FROM entity_base "
            "WHERE trust_status = 'unverified' AND is_active = true "
            "AND (lat IS NULL OR lng IS NULL "
            "     OR lat NOT BETWEEN :lat_min AND :lat_max "
            "     OR lng NOT BETWEEN :lng_min AND :lng_max)"
        ), JAPAN_BBOX)
        bad_rows = r_bad.fetchall()
        if bad_rows:
            print(f"\n  WARNING: {len(bad_rows)} unverified entities with bad/missing coords:")
            for row in bad_rows[:10]:
                print(f"    entity_id={row[0]} city={row[2]} lat={row[3]} lng={row[4]}")
        else:
            print("  All unverified entities have valid coords in JP bbox")

        # ── 4. 最终状态确认 ────────────────────────────────────────────────
        if not dry_run:
            r2 = await session.execute(text(
                "SELECT trust_status, is_active, COUNT(*) "
                "FROM entity_base GROUP BY trust_status, is_active "
                "ORDER BY trust_status, is_active"
            ))
            print("\n=== After ===")
            for row in r2.fetchall():
                print(f"  trust_status={row[0]:<20} is_active={str(row[1]):<5} count={row[2]}")

    if dry_run:
        print("\n[DRY RUN] No changes made")
    else:
        print("\nA2 DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))

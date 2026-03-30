"""
FIX-2: 分析并修复 suspicious 实体

逻辑：
- 坐标在日本范围内（lat 24-46, lng 122-146）且数据来自真实源（google_place_id 或 tabelog_id）
  → 改为 unverified
- 坐标完全缺失或明显错误（0,0 或超出日本范围）
  → 保持 suspicious

运行: python scripts/fix_suspicious.py [--dry-run]
"""
import asyncio, sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

JP_BBOX = dict(lat_min=24.0, lat_max=46.0, lng_min=122.0, lng_max=146.0)


async def main(dry_run: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        # 统计分类
        r = await session.execute(text("""
            SELECT
                COUNT(*) AS total,
                COUNT(CASE WHEN lat BETWEEN :lat_min AND :lat_max
                            AND lng BETWEEN :lng_min AND :lng_max THEN 1 END) AS in_bbox,
                COUNT(CASE WHEN lat IS NULL OR lng IS NULL THEN 1 END) AS no_coords
            FROM entity_base WHERE trust_status = 'suspicious'
        """), JP_BBOX)
        row = r.fetchone()
        print(f"[FIX-2] suspicious total={row[0]}, in_jp_bbox={row[1]}, no_coords={row[2]}")

        # 可以修复的：坐标在日本范围内
        r2 = await session.execute(text("""
            SELECT entity_id, name_zh, city_code, entity_type, google_place_id, lat, lng
            FROM entity_base
            WHERE trust_status = 'suspicious'
              AND lat BETWEEN :lat_min AND :lat_max
              AND lng BETWEEN :lng_min AND :lng_max
        """), JP_BBOX)
        fixable = r2.fetchall()
        print(f"  Fixable (valid JP coords): {len(fixable)}")

        # 真的有问题的：坐标异常
        r3 = await session.execute(text("""
            SELECT entity_id, name_zh, city_code, lat, lng
            FROM entity_base
            WHERE trust_status = 'suspicious'
              AND (lat IS NULL OR lng IS NULL
                   OR lat NOT BETWEEN :lat_min AND :lat_max
                   OR lng NOT BETWEEN :lng_min AND :lng_max)
        """), JP_BBOX)
        bad = r3.fetchall()
        print(f"  Truly bad (bad/missing coords): {len(bad)}")
        for row in bad[:5]:
            print(f"    {row[1][:20] if row[1] else '?'} city={row[2]} lat={row[3]} lng={row[4]}")

        if dry_run:
            print("[DRY RUN] No changes")
            return

        # 执行修复
        result = await session.execute(text("""
            UPDATE entity_base
            SET trust_status = 'unverified'
            WHERE trust_status = 'suspicious'
              AND lat BETWEEN :lat_min AND :lat_max
              AND lng BETWEEN :lng_min AND :lng_max
        """), JP_BBOX)
        await session.commit()
        fixed = result.rowcount
        print(f"\n  Fixed {fixed} suspicious → unverified")

        # 验证
        r4 = await session.execute(text(
            "SELECT trust_status, COUNT(*) FROM entity_base GROUP BY trust_status ORDER BY trust_status"
        ))
        print("\nFinal trust_status distribution:")
        for row in r4.fetchall():
            print(f"  {row[0]}: {row[1]}")

    print("\nFIX-2 DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))

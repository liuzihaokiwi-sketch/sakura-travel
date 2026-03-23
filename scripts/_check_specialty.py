"""快速健康检查：specialty clusters 命名一致性"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as s:
        print("=== 1. circle_id 分布 ===")
        r = await s.execute(text("SELECT circle_id, count(*) n FROM activity_clusters GROUP BY circle_id ORDER BY circle_id"))
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}")

        print("\n=== 2. specialty clusters (must_have_tags != null/empty) ===")
        r = await s.execute(text(
            "SELECT cluster_id, circle_id, primary_corridor "
            "FROM activity_clusters "
            "WHERE must_have_tags IS NOT NULL AND must_have_tags::text != '[]' "
            "ORDER BY cluster_id"
        ))
        rows = r.fetchall()
        print(f"  共 {len(rows)} 条")
        for row in rows:
            print(f"  {row[0]} | circle={row[1]} | corridor={row[2]}")

        print("\n=== 3. 全量 distinct primary_corridor ===")
        r = await s.execute(text(
            "SELECT DISTINCT primary_corridor FROM activity_clusters ORDER BY primary_corridor"
        ))
        corridors = [row[0] for row in r.fetchall()]
        print(f"  共 {len(corridors)} 条: {corridors}")

asyncio.run(main())

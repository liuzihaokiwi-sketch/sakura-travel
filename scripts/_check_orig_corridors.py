"""查原始 clusters 的 primary_corridor"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as s:
        r = await s.execute(text(
            "SELECT cluster_id, primary_corridor FROM activity_clusters "
            "WHERE must_have_tags IS NULL OR must_have_tags::text = '[]' "
            "ORDER BY cluster_id"
        ))
        print("=== 原始 clusters 的 primary_corridor ===")
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}")

asyncio.run(main())

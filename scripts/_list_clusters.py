import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as s:
        r = await s.execute(text(
            "SELECT cluster_id, level FROM activity_clusters ORDER BY level DESC, cluster_id"
        ))
        rows = r.fetchall()
        print(f"Total clusters: {len(rows)}")
        for row in rows:
            print(f"  {row[1]:3s} | {row[0]}")

asyncio.run(main())
import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as s:
        r = await s.execute(text("SELECT circle_id, name_zh FROM city_circles"))
        for row in r.fetchall():
            print(row)
        # Also check what circle_id the existing clusters use
        r2 = await s.execute(text("SELECT DISTINCT circle_id FROM activity_clusters LIMIT 5"))
        print("Cluster circle_ids:", [row[0] for row in r2.fetchall()])

asyncio.run(main())
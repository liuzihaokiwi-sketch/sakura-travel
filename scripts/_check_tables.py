"""Quick DB table check."""
import asyncio
from app.db.session import engine
from sqlalchemy import text

async def f():
    async with engine.connect() as c:
        r = await c.execute(text(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname='public' ORDER BY tablename"
        ))
        for row in r:
            print(row[0])

asyncio.run(f())

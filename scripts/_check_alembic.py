"""Check alembic_version."""
import asyncio
from app.db.session import engine
from sqlalchemy import text

async def f():
    async with engine.connect() as c:
        try:
            r = await c.execute(text("SELECT version_num FROM alembic_version"))
            rows = r.all()
            if rows:
                for row in rows:
                    print(f"alembic_version: {row[0]}")
            else:
                print("alembic_version table exists but is EMPTY")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(f())

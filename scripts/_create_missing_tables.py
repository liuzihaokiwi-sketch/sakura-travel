"""
Create missing tables from ORM models.
Uses checkfirst=True so existing tables are skipped.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import engine, Base
from sqlalchemy import text
import app.db.models  # noqa: F401 — register all models

async def main():
    async with engine.begin() as conn:
        # Ensure required extensions exist
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    print("✅ All missing tables created (checkfirst=True).")

asyncio.run(main())
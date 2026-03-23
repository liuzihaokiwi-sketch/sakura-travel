import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as s:
        await s.execute(text("""
            ALTER TABLE activity_clusters
            ADD COLUMN IF NOT EXISTS must_have_tags JSONB DEFAULT NULL,
            ADD COLUMN IF NOT EXISTS season_fit JSONB DEFAULT NULL,
            ADD COLUMN IF NOT EXISTS capacity_units FLOAT DEFAULT 1.0,
            ADD COLUMN IF NOT EXISTS transit_minutes INTEGER DEFAULT 60,
            ADD COLUMN IF NOT EXISTS slack_minutes INTEGER DEFAULT 30,
            ADD COLUMN IF NOT EXISTS meal_break_minutes INTEGER DEFAULT 60,
            ADD COLUMN IF NOT EXISTS day_type_hint VARCHAR(32) DEFAULT 'normal',
            ADD COLUMN IF NOT EXISTS typical_start_time VARCHAR(8) DEFAULT '09:00',
            ADD COLUMN IF NOT EXISTS description_zh TEXT DEFAULT NULL
        """))
        await s.commit()
        print("✅ 所有列已添加")

asyncio.run(main())

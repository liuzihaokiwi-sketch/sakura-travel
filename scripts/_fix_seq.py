"""Reset entity_tags id sequence to max(id)+1"""
import asyncio, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(Path(__file__).parent.parent)
from dotenv import load_dotenv; load_dotenv()
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine(os.getenv("DATABASE_URL", ""))
    async with engine.begin() as conn:
        # 查看表结构
        r = await conn.execute(text(
            "SELECT column_name, data_type, column_default "
            "FROM information_schema.columns WHERE table_name='entity_tags' ORDER BY ordinal_position"
        ))
        print("entity_tags columns:")
        for row in r.fetchall():
            print(f"  {row[0]:20s} {row[1]:20s} {row[2] or ''}")

        # 找序列名
        r = await conn.execute(text("SELECT pg_get_serial_sequence('entity_tags', 'id')"))
        seq = r.scalar()
        print(f"\nSequence: {seq}")

        # 当前 max id
        r = await conn.execute(text("SELECT max(id) FROM entity_tags"))
        max_id = r.scalar() or 0
        print(f"Max id: {max_id}")

        if seq and max_id > 0:
            await conn.execute(text(f"SELECT setval('{seq}', {max_id})"))
            print(f"✅ Sequence reset to {max_id}")

    await engine.dispose()

asyncio.run(main())

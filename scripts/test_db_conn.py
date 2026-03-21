import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import redis as redis_lib

load_dotenv()

async def test_pg():
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://japan_ai:japan_ai_dev@localhost:5432/japan_ai")
    e = create_async_engine(db_url)
    async with e.begin() as conn:
        r = await conn.execute(text("SELECT version()"))
        row = r.fetchone()[0]
        print(f"✅ PostgreSQL: {row[:60]}")
    await e.dispose()

def test_redis():
    r = redis_lib.Redis(host="localhost", port=6379, db=0)
    pong = r.ping()
    print(f"✅ Redis: ping={pong}")
    r.close()

asyncio.run(test_pg())
test_redis()
print("\n🎉 数据库环境全部就绪！")

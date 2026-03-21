"""从 Supabase 远端数据库拉取数据到本地"""
import asyncio
import os
import ssl
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
PROJECT_ID = SUPABASE_URL.replace("https://", "").split(".")[0] if SUPABASE_URL else ""
PG_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", ""))

# Supabase 直连格式
REMOTE_URL = f"postgresql+asyncpg://postgres.{PROJECT_ID}:{PG_PASSWORD}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
LOCAL_URL = os.getenv("DATABASE_URL", "")

print(f"Remote project: {PROJECT_ID}")
print(f"Remote host: aws-0-ap-northeast-1.pooler.supabase.com:6543")
print(f"Local: {LOCAL_URL.split('@')[1] if '@' in LOCAL_URL else LOCAL_URL}")

async def test_remote():
    # 尝试多种 Supabase 连接格式
    urls = [
        # pooler session mode (port 5432) — aws-1 region
        f"postgresql+asyncpg://postgres.{PROJECT_ID}:{PG_PASSWORD}@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres",
        # pooler transaction mode (port 6543) — aws-1 region
        f"postgresql+asyncpg://postgres.{PROJECT_ID}:{PG_PASSWORD}@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres",
        # direct
        f"postgresql+asyncpg://postgres:{PG_PASSWORD}@db.{PROJECT_ID}.supabase.co:5432/postgres",
    ]
    
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    for i, url in enumerate(urls):
        label = ["pooler:6543", "pooler:5432", "direct:5432"][i]
        try:
            print(f"\n尝试 [{label}]...")
            engine = create_async_engine(url, connect_args={"ssl": ssl_ctx}, pool_timeout=10)
            async with engine.begin() as conn:
                r = await conn.execute(text("SELECT count(*) FROM entity_base"))
                count = r.scalar()
                print(f"  ✅ 连接成功！entity_base 有 {count} 条数据")
                
                r2 = await conn.execute(text(
                    "SELECT entity_type, city_code, count(*) FROM entity_base "
                    "GROUP BY entity_type, city_code ORDER BY city_code"
                ))
                for row in r2.fetchall():
                    print(f"    {row[0]:12} {row[1]:8} {row[2]} 条")
            await engine.dispose()
            return url  # 返回可用的 URL
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            try:
                await engine.dispose()
            except:
                pass
    
    return None

result = asyncio.run(test_remote())
if result:
    print(f"\n🎯 可用连接: {result.split('@')[1]}")
else:
    print("\n❌ 所有连接方式都失败了。请检查 Supabase 数据库密码和项目 ID。")

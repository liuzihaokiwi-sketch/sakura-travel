import asyncio, sys, traceback
sys.path.insert(0, '.')

async def main():
    try:
        from app.db.session import engine, Base
        import app.db.models.catalog
        import app.db.models.derived
        import app.db.models.business
        import app.db.models.snapshots

        tables = list(Base.metadata.tables.keys())
        print(f"发现 {len(tables)} 张表:")
        for t in sorted(tables):
            print(f"  - {t}")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("\n✅ 所有表创建成功")
        await engine.dispose()
    except Exception as e:
        traceback.print_exc()
        print(f"\n❌ 失败: {e}")

asyncio.run(main())

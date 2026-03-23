import asyncio, sys, logging
logging.disable(logging.CRITICAL)
sys.path.insert(0, ".")
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.database_url, echo=False)
    async with AsyncSession(engine) as s:
        r = await s.execute(text(
            "SELECT preset_id, name_zh, min_days, max_days, switch_count, bases "
            "FROM hotel_strategy_presets ORDER BY min_days, max_days"
        ))
        rows = r.fetchall()
        print(f"Total presets: {len(rows)}", flush=True)
        for row in rows:
            print(f"  [{row[0]}] {row[1]} days={row[2]}-{row[3]} switches={row[4]}", flush=True)
            bases = row[5]
            if bases:
                for b in bases:
                    print(f"      base: city={b.get('base_city')} area={b.get('area')} nights={b.get('nights')} nr={b.get('nights_range')}", flush=True)

asyncio.run(main())

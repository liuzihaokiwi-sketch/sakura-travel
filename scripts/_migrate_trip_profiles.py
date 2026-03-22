import asyncio, asyncpg

async def run():
    conn = await asyncpg.connect("postgresql://postgres:Pp360808973!@localhost:5432/postgres")
    cols = [
        ("arrival_shape",         "VARCHAR(30)"),
        ("departure_shape",       "VARCHAR(30)"),
        ("arrival_airport",       "VARCHAR(10)"),
        ("departure_airport",     "VARCHAR(10)"),
        ("last_flight_time",      "VARCHAR(10)"),
        ("daytrip_tolerance",     "VARCHAR(20)"),
        ("hotel_switch_tolerance","VARCHAR(20)"),
        ("wake_up_time",          "VARCHAR(20)"),
        ("arrival_day_shape",     "VARCHAR(30)"),
        ("departure_day_shape",   "VARCHAR(30)"),
        ("accommodation_pref",    "JSONB"),
        ("flight_info",           "JSONB"),
    ]
    for col, typ in cols:
        await conn.execute(f"ALTER TABLE trip_profiles ADD COLUMN IF NOT EXISTS {col} {typ}")
        print(f"  OK: {col}")

    # 顺便检查实际列
    rows = await conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='trip_profiles' ORDER BY ordinal_position"
    )
    print("\nCurrent columns:")
    for r in rows:
        print(" ", r["column_name"])

    await conn.close()
    print("\nMigration done.")

asyncio.run(run())

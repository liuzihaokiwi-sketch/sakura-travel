"""One-shot migration: add ALL missing columns"""
import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

MIGRATIONS = [
    # trip_profiles
    "ALTER TABLE trip_profiles ADD COLUMN IF NOT EXISTS budget_focus VARCHAR(50)",
    "ALTER TABLE trip_profiles ADD COLUMN IF NOT EXISTS special_requirements TEXT",
    "ALTER TABLE trip_profiles ADD COLUMN IF NOT EXISTS normalized_at TIMESTAMPTZ",
    # entity_scores
    "ALTER TABLE entity_scores ADD COLUMN IF NOT EXISTS preview_score REAL",
    "ALTER TABLE entity_scores ADD COLUMN IF NOT EXISTS context_score REAL",
    "ALTER TABLE entity_scores ADD COLUMN IF NOT EXISTS soft_rule_score REAL",
    "ALTER TABLE entity_scores ADD COLUMN IF NOT EXISTS soft_rule_breakdown JSONB",
    "ALTER TABLE entity_scores ADD COLUMN IF NOT EXISTS segment_pack_id VARCHAR(50)",
    "ALTER TABLE entity_scores ADD COLUMN IF NOT EXISTS stage_pack_id VARCHAR(50)",
    # itinerary_items
    "ALTER TABLE itinerary_items ADD COLUMN IF NOT EXISTS swap_candidates JSONB",
    # itinerary_plans
    "ALTER TABLE itinerary_plans ADD COLUMN IF NOT EXISTS planner_run_id BIGINT",
    "ALTER TABLE itinerary_plans ADD COLUMN IF NOT EXISTS version SMALLINT DEFAULT 1",
    # new tables (create if not exist)
    """CREATE TABLE IF NOT EXISTS guide_fragments (
        fragment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        fragment_type VARCHAR(30) NOT NULL,
        destination_code VARCHAR(20) NOT NULL,
        theme_families JSONB DEFAULT '[]',
        party_types JSONB DEFAULT '[]',
        season_tags JSONB DEFAULT '[]',
        budget_tiers JSONB DEFAULT '[]',
        duration_range INT4RANGE,
        title_zh VARCHAR(200),
        body_zh TEXT,
        body_html TEXT,
        quality_score REAL DEFAULT 0.6,
        usage_count INTEGER DEFAULT 0,
        source_trip_id UUID,
        source_type VARCHAR(20) DEFAULT 'manual',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now(),
        last_used_at TIMESTAMPTZ
    )""",
    """CREATE TABLE IF NOT EXISTS generation_runs (
        run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        submission_id VARCHAR(100),
        order_id UUID,
        plan_id UUID,
        generation_mode VARCHAR(30),
        started_at TIMESTAMPTZ DEFAULT now(),
        completed_at TIMESTAMPTZ,
        status VARCHAR(20) DEFAULT 'running',
        total_fragments_hit INTEGER DEFAULT 0,
        total_fragments_adopted INTEGER DEFAULT 0,
        hit_tier VARCHAR(5),
        error_message TEXT,
        metadata_snapshot JSONB DEFAULT '{}'
    )""",
    """CREATE TABLE IF NOT EXISTS detail_forms (
        form_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_id UUID NOT NULL,
        current_step INTEGER DEFAULT 1,
        status VARCHAR(20) DEFAULT 'draft',
        form_data JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now()
    )""",
]

async def main():
    async with AsyncSessionLocal() as s:
        for sql in MIGRATIONS:
            try:
                await s.execute(text(sql))
                if "ALTER TABLE" in sql:
                    col = sql.split("ADD COLUMN IF NOT EXISTS ")[1].split(" ")[0]
                    tbl = sql.split("ALTER TABLE ")[1].split(" ")[0]
                    print(f"  ✅ {tbl}.{col}")
                elif "CREATE TABLE" in sql:
                    tbl = sql.split("CREATE TABLE IF NOT EXISTS ")[1].split(" ")[0].split("(")[0].strip()
                    print(f"  ✅ TABLE {tbl}")
            except Exception as e:
                print(f"  ⚠️ {str(e)[:80]}")
        await s.commit()
        print("\n✅ All migrations applied")

asyncio.run(main())
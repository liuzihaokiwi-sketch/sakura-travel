"""Add missing columns to entity_base table."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import engine
from sqlalchemy import text

COLUMNS = [
    "ALTER TABLE entity_base ADD COLUMN IF NOT EXISTS nearest_station VARCHAR(100)",
    "ALTER TABLE entity_base ADD COLUMN IF NOT EXISTS corridor_tags JSONB DEFAULT '[]'",
    "ALTER TABLE entity_base ADD COLUMN IF NOT EXISTS typical_duration_baseline SMALLINT",
    "ALTER TABLE entity_base ADD COLUMN IF NOT EXISTS price_band VARCHAR(10)",
    "ALTER TABLE entity_base ADD COLUMN IF NOT EXISTS operating_stability_level VARCHAR(10)",
    "ALTER TABLE entity_base ADD COLUMN IF NOT EXISTS google_place_id VARCHAR(200)",
    "ALTER TABLE entity_base ADD COLUMN IF NOT EXISTS tabelog_id VARCHAR(200)",
    # entity_media new columns
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS source_kind VARCHAR(30)",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS source_page_url TEXT",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS attribution_text VARCHAR(500)",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS copyright_note VARCHAR(200)",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS license_status VARCHAR(20) DEFAULT 'review_needed'",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS image_role VARCHAR(30)",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS quality_score NUMERIC(4,2)",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS representativeness_score NUMERIC(4,2)",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS season_tag VARCHAR(20)",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS daypart_tag VARCHAR(20)",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS is_selected BOOLEAN DEFAULT FALSE",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS needs_review BOOLEAN DEFAULT TRUE",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100)",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS width SMALLINT",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS height SMALLINT",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS file_size_kb SMALLINT",
    "ALTER TABLE entity_media ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
]

async def main():
    async with engine.begin() as conn:
        for sql in COLUMNS:
            await conn.execute(text(sql))
            print(f"  OK: {sql[:70]}...")
    print("✅ All missing columns added.")

asyncio.run(main())

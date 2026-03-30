"""D1: day_fragments table

Revision ID: 20260330_220000
Revises: 20260330_210000
Create Date: 2026-03-30 22:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260330_220000"
down_revision = "20260330_210000"  # Points to city_climate_holiday (correct)
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── day_fragments ────────────────────────────────────────────────────────
    op.create_table(
        "day_fragments",
        sa.Column("fragment_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("city_code", sa.String(50), nullable=False),
        sa.Column("corridor", sa.String(100), nullable=True),
        sa.Column("fragment_type", sa.String(20), nullable=False,
                  comment="'half_day' / 'full_day'"),
        sa.Column("theme", sa.String(100), nullable=True),
        sa.Column("items", postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  comment="Ordered list of activities with alternatives"),
        sa.Column("total_duration", sa.SmallInteger(), nullable=True,
                  comment="Minutes"),
        sa.Column("estimated_cost", sa.Integer(), nullable=True,
                  comment="JPY per person"),
        sa.Column("best_season", postgresql.ARRAY(sa.String(20)), nullable=True),
        sa.Column("weather_ok", postgresql.ARRAY(sa.String(20)),
                  nullable=True),
        sa.Column("suitable_for", postgresql.ARRAY(sa.String(20)),
                  nullable=True),
        sa.Column("pace", sa.String(20)),
        sa.Column("energy_level", sa.String(20)),
        sa.Column("start_station", sa.String(100), nullable=True),
        sa.Column("end_station", sa.String(100), nullable=True),
        sa.Column("transit_from_prev", sa.String(200), nullable=True),
        sa.Column("title_zh", sa.String(200), nullable=True),
        sa.Column("summary_zh", sa.Text(), nullable=True),
        sa.Column("practical_notes", sa.Text(), nullable=True),
        sa.Column("quality_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("fragment_id"),
    )
    op.create_index("ix_day_fragments_city_code", "day_fragments", ["city_code"])


def downgrade() -> None:
    op.drop_table("day_fragments")

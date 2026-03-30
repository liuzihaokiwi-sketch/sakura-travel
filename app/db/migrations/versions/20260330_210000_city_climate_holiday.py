"""A3: city_climate_monthly + holiday_calendar tables

Revision ID: 20260330_210000
Revises: 20260330_200000
Create Date: 2026-03-30 21:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260330_210000"
down_revision = "20260330_200000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── city_climate_monthly ──────────────────────────────────────────────────
    op.create_table(
        "city_climate_monthly",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("city_code", sa.String(50), nullable=False),
        sa.Column("month", sa.SmallInteger(), nullable=False,
                  comment="1-12"),
        sa.Column("avg_temp_high", sa.Numeric(4, 1), nullable=True,
                  comment="Celsius, monthly average high"),
        sa.Column("avg_temp_low", sa.Numeric(4, 1), nullable=True,
                  comment="Celsius, monthly average low"),
        sa.Column("precipitation", sa.SmallInteger(), nullable=True,
                  comment="mm per month"),
        sa.Column("sunshine_hours", sa.SmallInteger(), nullable=True,
                  comment="hours per month"),
        sa.Column("snow_days", sa.SmallInteger(), nullable=True,
                  comment="days with snowfall"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("data_source", sa.String(100), nullable=True,
                  server_default="'Japan Meteorological Agency'"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_code", "month", name="uq_city_month"),
    )
    op.create_index("ix_city_climate_monthly_city_code",
                    "city_climate_monthly", ["city_code"])

    # ── holiday_calendar ──────────────────────────────────────────────────────
    op.create_table(
        "holiday_calendar",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True,
                  comment="For multi-day events; NULL = single day"),
        sa.Column("name_ja", sa.String(100), nullable=True),
        sa.Column("name_en", sa.String(100), nullable=False),
        sa.Column("country_code", sa.String(5), nullable=False,
                  server_default="'JP'"),
        sa.Column("city_code", sa.String(50), nullable=True,
                  comment="NULL = nationwide, else city-specific festival"),
        sa.Column("type", sa.String(30), nullable=False,
                  comment="public_holiday / festival / school_holiday / golden_week"),
        sa.Column("crowd_level", sa.String(20), nullable=True,
                  comment="low / medium / high / very_high"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_holiday_calendar_date",
                    "holiday_calendar", ["date"])
    op.create_index("ix_holiday_calendar_country_city",
                    "holiday_calendar", ["country_code", "city_code"])


def downgrade() -> None:
    op.drop_table("holiday_calendar")
    op.drop_table("city_climate_monthly")

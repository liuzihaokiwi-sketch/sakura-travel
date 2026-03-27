"""trip_profiles: add Layer 2 canonical input contract columns

Revision ID: 20260326_220000
Revises: 20260323_030000
Create Date: 2026-03-26 22:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260326_220000"
down_revision = "20260323_030000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trip_profiles", sa.Column("contract_version", sa.String(length=20), nullable=True))
    op.add_column("trip_profiles", sa.Column("requested_city_circle", sa.String(length=80), nullable=True))
    op.add_column("trip_profiles", sa.Column("arrival_local_datetime", sa.DateTime(timezone=False), nullable=True))
    op.add_column("trip_profiles", sa.Column("departure_local_datetime", sa.DateTime(timezone=False), nullable=True))
    op.add_column("trip_profiles", sa.Column("visited_places", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("trip_profiles", sa.Column("do_not_go_places", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("trip_profiles", sa.Column("booked_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("trip_profiles", sa.Column("companion_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("trip_profiles", sa.Column("budget_range", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("trip_profiles", "budget_range")
    op.drop_column("trip_profiles", "companion_breakdown")
    op.drop_column("trip_profiles", "booked_items")
    op.drop_column("trip_profiles", "do_not_go_places")
    op.drop_column("trip_profiles", "visited_places")
    op.drop_column("trip_profiles", "departure_local_datetime")
    op.drop_column("trip_profiles", "arrival_local_datetime")
    op.drop_column("trip_profiles", "requested_city_circle")
    op.drop_column("trip_profiles", "contract_version")

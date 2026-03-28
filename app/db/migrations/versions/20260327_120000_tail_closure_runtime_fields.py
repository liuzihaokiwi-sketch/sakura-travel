"""add runtime closure fields for trip_profiles/detail_forms

Revision ID: 20260327_120000
Revises: 20260326_220000
Create Date: 2026-03-27 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260327_120000"
down_revision = "20260326_220000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trip_profiles",
        sa.Column("must_visit_places", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "detail_forms",
        sa.Column("requested_city_circle", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "detail_forms",
        sa.Column("visited_places", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "detail_forms",
        sa.Column("do_not_go_places", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "detail_forms",
        sa.Column("booked_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("detail_forms", "booked_items")
    op.drop_column("detail_forms", "do_not_go_places")
    op.drop_column("detail_forms", "visited_places")
    op.drop_column("detail_forms", "requested_city_circle")
    op.drop_column("trip_profiles", "must_visit_places")

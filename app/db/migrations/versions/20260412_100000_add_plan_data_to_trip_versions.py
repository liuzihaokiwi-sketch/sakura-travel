"""add plan_data JSONB to trip_versions

v2 流程 Opus 装配的方案快照存 trip_versions.plan_data，
不再把大 JSON 塞进 trip_requests.raw_input。

Revision ID: 20260412_100000
Revises: 20260330_230000
Create Date: 2026-04-12 10:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260412_100000"
down_revision = "20260330_230000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trip_versions",
        sa.Column(
            "plan_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="v2流程：Opus装配的plan快照（plan_preview或final_plan）",
        ),
    )


def downgrade() -> None:
    op.drop_column("trip_versions", "plan_data")

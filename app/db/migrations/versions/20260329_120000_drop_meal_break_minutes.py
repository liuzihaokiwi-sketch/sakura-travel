"""activity_clusters: drop meal_break_minutes (duplicate of meal_buffer_minutes)

Revision ID: 20260329_120000
Revises: 20260329_110000
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa

revision = "20260329_120000"
down_revision = "20260329_110000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("activity_clusters", "meal_break_minutes")


def downgrade() -> None:
    op.add_column(
        "activity_clusters",
        sa.Column(
            "meal_break_minutes",
            sa.SmallInteger(),
            server_default="0",
            nullable=True,
            comment="簇内餐饮中断时长（分钟），与 meal_buffer_minutes 不同",
        ),
    )

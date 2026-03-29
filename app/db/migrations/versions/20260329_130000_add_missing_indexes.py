"""add missing indexes for rotation and active entity filtering

Revision ID: 20260329_130000
Revises: 20260329_120000
Create Date: 2026-03-29
"""
from alembic import op

revision = "20260329_130000"
down_revision = "20260329_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_entity_base_recommendation_count",
        "entity_base",
        ["recommendation_count_30d"],
    )
    op.create_index(
        "ix_entity_base_is_active",
        "entity_base",
        ["is_active"],
    )


def downgrade() -> None:
    op.drop_index("ix_entity_base_is_active", table_name="entity_base")
    op.drop_index("ix_entity_base_recommendation_count", table_name="entity_base")

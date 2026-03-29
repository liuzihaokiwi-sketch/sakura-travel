"""entity_base: add last_refreshed_at

Revision ID: 20260329_110000
Revises: 20260329_100000
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa

revision = "20260329_110000"
down_revision = "20260329_100000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "entity_base",
        sa.Column(
            "last_refreshed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="上次 AI 刷新实体数据的时间，用于定时更新调度",
        ),
    )
    op.create_index(
        "ix_entity_base_last_refreshed_at",
        "entity_base",
        ["last_refreshed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_entity_base_last_refreshed_at", table_name="entity_base")
    op.drop_column("entity_base", "last_refreshed_at")

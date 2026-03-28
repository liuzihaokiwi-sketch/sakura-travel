"""add recommendation_count_30d to entity_base

Revision ID: 20260328_120000
Revises: 20260328_110000
Create Date: 2026-03-28 12:00:00.000000

新增字段：
  entity_base.recommendation_count_30d  int — 过去30天该实体被推荐进行程的次数
  entity_base.last_recommended_at       timestamp — 最后一次被推荐的时间（用于轮转衰减计算）
"""

from alembic import op
import sqlalchemy as sa


revision = "20260328_120000"
down_revision = "20260328_110000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "entity_base",
        sa.Column(
            "recommendation_count_30d",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="过去30天被推荐进行程的次数（轮转机制依赖此字段）"
        ),
    )
    op.add_column(
        "entity_base",
        sa.Column(
            "last_recommended_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="最后一次被推荐的时间"
        ),
    )
    op.create_index(
        "ix_entity_base_rec_count",
        "entity_base",
        ["recommendation_count_30d"],
    )


def downgrade() -> None:
    op.drop_index("ix_entity_base_rec_count", table_name="entity_base")
    op.drop_column("entity_base", "last_recommended_at")
    op.drop_column("entity_base", "recommendation_count_30d")

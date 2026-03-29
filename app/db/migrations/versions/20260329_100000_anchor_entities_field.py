"""activity_cluster: add anchor_entities JSONB field

Revision ID: 20260329_100000
Revises: 20260328_150000
Create Date: 2026-03-29 10:00:00.000000

核心实体声明字段。每个活动簇直接声明它需要的景点/餐厅/酒店列表，
格式: [{"name":"清水寺","type":"poi","role":"anchor"}, ...]

不再依赖从 notes 自由文本反推。
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "20260329_100000"
down_revision = "20260328_150000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "activity_clusters",
        sa.Column(
            "anchor_entities",
            JSONB,
            nullable=True,
            comment='核心实体列表 [{"name":"富士山五合目","type":"poi","role":"anchor"},...]',
        ),
    )


def downgrade() -> None:
    op.drop_column("activity_clusters", "anchor_entities")

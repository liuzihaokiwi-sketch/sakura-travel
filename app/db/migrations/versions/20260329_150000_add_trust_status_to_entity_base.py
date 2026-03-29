"""entity_base: add trust_status fields

Revision ID: 20260329_150000
Revises: 5687d628fc36
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa

revision = "20260329_150000"
down_revision = "5687d628fc36"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "entity_base",
        sa.Column(
            "trust_status",
            sa.String(20),
            nullable=False,
            server_default="unverified",
            comment="verified / unverified / ai_generated / suspicious / rejected",
        ),
    )
    op.add_column("entity_base", sa.Column("verified_by", sa.String(100), nullable=True))
    op.add_column("entity_base", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("entity_base", sa.Column("trust_note", sa.Text, nullable=True))

    op.create_index("ix_entity_base_trust_status", "entity_base", ["trust_status"])

    # 已存在的 AI 生成数据（data_tier='B' 且无外部 ID）标记为 ai_generated
    op.execute(
        """
        UPDATE entity_base
        SET trust_status = 'ai_generated'
        WHERE data_tier = 'B'
          AND google_place_id IS NULL
          AND tabelog_id IS NULL
        """
    )
    # OSM / Tabelog 爬取的（data_tier='A'）标记为 unverified（已是 server_default，此语句可省略，但明确化）
    op.execute(
        """
        UPDATE entity_base
        SET trust_status = 'unverified'
        WHERE data_tier = 'A'
        """
    )


def downgrade() -> None:
    op.drop_index("ix_entity_base_trust_status", table_name="entity_base")
    op.drop_column("entity_base", "trust_note")
    op.drop_column("entity_base", "verified_at")
    op.drop_column("entity_base", "verified_by")
    op.drop_column("entity_base", "trust_status")

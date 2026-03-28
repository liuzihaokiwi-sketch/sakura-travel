"""add marketing_attribution table and utm fields to trip_requests

Revision ID: 20260328_130000
Revises: 20260328_120000
Create Date: 2026-03-28 13:00:00.000000

新增内容：
  marketing_attribution 表 — 记录每个 trip_request 的营销来源
  字段：utm_source, utm_medium, utm_campaign, utm_content, referral_code, landing_page, from_tool
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "20260328_130000"
down_revision = "20260328_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marketing_attribution",
        sa.Column("attr_id", sa.BigInteger(), autoincrement=True, nullable=False, primary_key=True),
        sa.Column(
            "trip_request_id",
            UUID(as_uuid=True),
            sa.ForeignKey("trip_requests.trip_request_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # UTM 参数
        sa.Column("utm_source", sa.String(100), nullable=True, comment="如 xhs / douyin / google / direct"),
        sa.Column("utm_medium", sa.String(100), nullable=True, comment="如 social / organic / cpc"),
        sa.Column("utm_campaign", sa.String(200), nullable=True, comment="如 sakura_2026 / kansai_ramen"),
        sa.Column("utm_content", sa.String(200), nullable=True, comment="具体内容标识，如帖子ID"),
        # 简化 from 参数
        sa.Column("from_tool", sa.String(100), nullable=True, comment="如 sakura_tool / budget_tool / koyo_tool"),
        sa.Column("referral_code", sa.String(100), nullable=True, comment="老用户推荐码"),
        sa.Column("landing_page", sa.String(500), nullable=True, comment="用户进来时的落地页 URL"),
        sa.Column("referrer", sa.String(500), nullable=True, comment="HTTP Referer"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("trip_request_id", name="uq_attribution_trip_request"),
    )

    op.create_index(
        "ix_marketing_attribution_utm_source",
        "marketing_attribution",
        ["utm_source"],
    )
    op.create_index(
        "ix_marketing_attribution_from_tool",
        "marketing_attribution",
        ["from_tool"],
    )
    op.create_index(
        "ix_marketing_attribution_referral",
        "marketing_attribution",
        ["referral_code"],
    )


def downgrade() -> None:
    op.drop_index("ix_marketing_attribution_referral", table_name="marketing_attribution")
    op.drop_index("ix_marketing_attribution_from_tool", table_name="marketing_attribution")
    op.drop_index("ix_marketing_attribution_utm_source", table_name="marketing_attribution")
    op.drop_table("marketing_attribution")

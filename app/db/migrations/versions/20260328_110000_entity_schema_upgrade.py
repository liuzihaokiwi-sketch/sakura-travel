"""entity schema upgrade: quality_tier, budget_tier, risk_flags, booking_method, etc.

Revision ID: 20260328_110000
Revises: 20260328_100000
Create Date: 2026-03-28 11:00:00.000000

新增字段说明：
  entity_base:
    quality_tier       S/A/B/C — 内容深度等级，用于规划权重和自动发布门槛
    budget_tier        free/budget/mid/premium/luxury — 统一预算分层（取代各表分散的 price_band）
    risk_flags         JSONB list — 风险标签，如 ['requires_reservation','seasonal_closure','long_queue']
    booking_method     walk_in / online_advance / phone / impossible — 主要预约方式
    best_time_of_day   morning/afternoon/evening/anytime — 最佳游览时段
    visit_duration_min int — 建议游览时长（分钟），替代 typical_duration_baseline

  pois:
    advance_booking_days  int — 建议提前预约天数
    booking_url           text — 官方预约链接
    queue_wait_typical_min int — 典型排队时间（分钟）

  restaurants:
    advance_booking_days  int
    booking_url           text
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260328_110000"
down_revision = "20260328_100000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── entity_base 新增字段 ───────────────────────────────────────────────────
    op.add_column(
        "entity_base",
        sa.Column(
            "quality_tier",
            sa.String(1),
            nullable=True,
            comment="S/A/B/C — 内容深度等级"
        ),
    )
    op.add_column(
        "entity_base",
        sa.Column(
            "budget_tier",
            sa.String(10),
            nullable=True,
            comment="free/budget/mid/premium/luxury"
        ),
    )
    op.add_column(
        "entity_base",
        sa.Column(
            "risk_flags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
            comment="['requires_reservation','seasonal_closure','long_queue',...]"
        ),
    )
    op.add_column(
        "entity_base",
        sa.Column(
            "booking_method",
            sa.String(20),
            nullable=True,
            comment="walk_in/online_advance/phone/impossible"
        ),
    )
    op.add_column(
        "entity_base",
        sa.Column(
            "best_time_of_day",
            sa.String(20),
            nullable=True,
            comment="morning/afternoon/evening/night/anytime"
        ),
    )
    op.add_column(
        "entity_base",
        sa.Column(
            "visit_duration_min",
            sa.SmallInteger(),
            nullable=True,
            comment="建议游览时长（分钟），汇总值"
        ),
    )

    # 将已有 data_tier 值回填到 quality_tier（向后兼容）
    op.execute(
        sa.text("UPDATE entity_base SET quality_tier = data_tier WHERE quality_tier IS NULL")
    )
    # 将已有 price_band 回填到 budget_tier
    op.execute(
        sa.text("UPDATE entity_base SET budget_tier = price_band WHERE budget_tier IS NULL AND price_band IS NOT NULL")
    )

    # 创建索引
    op.create_index("ix_entity_base_quality_tier", "entity_base", ["quality_tier"])
    op.create_index("ix_entity_base_budget_tier", "entity_base", ["budget_tier"])
    op.create_index(
        "ix_entity_base_booking_method", "entity_base", ["booking_method"]
    )

    # ── pois 新增字段 ──────────────────────────────────────────────────────────
    op.add_column(
        "pois",
        sa.Column(
            "advance_booking_days",
            sa.SmallInteger(),
            nullable=True,
            comment="建议提前预约天数（0=当天，-1=无需预约）"
        ),
    )
    op.add_column(
        "pois",
        sa.Column(
            "booking_url",
            sa.Text(),
            nullable=True,
            comment="官方预约/购票链接"
        ),
    )
    op.add_column(
        "pois",
        sa.Column(
            "queue_wait_typical_min",
            sa.SmallInteger(),
            nullable=True,
            comment="典型排队等候时间（分钟）"
        ),
    )

    # ── restaurants 新增字段 ───────────────────────────────────────────────────
    op.add_column(
        "restaurants",
        sa.Column(
            "advance_booking_days",
            sa.SmallInteger(),
            nullable=True,
            comment="建议提前预约天数"
        ),
    )
    op.add_column(
        "restaurants",
        sa.Column(
            "booking_url",
            sa.Text(),
            nullable=True,
            comment="官方预约链接（如 Tablecheck / Omakase）"
        ),
    )


def downgrade() -> None:
    op.drop_column("restaurants", "booking_url")
    op.drop_column("restaurants", "advance_booking_days")

    op.drop_column("pois", "queue_wait_typical_min")
    op.drop_column("pois", "booking_url")
    op.drop_column("pois", "advance_booking_days")

    op.drop_index("ix_entity_base_booking_method", table_name="entity_base")
    op.drop_index("ix_entity_base_budget_tier", table_name="entity_base")
    op.drop_index("ix_entity_base_quality_tier", table_name="entity_base")

    op.drop_column("entity_base", "visit_duration_min")
    op.drop_column("entity_base", "best_time_of_day")
    op.drop_column("entity_base", "booking_method")
    op.drop_column("entity_base", "risk_flags")
    op.drop_column("entity_base", "budget_tier")
    op.drop_column("entity_base", "quality_tier")

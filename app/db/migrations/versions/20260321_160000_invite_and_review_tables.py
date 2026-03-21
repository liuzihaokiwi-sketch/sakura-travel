"""invite_and_review_tables

Revision ID: 20260321_160000
Revises: 20260321_150000
Create Date: 2026-03-21 16:00:00

- invite_codes        — T29 老客带新邀请码
- invite_rewards      — T29 邀请返现记录
- plan_review_reports — T22-T25 多模型评审结果
- entity_data_conflicts — T26 数据冲突待审记录
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260321_160000"
down_revision = "20260321_150000"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ── T29: invite_codes ────────────────────────────────────────────────────
    op.create_table(
        "invite_codes",
        sa.Column("invite_code", sa.String(20), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True)),
        sa.Column("discount_cny", sa.Numeric(6, 2), nullable=False, default=50),
        sa.Column("reward_cny", sa.Numeric(6, 2), nullable=False, default=50),
        sa.Column("max_uses", sa.SmallInteger, nullable=False, default=10),
        sa.Column("total_uses", sa.SmallInteger, nullable=False, default=0),
        sa.Column("total_reward_cny", sa.Numeric(8, 2), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_invite_codes_order", "invite_codes", ["order_id"])
    op.create_index("ix_invite_codes_user", "invite_codes", ["user_id"])

    # ── T29: invite_rewards ──────────────────────────────────────────────────
    op.create_table(
        "invite_rewards",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("invite_code", sa.String(20), nullable=False),
        sa.Column("triggered_order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("reward_cny", sa.Numeric(6, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="pending",
                  comment="pending/credited/expired"),
        sa.Column("credited_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_invite_rewards_code", "invite_rewards", ["invite_code"])
    op.create_index("ix_invite_rewards_status", "invite_rewards", ["status"])

    # ── 为 orders 表添加邀请码字段 ────────────────────────────────────────────
    op.add_column("orders", sa.Column("invite_code_used", sa.String(20)))
    op.add_column("orders", sa.Column("discount_applied_cny", sa.Numeric(6, 2)))

    # ── T22-T25: plan_review_reports ─────────────────────────────────────────
    op.create_table(
        "plan_review_reports",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("plan_id", UUID(as_uuid=True), nullable=False),
        sa.Column("overall_score", sa.Numeric(4, 2), nullable=False),
        sa.Column("passed", sa.Boolean, nullable=False),
        sa.Column("blocker_count", sa.SmallInteger, nullable=False, default=0),
        sa.Column("warning_count", sa.SmallInteger, nullable=False, default=0),
        sa.Column("summary", sa.Text),
        sa.Column("comments", JSONB, comment="四个模型的评论列表"),
        sa.Column("slot_boundaries", JSONB, comment="T25 每个 slot 的可微调边界"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_prr_plan", "plan_review_reports", ["plan_id"])
    op.create_index("ix_prr_passed", "plan_review_reports", ["passed"])

    # ── T26: entity_data_conflicts ───────────────────────────────────────────
    op.create_table(
        "entity_data_conflicts",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("old_data", JSONB),
        sa.Column("new_data", JSONB),
        sa.Column("conflicts", JSONB),
        sa.Column("resolved", sa.Boolean, default=False),
        sa.Column("resolved_by", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_edc_entity", "entity_data_conflicts", ["entity_id"])
    op.create_index("ix_edc_resolved", "entity_data_conflicts", ["resolved"])


def downgrade() -> None:
    op.drop_table("entity_data_conflicts")
    op.drop_table("plan_review_reports")
    op.drop_column("orders", "discount_applied_cny")
    op.drop_column("orders", "invite_code_used")
    op.drop_table("invite_rewards")
    op.drop_table("invite_codes")

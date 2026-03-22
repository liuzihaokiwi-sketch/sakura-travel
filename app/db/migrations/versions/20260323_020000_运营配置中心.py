"""运营配置中心 5 张表

Revision ID: 20260323_020000
Revises: 20260323_010000
Create Date: 2026-03-23 02:00:00
"""
from __future__ import annotations
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260323_020000"
down_revision = "20260323_010000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "config_packs",
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("pack_type", sa.String(30), nullable=False, server_default="weights"),
        sa.Column("active_version_no", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_config_packs_status", "config_packs", ["status"])
    op.create_index("ix_config_packs_pack_type", "config_packs", ["pack_type"])

    op.create_table(
        "config_pack_versions",
        sa.Column("version_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("config_packs.pack_id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer, nullable=False),
        sa.Column("weights", postgresql.JSONB, nullable=True),
        sa.Column("thresholds", postgresql.JSONB, nullable=True),
        sa.Column("switches", postgresql.JSONB, nullable=True),
        sa.Column("hard_rules", postgresql.JSONB, nullable=True),
        sa.Column("change_summary", sa.Text, nullable=True),
        sa.Column("changed_fields", postgresql.JSONB, nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preview_run_ids", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_cpv_pack_version", "config_pack_versions", ["pack_id", "version_no"], unique=True)

    op.create_table(
        "config_scopes",
        sa.Column("scope_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("config_packs.pack_id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope_type", sa.String(20), nullable=False),
        sa.Column("scope_value", sa.String(100), nullable=True),
        sa.Column("rollout_pct", sa.Numeric(4, 3), nullable=False, server_default="1.0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_config_scopes_type_value", "config_scopes", ["scope_type", "scope_value"])
    op.create_index("ix_config_scopes_active", "config_scopes", ["is_active"])

    op.create_table(
        "config_preview_runs",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("config_packs.pack_id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer, nullable=False),
        sa.Column("subject_type", sa.String(20), nullable=False),
        sa.Column("subject_id", sa.String(100), nullable=False),
        sa.Column("baseline_result", postgresql.JSONB, nullable=True),
        sa.Column("candidate_result", postgresql.JSONB, nullable=True),
        sa.Column("diff_summary", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_cpr_pack_id", "config_preview_runs", ["pack_id"])
    op.create_index("ix_cpr_subject", "config_preview_runs", ["subject_type", "subject_id"])
    op.create_index("ix_cpr_status", "config_preview_runs", ["status"])

    op.create_table(
        "config_release_records",
        sa.Column("record_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("config_packs.pack_id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer, nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("rollback_to_version_no", sa.Integer, nullable=True),
        sa.Column("rollback_reason", sa.Text, nullable=True),
        sa.Column("rollout_scope", postgresql.JSONB, nullable=True),
        sa.Column("preview_run_ids", postgresql.JSONB, nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_crr_pack_id", "config_release_records", ["pack_id"])
    op.create_index("ix_crr_action", "config_release_records", ["action"])
    op.create_index("ix_crr_created_at", "config_release_records", ["created_at"])


def downgrade() -> None:
    op.drop_table("config_release_records")
    op.drop_table("config_preview_runs")
    op.drop_table("config_scopes")
    op.drop_table("config_pack_versions")
    op.drop_table("config_packs")

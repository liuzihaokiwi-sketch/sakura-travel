"""A1: data_source_registry + entity_source_scores + city_data_coverage + city_food_specialties + discovery_candidates

Revision ID: 20260330_200000
Revises: 5687d628fc36
Create Date: 2026-03-30 20:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260330_200000"
down_revision = "5687d628fc36"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── data_source_registry ──────────────────────────────────────────────────
    op.create_table(
        "data_source_registry",
        sa.Column("source_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_name", sa.String(50), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False,
                  comment="rating / infrastructure / perception / official"),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("coverage", postgresql.JSONB(), nullable=True),
        sa.Column("entity_types", postgresql.JSONB(), nullable=True),
        sa.Column("priority", sa.SmallInteger(), nullable=False, server_default="50"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("rate_limit", postgresql.JSONB(), nullable=True),
        sa.Column("auth_config", postgresql.JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("source_id"),
        sa.UniqueConstraint("source_name"),
    )
    op.create_index("ix_data_source_registry_source_type",
                    "data_source_registry", ["source_type"])

    # ── entity_source_scores ──────────────────────────────────────────────────
    op.create_table(
        "entity_source_scores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_name", sa.String(50), nullable=False),
        sa.Column("raw_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("normalized_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["entity_id"], ["entity_base.entity_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entity_id", "source_name", name="uq_entity_source"),
    )
    op.create_index("ix_entity_source_scores_entity_id",
                    "entity_source_scores", ["entity_id"])
    op.create_index("ix_entity_source_scores_source_name",
                    "entity_source_scores", ["source_name"])

    # ── city_data_coverage ────────────────────────────────────────────────────
    op.create_table(
        "city_data_coverage",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("city_code", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("sub_category", sa.String(50), nullable=True),
        sa.Column("target_count", sa.Integer(), nullable=False),
        sa.Column("current_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sources_used", postgresql.JSONB(), nullable=True),
        sa.Column("sources_pending", postgresql.JSONB(), nullable=True),
        sa.Column("last_updated", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_code", "entity_type", "sub_category",
                            name="uq_city_coverage"),
    )
    op.create_index("ix_city_data_coverage_city_code",
                    "city_data_coverage", ["city_code"])

    # ── city_food_specialties ─────────────────────────────────────────────────
    op.create_table(
        "city_food_specialties",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("city_code", sa.String(50), nullable=False),
        sa.Column("cuisine", sa.String(100), nullable=False),
        sa.Column("cuisine_en", sa.String(100), nullable=True),
        sa.Column("cuisine_ja", sa.String(100), nullable=True),
        sa.Column("importance", sa.String(20), nullable=False, server_default="'regional'"),
        sa.Column("description_zh", sa.Text(), nullable=True),
        sa.Column("recommended_entities", postgresql.JSONB(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_code", "cuisine", name="uq_city_cuisine"),
    )
    op.create_index("ix_city_food_specialties_city_code",
                    "city_food_specialties", ["city_code"])

    # ── discovery_candidates ──────────────────────────────────────────────────
    op.create_table(
        "discovery_candidates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("city_code", sa.String(50), nullable=False),
        sa.Column("name_raw", sa.String(300), nullable=False),
        sa.Column("name_normalized", sa.String(300), nullable=True),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sources", postgresql.JSONB(), nullable=True),
        sa.Column("mention_contexts", postgresql.JSONB(), nullable=True),
        sa.Column("matched_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("match_confidence", sa.Numeric(4, 2), nullable=True),
        sa.Column("entity_type_guess", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="'pending'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["matched_entity_id"], ["entity_base.entity_id"],
                                ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_discovery_candidates_city_code",
                    "discovery_candidates", ["city_code"])
    op.create_index("ix_discovery_candidates_source_count",
                    "discovery_candidates", ["source_count"])


def downgrade() -> None:
    op.drop_table("discovery_candidates")
    op.drop_table("city_food_specialties")
    op.drop_table("city_data_coverage")
    op.drop_table("entity_source_scores")
    op.drop_table("data_source_registry")

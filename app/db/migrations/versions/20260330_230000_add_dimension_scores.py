"""C2: add dimension_scores JSONB to entity_review_signals

Revision ID: 20260330_230000
Revises: 99d548c6b876
Create Date: 2026-03-30 23:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260330_230000"
down_revision = "99d548c6b876"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "entity_review_signals",
        sa.Column("dimension_scores", postgresql.JSONB(astext_type=sa.Text()),
                  nullable=True,
                  comment="Per-type dimension scores extracted from reviews"),
    )


def downgrade() -> None:
    op.drop_column("entity_review_signals", "dimension_scores")

"""Drop deprecated tables: preview_trigger_scores, swap_candidate_soft_scores,
stage_weight_packs, product_config, feature_flags, user_events

Revision ID: 20260330_100000
Revises: 20260329_150000
Create Date: 2026-03-30
"""
from alembic import op

revision = "20260330_100000"
down_revision = "20260329_150000"
branch_labels = None
depends_on = None

_TABLES = [
    "preview_trigger_scores",
    "swap_candidate_soft_scores",
    "stage_weight_packs",
    "product_config",
    "feature_flags",
    "user_events",
]


def upgrade() -> None:
    for table in _TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")


def downgrade() -> None:
    # 这些表均为废弃表，downgrade 不重建
    pass

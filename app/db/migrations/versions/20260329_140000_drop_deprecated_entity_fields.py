"""drop deprecated entity_base fields (best_time_of_day, visit_duration_min, price_band, operating_stability_level)

These fields are duplicated by other tables or never consumed by domain logic:
- best_time_of_day → use entity_temporal_profiles.best_time_window
- visit_duration_min → use pois.typical_duration_min
- price_band → use budget_tier
- operating_stability_level → use EntitySignals.operational_stability_score

Revision ID: 20260329_140000
Revises: 20260329_130000
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa

revision = "20260329_140000"
down_revision = "20260329_130000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("entity_base", "best_time_of_day")
    op.drop_column("entity_base", "visit_duration_min")
    op.drop_column("entity_base", "price_band")
    op.drop_column("entity_base", "operating_stability_level")


def downgrade() -> None:
    op.add_column("entity_base", sa.Column(
        "operating_stability_level", sa.String(10), nullable=True,
        comment="stable / moderate / volatile",
    ))
    op.add_column("entity_base", sa.Column(
        "price_band", sa.String(10), nullable=True,
        comment="free / budget / mid / premium / luxury",
    ))
    op.add_column("entity_base", sa.Column(
        "visit_duration_min", sa.SmallInteger(), nullable=True,
        comment="建议游览时长汇总（分钟）",
    ))
    op.add_column("entity_base", sa.Column(
        "best_time_of_day", sa.String(20), nullable=True,
        comment="morning/afternoon/evening/night/anytime — 最佳游览时段",
    ))

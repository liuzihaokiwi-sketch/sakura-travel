"""add budget_focus to trip_profiles

Revision ID: 20260321_210000
Revises: 20260321_160000_invite_and_review_tables
Create Date: 2026-03-21 21:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20260321_210000'
down_revision = '20260321_160000_invite_and_review_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'trip_profiles',
        sa.Column(
            'budget_focus',
            sa.String(30),
            nullable=True,
            comment='better_stay / better_food / better_experience / balanced / best_value',
        ),
    )


def downgrade() -> None:
    op.drop_column('trip_profiles', 'budget_focus')

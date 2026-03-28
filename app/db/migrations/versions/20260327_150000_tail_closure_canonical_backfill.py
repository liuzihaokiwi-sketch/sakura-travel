"""backfill canonical detail-form runtime fields from legacy compatibility columns

Revision ID: 20260327_150000
Revises: 20260327_120000
Create Date: 2026-03-27 15:00:00.000000
"""

from alembic import op


revision = "20260327_150000"
down_revision = "20260327_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE detail_forms
        SET must_visit_places = COALESCE(must_visit_places, must_go_places)
        WHERE must_visit_places IS NULL
          AND must_go_places IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE detail_forms
        SET do_not_go_places = COALESCE(do_not_go_places, dont_want_places)
        WHERE do_not_go_places IS NULL
          AND dont_want_places IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE detail_forms
        SET booked_items = booked_hotels
        WHERE booked_items IS NULL
          AND booked_hotels IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE detail_forms
        SET booked_items = NULL,
            do_not_go_places = NULL
        """
    )

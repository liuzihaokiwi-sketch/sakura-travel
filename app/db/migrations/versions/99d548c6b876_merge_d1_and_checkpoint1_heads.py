"""merge D1 and checkpoint1 heads

Revision ID: 99d548c6b876
Revises: 20260330_100000, 20260330_220000
Create Date: 2026-03-30 14:16:53.763838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99d548c6b876'
down_revision: Union[str, Sequence[str], None] = ('20260330_100000', '20260330_220000')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

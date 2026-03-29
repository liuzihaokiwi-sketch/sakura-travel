"""merge migration heads

Revision ID: 5687d628fc36
Revises: 20260327_150000, 20260329_140000, 204fa6789b76
Create Date: 2026-03-29 12:35:01.452387

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5687d628fc36'
down_revision: Union[str, Sequence[str], None] = ('20260327_150000', '20260329_140000', '204fa6789b76')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

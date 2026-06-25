"""repair known classification topic match status

Revision ID: 9fdaa002a54b
Revises: 725f8e5aa178
Create Date: 2026-06-25 19:15:23.151009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fdaa002a54b'
down_revision: Union[str, Sequence[str], None] = '725f8e5aa178'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        UPDATE classification_events
        SET topic_match_status = 'not_applicable'
        WHERE classification_status = 'known'
          AND topic_match_status <> 'not_applicable'
        """
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""add complaint embedding hnsw index

Revision ID: a27f7ff8c685
Revises: 23b9416d5a9d
Create Date: 2026-06-25 11:46:20.648371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a27f7ff8c685'
down_revision: Union[str, Sequence[str], None] = '23b9416d5a9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_complaints_embedding_hnsw
        ON complaints
        USING hnsw (embedding vector_cosine_ops)
        WHERE embedding IS NOT NULL
        """
    )    
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_complaints_embedding_hnsw")
    pass

"""add spin and batna analysis text blocks

Revision ID: 79b1c66f3d7b
Revises: a7cccd80c0e7
Create Date: 2026-09-22 20:22:09.394331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79b1c66f3d7b'
down_revision: Union[str, Sequence[str], None] = 'a7cccd80c0e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('analysis_reports', sa.Column('spin_analysis', sa.Text(), nullable=True))
    op.add_column('analysis_reports', sa.Column('batna_analysis', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('analysis_reports', 'batna_analysis')
    op.drop_column('analysis_reports', 'spin_analysis')

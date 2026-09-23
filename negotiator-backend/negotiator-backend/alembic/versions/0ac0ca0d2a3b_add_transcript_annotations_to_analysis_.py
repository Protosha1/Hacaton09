"""add transcript_annotations to analysis_reports

Revision ID: 0ac0ca0d2a3b
Revises: 79b1c66f3d7b
Create Date: 2026-09-22 20:34:34.766687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ac0ca0d2a3b'
down_revision: Union[str, Sequence[str], None] = '79b1c66f3d7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'analysis_reports',
        sa.Column('transcript_annotations', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('analysis_reports', 'transcript_annotations')

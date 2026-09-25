"""add xp_earned and is_perfect to analysis

Revision ID: daf2664f5f09
Revises: 34a8230cbc0e
Create Date: 2026-09-22 15:32:05.625388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'daf2664f5f09'
down_revision: Union[str, Sequence[str], None] = '34a8230cbc0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'analysis_reports',
        sa.Column('xp_earned', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'analysis_reports',
        sa.Column('is_perfect', sa.Boolean(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    op.drop_column('analysis_reports', 'is_perfect')
    op.drop_column('analysis_reports', 'xp_earned')

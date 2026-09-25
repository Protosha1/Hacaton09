"""add consent_given to users

Revision ID: 0daea6f90477
Revises: 0ac0ca0d2a3b
Create Date: 2026-09-22 20:54:36.412838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0daea6f90477'
down_revision: Union[str, Sequence[str], None] = '0ac0ca0d2a3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('consent_given', sa.Boolean(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'consent_given')

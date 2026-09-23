"""add avatar_url to users

Revision ID: 87a8855ff024
Revises: 0daea6f90477
Create Date: 2026-09-22 21:24:45.966722

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87a8855ff024'
down_revision: Union[str, Sequence[str], None] = '0daea6f90477'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'avatar_url')

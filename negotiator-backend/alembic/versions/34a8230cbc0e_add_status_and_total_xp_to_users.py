"""add status and total_xp to users

Revision ID: 34a8230cbc0e
Revises: de2c6c2820e3
Create Date: 2026-09-22 14:52:59.746023

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34a8230cbc0e'
down_revision: Union[str, Sequence[str], None] = 'de2c6c2820e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending_onboarding')
    )
    op.create_index('ix_users_status', 'users', ['status'], unique=False)
    op.add_column(
        'users',
        sa.Column('total_xp', sa.Integer(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'total_xp')
    op.drop_index('ix_users_status', table_name='users')
    op.drop_column('users', 'status')

"""add admin fields to scenarios and user_added_cases

Revision ID: a7cccd80c0e7
Revises: 4f77ec0c404e
Create Date: 2026-09-22 20:08:51.172220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7cccd80c0e7'
down_revision: Union[str, Sequence[str], None] = '4f77ec0c404e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create user_added_cases table
    op.create_table(
        'user_added_cases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('case_id', sa.String(length=36), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['case_id'], ['scenarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'case_id', name='uq_user_added_case'),
    )
    op.create_index(op.f('ix_user_added_cases_user_id'), 'user_added_cases', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_added_cases_case_id'), 'user_added_cases', ['case_id'], unique=False)

    # Add new columns to scenarios
    op.add_column('scenarios', sa.Column('tone_behavior', sa.Text(), nullable=True))
    op.add_column('scenarios', sa.Column('non_standard_case', sa.Text(), nullable=True))
    op.add_column('scenarios', sa.Column('admin_id', sa.String(length=36), nullable=True))
    op.add_column(
        'scenarios',
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ready')
    )
    op.add_column('scenarios', sa.Column('invite_code', sa.String(length=50), nullable=True))

    # Indexes
    op.create_index(op.f('ix_scenarios_admin_id'), 'scenarios', ['admin_id'], unique=False)
    op.create_index(op.f('ix_scenarios_status'), 'scenarios', ['status'], unique=False)
    op.create_index(op.f('ix_scenarios_invite_code'), 'scenarios', ['invite_code'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_scenarios_invite_code'), table_name='scenarios')
    op.drop_index(op.f('ix_scenarios_status'), table_name='scenarios')
    op.drop_index(op.f('ix_scenarios_admin_id'), table_name='scenarios')
    op.drop_column('scenarios', 'invite_code')
    op.drop_column('scenarios', 'status')
    op.drop_column('scenarios', 'admin_id')
    op.drop_column('scenarios', 'non_standard_case')
    op.drop_column('scenarios', 'tone_behavior')

    op.drop_index(op.f('ix_user_added_cases_case_id'), table_name='user_added_cases')
    op.drop_index(op.f('ix_user_added_cases_user_id'), table_name='user_added_cases')
    op.drop_table('user_added_cases')
"""Add projects table

Revision ID: 2058bf4fb6ff
Revises: c4a95565f41c
Create Date: 2026-01-26 14:55:31.640516

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2058bf4fb6ff'
down_revision: Union[str, Sequence[str], None] = 'c4a95565f41c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create projects table with all required fields
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=5000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    # Create index on user_id for multi-tenancy queries
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop projects table
    op.drop_index(op.f('ix_projects_user_id'), table_name='projects')
    op.drop_table('projects')

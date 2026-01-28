"""Add habits tables.

Story 7.1: Simple Habit Tracker

Create habits and habit_completions tables for habit tracking functionality.

Revision ID: 002_add_habits_tables
Revises: (previous migration)
Create Date: 2026-01-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_habits_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create habits and habit_completions tables."""
    
    # Create habits table
    op.create_table(
        'habits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='Habits table for simple habit tracking (Story 7.1)'
    )
    
    # Create habit_completions table
    op.create_table(
        'habit_completions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('habit_id', sa.Integer(), nullable=False),
        sa.Column('completion_date', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['habit_id'], ['habits.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('habit_id', 'completion_date', name='unique_habit_completion'),
        comment='Habit completions tracking (Story 7.1)'
    )
    
    # Create index for frequent queries
    op.create_index('idx_habit_completions_habit_id_date',
                    'habit_completions',
                    ['habit_id', 'completion_date'])


def downgrade():
    """Drop habits and habit_completions tables."""
    op.drop_index('idx_habit_completions_habit_id_date', table_name='habit_completions')
    op.drop_table('habit_completions')
    op.drop_table('habits')

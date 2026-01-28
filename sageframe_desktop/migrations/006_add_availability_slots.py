"""Add availability_slots table.

Revision ID: 006
Revises: 005
Create Date: 2026-01-27

This migration creates the availability_slots table for storing computed
free and busy time periods from calendar events.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create availability_slots table."""
    
    op.create_table(
        'availability_slots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('event_summary', sa.Text(), nullable=True),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['calendar_connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['calendar_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient time-range queries
    op.create_index(op.f('ix_availability_slots_connection_id'), 'availability_slots', ['connection_id'], unique=False)
    op.create_index(op.f('ix_availability_slots_start_time'), 'availability_slots', ['start_time'], unique=False)
    op.create_index(op.f('ix_availability_slots_end_time'), 'availability_slots', ['end_time'], unique=False)
    op.create_index(op.f('ix_availability_slots_status'), 'availability_slots', ['status'], unique=False)
    
    # Composite index for time range + status queries
    op.create_index(
        'ix_availability_time_range_status',
        'availability_slots',
        ['connection_id', 'start_time', 'end_time', 'status'],
        unique=False
    )


def downgrade() -> None:
    """Drop availability_slots table."""
    op.drop_index('ix_availability_time_range_status', table_name='availability_slots')
    op.drop_index(op.f('ix_availability_slots_status'), table_name='availability_slots')
    op.drop_index(op.f('ix_availability_slots_end_time'), table_name='availability_slots')
    op.drop_index(op.f('ix_availability_slots_start_time'), table_name='availability_slots')
    op.drop_index(op.f('ix_availability_slots_connection_id'), table_name='availability_slots')
    op.drop_table('availability_slots')

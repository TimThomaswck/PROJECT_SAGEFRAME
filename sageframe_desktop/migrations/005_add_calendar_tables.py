"""Add calendar integration tables.

Revision ID: 005
Revises: 004
Create Date: 2026-01-27

This migration creates tables for calendar integration:
- calendar_connections: Stores OAuth connections to external calendars
- calendar_events: Stores synchronized calendar events
- sync_logs: Tracks sync operations and errors
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create calendar integration tables."""
    
    # Create calendar_connections table
    op.create_table(
        'calendar_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('connection_name', sa.String(length=200), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('calendar_id', sa.String(length=255), nullable=False),
        sa.Column('sync_enabled', sa.Integer(), nullable=False),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'user_email', 'calendar_id', name='uq_calendar_connection')
    )
    op.create_index(op.f('ix_calendar_connections_user_email'), 'calendar_connections', ['user_email'], unique=False)
    
    # Create calendar_events table
    op.create_table(
        'calendar_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('is_all_day', sa.Integer(), nullable=False),
        sa.Column('recurrence_rule', sa.Text(), nullable=True),
        sa.Column('attendees', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('last_modified', sa.DateTime(), nullable=False),
        sa.Column('sync_version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['calendar_connections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('connection_id', 'event_id', name='uq_calendar_event')
    )
    op.create_index(op.f('ix_calendar_events_connection_id'), 'calendar_events', ['connection_id'], unique=False)
    op.create_index(op.f('ix_calendar_events_start_time'), 'calendar_events', ['start_time'], unique=False)
    op.create_index(op.f('ix_calendar_events_end_time'), 'calendar_events', ['end_time'], unique=False)
    
    # Create sync_logs table
    op.create_table(
        'sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('sync_direction', sa.String(length=50), nullable=False),
        sa.Column('sync_status', sa.String(length=50), nullable=False),
        sa.Column('events_synced', sa.Integer(), nullable=False),
        sa.Column('events_failed', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sync_started_at', sa.DateTime(), nullable=False),
        sa.Column('sync_completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['calendar_connections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sync_logs_connection_id'), 'sync_logs', ['connection_id'], unique=False)


def downgrade() -> None:
    """Drop calendar integration tables."""
    op.drop_index(op.f('ix_sync_logs_connection_id'), table_name='sync_logs')
    op.drop_table('sync_logs')
    
    op.drop_index(op.f('ix_calendar_events_end_time'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_start_time'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_connection_id'), table_name='calendar_events')
    op.drop_table('calendar_events')
    
    op.drop_index(op.f('ix_calendar_connections_user_email'), table_name='calendar_connections')
    op.drop_table('calendar_connections')

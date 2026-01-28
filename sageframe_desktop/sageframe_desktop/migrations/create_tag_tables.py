"""Create tag and tagged_items tables for smart tagging system.

Revision ID: tag_management_001
Created: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'tag_management_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tag management tables."""
    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tag_name', sa.String(100), nullable=False, unique=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tag_name', name='uq_tag_name')
    )
    
    # Create index on tag_name for search performance
    op.create_index('ix_tags_tag_name', 'tags', ['tag_name'])
    
    # Create tagged_items table
    op.create_table(
        'tagged_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(50), nullable=False, server_default='task'),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tag_id', 'item_id', name='uq_tag_item')
    )
    
    # Create indexes for tagged_items
    op.create_index('ix_tagged_items_tag_id', 'tagged_items', ['tag_id'])
    op.create_index('ix_tagged_items_item_id', 'tagged_items', ['item_id'])
    op.create_index('ix_tagged_items_item_type', 'tagged_items', ['item_type'])


def downgrade() -> None:
    """Drop tag management tables."""
    op.drop_index('ix_tagged_items_item_type', table_name='tagged_items')
    op.drop_index('ix_tagged_items_item_id', table_name='tagged_items')
    op.drop_index('ix_tagged_items_tag_id', table_name='tagged_items')
    op.drop_table('tagged_items')
    
    op.drop_index('ix_tags_tag_name', table_name='tags')
    op.drop_table('tags')

"""Database migration to add performance indexes for tag filtering."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_tag_indexes'
down_revision = '003'  # Update this to match your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes for tag filtering performance."""
    # Index on tag_name for fast tag lookups
    op.create_index('idx_tags_tag_name', 'tags', ['tag_name'])
    
    # Index on junction table foreign keys for fast joins
    op.create_index('idx_tagged_items_tag_id', 'tagged_items', ['tag_id'])
    op.create_index('idx_tagged_items_item_id', 'tagged_items', ['item_id'])
    
    # Composite index for common query patterns
    op.create_index('idx_tagged_items_tag_item', 'tagged_items', ['tag_id', 'item_id'])


def downgrade():
    """Remove tag filtering indexes."""
    op.drop_index('idx_tagged_items_tag_item', table_name='tagged_items')
    op.drop_index('idx_tagged_items_item_id', table_name='tagged_items')
    op.drop_index('idx_tagged_items_tag_id', table_name='tagged_items')
    op.drop_index('idx_tags_tag_name', table_name='tags')

"""SQLAlchemy models for smart tag management.

This module defines the data models for tags and tagged items,
supporting the smart tagging system for automatic categorization.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Tag(Base):
    """Model for a smart tag (e.g., @movie, @book).
    
    Attributes:
        id: Primary key
        tag_name: The tag name without @ symbol (e.g., 'movie')
        category: Optional grouping for future use
        created_at: Timestamp of creation (ISO 8601 UTC)
        tagged_items: Relationship to TaggedItem entries
    """
    
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True)
    tag_name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to tagged items
    tagged_items = relationship("TaggedItem", back_populates="tag", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, tag_name={self.tag_name})>"


class TaggedItem(Base):
    """Junction table linking tags to captured items.
    
    Attributes:
        id: Primary key
        tag_id: Foreign key to Tag
        item_id: Foreign key to the item being tagged (generic, references various tables)
        item_type: Type of item (e.g., 'task', 'note', 'capture')
        content: Optional tag-specific content (e.g., title for @movie: Inception)
        created_at: Timestamp of tagging (ISO 8601 UTC)
        tag: Relationship to parent Tag
        enrichments: Relationship to TagEnrichment entries
    """
    
    __tablename__ = "tagged_items"
    
    id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, nullable=False, index=True)
    item_type = Column(String(50), nullable=False, default="task")  # e.g., 'task', 'note', 'capture'
    content = Column(Text, nullable=True)  # e.g., "Inception" for @movie: Inception
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Unique constraint to prevent duplicate tagging of same item
    __table_args__ = (UniqueConstraint("tag_id", "item_id", name="uq_tag_item"),)
    
    # Relationship to tag
    tag = relationship("Tag", back_populates="tagged_items")
    
    # Relationship to enrichments
    enrichments = relationship("TagEnrichment", back_populates="tagged_item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TaggedItem(tag_id={self.tag_id}, item_id={self.item_id}, item_type={self.item_type})>"


class TagEnrichment(Base):
    """Enrichment data for tagged items from external APIs.
    
    This table stores metadata fetched from external sources (TMDB, Google Books, etc.)
    and tracks the fetch status for each enrichment attempt.
    
    Attributes:
        id: Primary key
        tagged_item_id: Foreign key to TaggedItem
        api_provider: Name of the API provider (e.g., 'tmdb', 'google_books')
        enrichment_data: JSON blob containing the enriched metadata
        fetch_status: Status of enrichment ('pending', 'fetching', 'completed', 'failed')
        error_message: Error message if fetch_status is 'failed'
        fetched_at: Timestamp when enrichment was last fetched (ISO 8601 UTC)
        created_at: Timestamp when this enrichment record was created
        updated_at: Timestamp when this enrichment record was last updated
        tagged_item: Relationship to parent TaggedItem
    """
    
    __tablename__ = "tag_enrichments"
    
    id = Column(Integer, primary_key=True)
    tagged_item_id = Column(Integer, ForeignKey("tagged_items.id", ondelete="CASCADE"), nullable=False, index=True)
    api_provider = Column(String(50), nullable=False)  # e.g., 'tmdb', 'google_books'
    enrichment_data = Column(JSON, nullable=True)  # Stores metadata as JSON
    fetch_status = Column(String(20), nullable=False, default="pending")  # 'pending', 'fetching', 'completed', 'failed'
    error_message = Column(Text, nullable=True)  # Only set if fetch_status is 'failed'
    fetched_at = Column(DateTime, nullable=True)  # When the enrichment was fetched
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Unique constraint to prevent duplicate enrichments from same provider
    __table_args__ = (UniqueConstraint("tagged_item_id", "api_provider", name="uq_enrichment_provider"),)
    
    # Relationship to tagged item
    tagged_item = relationship("TaggedItem", back_populates="enrichments")
    
    def __repr__(self):
        return f"<TagEnrichment(tagged_item_id={self.tagged_item_id}, api_provider={self.api_provider}, status={self.fetch_status})>"

"""Service layer for tag management.

Provides CRUD operations, tag storage, and categorization logic.
Follows the same pattern as ProjectService and TaskService.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.modules.tag_management.filtering.models import TagFilter
from app.modules.tag_management.filtering.query_builder import FilterQueryBuilder

from app.database import SessionLocal
from app.modules.tag_management.models import Tag, TaggedItem
from app.modules.tag_management.parsers import TagParser


class TagSchema:
    """Simple schema validator for tag data."""
    
    def __init__(self, tag_name: str, category: Optional[str] = None):
        if not tag_name or not tag_name.strip():
            raise ValueError("Tag name cannot be empty")
        
        # Normalize: trim whitespace and lowercase
        normalized_tag = tag_name.strip().lower()
        
        if len(normalized_tag) > 100:
            raise ValueError("Tag name must be <= 100 characters")
        # Allow only alphanumeric, hyphens, underscores
        if not all(c.isalnum() or c in '-_' for c in normalized_tag):
            raise ValueError("Tag name can only contain letters, numbers, hyphens, and underscores")
        
        self.tag_name = normalized_tag
        self.category = category.lower().strip() if category else None


class TagService:
    """Service for tag CRUD, storage, and categorization operations."""
    
    # Optional global enrichment integration set by application startup
    _global_enrichment_integration = None

    @classmethod
    def set_global_enrichment_integration(cls, integration_obj) -> None:
        """Set a global enrichment integration used by all TagService instances.

        Args:
            integration_obj: Object with methods enrich_on_tag_created(tagged_item_id)
                             and enrich_on_tag_updated(tagged_item_id)
        """
        cls._global_enrichment_integration = integration_obj

    def __init__(self, session: Optional[Session] = None):
        """Initialize TagService.
        
        Args:
            session: Optional SQLAlchemy session. Creates new if not provided.
        """
        self._session = session
        self._owns_session = session is None
        if self._owns_session:
            self._session = SessionLocal()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
    
    def close(self):
        """Close the database session if owned by this service."""
        if self._owns_session and self._session:
            self._session.close()
            self._session = None
    
    @property
    def session(self) -> Session:
        """Get the database session."""
        if self._session is None:
            raise RuntimeError("Service session is closed")
        return self._session
    
    # Tag CRUD Operations
    
    def create_tag(self, tag_name: str, category: Optional[str] = None) -> Tag:
        """Create a new tag.
        
        Args:
            tag_name: Tag name (validated, lowercase)
            category: Optional category for grouping
            
        Returns:
            Created Tag object
            
        Raises:
            ValueError: If validation fails
        """
        try:
            validated = TagSchema(tag_name, category)
            
            # Check if tag already exists
            existing = self.session.query(Tag).filter_by(tag_name=validated.tag_name).first()
            if existing:
                return existing
            
            tag = Tag(
                tag_name=validated.tag_name,
                category=validated.category,
                created_at=datetime.now(timezone.utc)
            )
            
            self.session.add(tag)
            self.session.commit()
            self.session.refresh(tag)
            return tag
            
        except ValidationError as e:
            self.session.rollback()
            raise ValueError(str(e)) from e
        except Exception as e:
            self.session.rollback()
            raise
    
    def get_tag(self, tag_id: int) -> Optional[Tag]:
        """Get a tag by ID.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            Tag object if found, None otherwise
        """
        return self.session.query(Tag).filter_by(id=tag_id).first()
    
    def get_tag_by_name(self, tag_name: str) -> Optional[Tag]:
        """Get a tag by name.
        
        Args:
            tag_name: Tag name (will be normalized to lowercase)
            
        Returns:
            Tag object if found, None otherwise
        """
        normalized = tag_name.lower().strip()
        return self.session.query(Tag).filter_by(tag_name=normalized).first()
    
    def list_all_tags(self) -> List[Tag]:
        """Get all tags ordered by creation date.
        
        Returns:
            List of Tag objects
        """
        return self.session.query(Tag).order_by(Tag.created_at.desc()).all()
    
    def delete_tag(self, tag_id: int) -> bool:
        """Delete a tag (cascade deletes TaggedItems).
        
        Args:
            tag_id: Tag ID
            
        Returns:
            True if deleted, False if not found
        """
        tag = self.get_tag(tag_id)
        if not tag:
            return False
        
        try:
            self.session.delete(tag)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise
    
    # Tagged Item Operations
    
    def tag_item(
        self,
        tag_name: str,
        item_id: int,
        item_type: str = "task",
        content: Optional[str] = None
    ) -> TaggedItem:
        """Associate a tag with an item.
        
        Args:
            tag_name: Tag name (will create if doesn't exist)
            item_id: ID of the item being tagged
            item_type: Type of item (default: 'task')
            content: Optional content associated with tag (e.g., movie title)
            
        Returns:
            Created or existing TaggedItem
        """
        # Create tag if it doesn't exist
        tag = self.get_tag_by_name(tag_name)
        if not tag:
            tag = self.create_tag(tag_name)
        
        # Check if item is already tagged with this tag
        existing = self.session.query(TaggedItem).filter_by(
            tag_id=tag.id,
            item_id=item_id,
            item_type=item_type
        ).first()
        
        if existing:
            # Update content if provided
            if content:
                existing.content = content
                self.session.commit()
                # Trigger enrichment on update when content is present
                if content and TagService._global_enrichment_integration:
                    try:
                        TagService._global_enrichment_integration.enrich_on_tag_updated(existing.id)
                    except Exception:
                        # Swallow integration errors to not impact core tagging
                        pass
            return existing
        
        # Create new tagged item
        tagged_item = TaggedItem(
            tag_id=tag.id,
            item_id=item_id,
            item_type=item_type,
            content=content,
            created_at=datetime.now(timezone.utc)
        )
        
        self.session.add(tagged_item)
        self.session.commit()
        self.session.refresh(tagged_item)
        # Trigger enrichment on creation when content is present
        if tagged_item.content and TagService._global_enrichment_integration:
            try:
                TagService._global_enrichment_integration.enrich_on_tag_created(tagged_item.id)
            except Exception:
                # Swallow integration errors to not impact core tagging
                pass
        return tagged_item
    
    def tag_item_with_multiple(
        self,
        item_id: int,
        tag_names: List[str],
        item_type: str = "task",
        tag_contents: Optional[Dict[str, str]] = None
    ) -> List[TaggedItem]:
        """Associate multiple tags with an item.
        
        Args:
            item_id: ID of the item
            tag_names: List of tag names
            item_type: Type of item
            tag_contents: Optional dict mapping tag_name -> content
            
        Returns:
            List of TaggedItem objects
        """
        if tag_contents is None:
            tag_contents = {}
        
        tagged_items = []
        for tag_name in tag_names:
            content = tag_contents.get(tag_name)
            tagged_item = self.tag_item(tag_name, item_id, item_type, content)
            tagged_items.append(tagged_item)
        
        return tagged_items
    
    def get_item_tags(self, item_id: int, item_type: str = "task") -> List[Tag]:
        """Get all tags associated with an item.
        
        Args:
            item_id: Item ID
            item_type: Type of item
            
        Returns:
            List of Tag objects
        """
        tagged_items = self.session.query(TaggedItem).filter_by(
            item_id=item_id,
            item_type=item_type
        ).all()
        
        return [ti.tag for ti in tagged_items]
    
    def get_items_by_tag(
        self,
        tag_name: str,
        item_type: str = "task"
    ) -> List[Dict[str, Any]]:
        """Get all items tagged with a specific tag.
        
        Args:
            tag_name: Tag name
            item_type: Type of item to filter
            
        Returns:
            List of dicts with item_id, item_type, content
        """
        tag = self.get_tag_by_name(tag_name)
        if not tag:
            return []
        
        tagged_items = self.session.query(TaggedItem).filter_by(
            tag_id=tag.id,
            item_type=item_type
        ).all()
        
        return [
            {
                'item_id': ti.item_id,
                'item_type': ti.item_type,
                'content': ti.content,
                'created_at': ti.created_at
            }
            for ti in tagged_items
        ]
    
    def untag_item(self, tag_name: str, item_id: int, item_type: str = "task") -> bool:
        """Remove a tag from an item.
        
        Args:
            tag_name: Tag name
            item_id: Item ID
            item_type: Type of item
            
        Returns:
            True if untagged, False if tag/item not found
        """
        tag = self.get_tag_by_name(tag_name)
        if not tag:
            return False
        
        tagged_item = self.session.query(TaggedItem).filter_by(
            tag_id=tag.id,
            item_id=item_id,
            item_type=item_type
        ).first()
        
        if not tagged_item:
            return False
        
        try:
            self.session.delete(tagged_item)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise
    
    # Parsing & Categorization
    
    def parse_and_tag_text(
        self,
        text: str,
        item_id: int,
        item_type: str = "task"
    ) -> List[TaggedItem]:
        """Parse tags from text and apply them to an item.
        
        Args:
            text: Text containing tags
            item_id: Item to tag
            item_type: Type of item
            
        Returns:
            List of created TaggedItem objects
        """
        parsed = TagParser.parse_tags(text)
        tag_contents = {t['tag_name']: t['content'] for t in parsed}
        tag_names = [t['tag_name'] for t in parsed]
        
        return self.tag_item_with_multiple(item_id, tag_names, item_type, tag_contents)
    
    def get_tag_suggestions(self, partial_input: str) -> List[str]:
        """Get tag suggestions for autocomplete.
        
        Args:
            partial_input: User's current input
            
        Returns:
            List of suggested tag names
        """
        existing_tags = [tag.tag_name for tag in self.list_all_tags()]
        return TagParser.suggest_tags(partial_input, existing_tags)
    
    def filter_items(self, tag_filter: TagFilter, item_model, item_type: str = "task"):
        """Filter items by tags using AND/OR logic.
        
        Args:
            tag_filter: Filter configuration with rules and operators
            item_model: SQLAlchemy model to filter (Task, ImportedFile, etc.)
            item_type: Type of item for TaggedItem filtering
            
        Returns:
            List of filtered items
        """
        query = self.session.query(item_model)
        
        # Apply tag filter using query builder
        builder = FilterQueryBuilder()
        filtered_query = builder.apply_filter(query, tag_filter, item_model)
        
        return filtered_query.all()

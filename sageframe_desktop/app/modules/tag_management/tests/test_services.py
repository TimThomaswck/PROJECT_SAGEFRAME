"""Tests for tag service module."""

import pytest
from datetime import datetime, timezone
from app.modules.tag_management.services import TagService, TagSchema
from app.modules.tag_management.models import Tag, TaggedItem


@pytest.fixture
def service():
    """Create in-memory service for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return TagService(session=session)


class TestTagSchema:
    """Test TagSchema validation."""
    
    def test_valid_tag_name(self):
        """Test valid tag name."""
        schema = TagSchema("movie")
        assert schema.tag_name == "movie"
    
    def test_empty_tag_raises(self):
        """Test empty tag name raises error."""
        with pytest.raises(ValueError):
            TagSchema("")
    
    def test_tag_normalization(self):
        """Test tag name normalization to lowercase."""
        schema = TagSchema("MOVIE")
        assert schema.tag_name == "movie"
    
    def test_tag_whitespace_trimmed(self):
        """Test whitespace is trimmed."""
        schema = TagSchema("  movie  ")
        assert schema.tag_name == "movie"
    
    def test_tag_too_long(self):
        """Test tag name length limit."""
        with pytest.raises(ValueError):
            TagSchema("a" * 101)
    
    def test_tag_with_hyphen(self):
        """Test tag with hyphen is valid."""
        schema = TagSchema("sci-fi")
        assert schema.tag_name == "sci-fi"
    
    def test_tag_with_underscore(self):
        """Test tag with underscore is valid."""
        schema = TagSchema("to_read")
        assert schema.tag_name == "to_read"
    
    def test_tag_with_special_char_fails(self):
        """Test special characters are rejected."""
        with pytest.raises(ValueError):
            TagSchema("tag@name")


class TestTagService:
    """Test suite for TagService."""
    
    def test_create_tag(self, service):
        """Test creating a tag."""
        tag = service.create_tag("movie")
        assert tag.tag_name == "movie"
        assert tag.id is not None
        assert tag.created_at is not None
    
    def test_create_tag_with_category(self, service):
        """Test creating a tag with category."""
        tag = service.create_tag("movie", category="media")
        assert tag.category == "media"
    
    def test_get_tag_by_name(self, service):
        """Test retrieving tag by name."""
        service.create_tag("movie")
        tag = service.get_tag_by_name("movie")
        assert tag is not None
        assert tag.tag_name == "movie"
    
    def test_get_tag_by_name_case_insensitive(self, service):
        """Test tag name lookup is case-insensitive."""
        service.create_tag("movie")
        tag = service.get_tag_by_name("MOVIE")
        assert tag is not None
    
    def test_get_tag_not_found(self, service):
        """Test getting nonexistent tag returns None."""
        tag = service.get_tag_by_name("nonexistent")
        assert tag is None
    
    def test_list_all_tags(self, service):
        """Test listing all tags."""
        service.create_tag("movie")
        service.create_tag("book")
        tags = service.list_all_tags()
        assert len(tags) == 2
    
    def test_delete_tag(self, service):
        """Test deleting a tag."""
        tag = service.create_tag("movie")
        success = service.delete_tag(tag.id)
        assert success
        tag = service.get_tag(tag.id)
        assert tag is None
    
    def test_delete_nonexistent_tag(self, service):
        """Test deleting nonexistent tag returns False."""
        success = service.delete_tag(999)
        assert not success
    
    def test_tag_item(self, service):
        """Test tagging an item."""
        tagged_item = service.tag_item("movie", item_id=1)
        assert tagged_item.tag.tag_name == "movie"
        assert tagged_item.item_id == 1
    
    def test_tag_item_with_content(self, service):
        """Test tagging with content."""
        tagged_item = service.tag_item("movie", item_id=1, content="Inception")
        assert tagged_item.content == "Inception"
    
    def test_tag_item_creates_tag_if_missing(self, service):
        """Test tagging creates tag if it doesn't exist."""
        service.tag_item("movie", item_id=1)
        tag = service.get_tag_by_name("movie")
        assert tag is not None
    
    def test_tag_item_duplicate_returns_existing(self, service):
        """Test tagging same item twice returns existing."""
        ti1 = service.tag_item("movie", item_id=1)
        ti2 = service.tag_item("movie", item_id=1)
        assert ti1.id == ti2.id
    
    def test_tag_item_with_multiple(self, service):
        """Test tagging with multiple tags."""
        tagged_items = service.tag_item_with_multiple(
            item_id=1,
            tag_names=["movie", "favorite"],
            tag_contents={"movie": "Inception"}
        )
        assert len(tagged_items) == 2
    
    def test_get_item_tags(self, service):
        """Test retrieving tags for an item."""
        service.tag_item("movie", item_id=1)
        service.tag_item("favorite", item_id=1)
        tags = service.get_item_tags(item_id=1)
        assert len(tags) == 2
        tag_names = [t.tag_name for t in tags]
        assert "movie" in tag_names
        assert "favorite" in tag_names
    
    def test_get_items_by_tag(self, service):
        """Test retrieving items by tag."""
        service.tag_item("movie", item_id=1, content="Inception")
        service.tag_item("movie", item_id=2, content="Matrix")
        items = service.get_items_by_tag("movie")
        assert len(items) == 2
    
    def test_untag_item(self, service):
        """Test removing a tag from an item."""
        service.tag_item("movie", item_id=1)
        success = service.untag_item("movie", item_id=1)
        assert success
        tags = service.get_item_tags(item_id=1)
        assert len(tags) == 0
    
    def test_untag_nonexistent_tag(self, service):
        """Test untagging nonexistent tag returns False."""
        success = service.untag_item("nonexistent", item_id=1)
        assert not success
    
    def test_parse_and_tag_text(self, service):
        """Test parsing text and tagging item."""
        text = "Watched @movie: Inception"
        tagged_items = service.parse_and_tag_text(text, item_id=1)
        assert len(tagged_items) == 1
        assert tagged_items[0].tag.tag_name == "movie"
        assert tagged_items[0].content == "Inception"
    
    def test_parse_and_tag_multiple(self, service):
        """Test parsing multiple tags from text."""
        text = "Watched @movie: Inception, read @book: Dune"
        tagged_items = service.parse_and_tag_text(text, item_id=1)
        assert len(tagged_items) == 2
    
    def test_tag_suggestions(self, service):
        """Test getting tag suggestions."""
        service.create_tag("movie")
        service.create_tag("music")
        suggestions = service.get_tag_suggestions("@mov")
        assert "movie" in suggestions

"""UI tests for tag components."""

import pytest
from app.ui.tag_management.tag_syntax_highlighter import TagSyntaxHighlighter
from app.ui.tag_management.tag_input_widget import TagInputWidget
from app.ui.tag_management.tag_badge import TagBadge, TagBadgeContainer
from PySide6.QtWidgets import QApplication, QPlainTextEdit


@pytest.fixture
def app():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestTagSyntaxHighlighter:
    """Test tag syntax highlighter."""
    
    def test_highlighter_creation(self, app):
        """Test creating highlighter."""
        text_edit = QPlainTextEdit()
        doc = text_edit.document()
        highlighter = TagSyntaxHighlighter(doc)
        assert highlighter is not None
    
    def test_highlighter_formats(self, app):
        """Test that formats are properly initialized."""
        text_edit = QPlainTextEdit()
        doc = text_edit.document()
        highlighter = TagSyntaxHighlighter(doc)
        assert highlighter.tag_format is not None
        assert highlighter.content_format is not None
        assert highlighter.at_format is not None


class TestTagInputWidget:
    """Test tag input widget."""
    
    def test_widget_creation(self, app):
        """Test creating tag input widget."""
        widget = TagInputWidget()
        assert widget is not None
        assert widget.text_edit is not None
    
    def test_set_and_get_text(self, app):
        """Test setting and getting text."""
        widget = TagInputWidget()
        text = "Hello @world"
        widget.set_text(text)
        assert widget.get_text() == text
    
    def test_clear_text(self, app):
        """Test clearing text."""
        widget = TagInputWidget()
        widget.set_text("Some text")
        widget.clear()
        assert widget.get_text() == ""
    
    def test_append_text(self, app):
        """Test appending text."""
        widget = TagInputWidget()
        widget.set_text("Hello")
        widget.append_text(" @world")
        assert "Hello" in widget.get_text()
        assert "@world" in widget.get_text()
    
    def test_extract_tags_simple(self, app):
        """Test extracting tags from input."""
        widget = TagInputWidget()
        widget.set_text("Watched @movie: Inception")
        extracted = widget.get_extracted_tags()
        assert 'movie' in extracted['tags']
        assert extracted['tag_contents']['movie'] == 'Inception'
    
    def test_extract_multiple_tags(self, app):
        """Test extracting multiple tags."""
        widget = TagInputWidget()
        widget.set_text("@movie: Inception @director: Nolan")
        extracted = widget.get_extracted_tags()
        assert len(extracted['tags']) == 2
        assert 'movie' in extracted['tags']
        assert 'director' in extracted['tags']
    
    def test_clean_text(self, app):
        """Test removing tag markup from text."""
        widget = TagInputWidget()
        widget.set_text("Watched @movie: Inception today")
        clean = widget.get_clean_text()
        assert '@' not in clean
        assert 'Inception' in clean
    
    def test_set_available_tags(self, app):
        """Test setting available tags."""
        widget = TagInputWidget()
        tags = ['movie', 'book', 'article']
        widget.set_available_tags(tags)
        assert widget._available_tags == tags


class TestTagBadge:
    """Test tag badge component."""
    
    def test_badge_creation(self, app):
        """Test creating a tag badge."""
        badge = TagBadge("movie")
        assert badge is not None
        assert badge.tag_name == "movie"
    
    def test_badge_removable(self, app):
        """Test creating removable badge."""
        badge = TagBadge("movie", removable=True)
        assert badge is not None
    
    def test_badge_not_removable(self, app):
        """Test creating non-removable badge."""
        badge = TagBadge("movie", removable=False)
        assert badge is not None
    
    def test_badge_with_callback(self, app):
        """Test badge with removal callback."""
        removed = []
        
        def on_remove(tag_name):
            removed.append(tag_name)
        
        badge = TagBadge("movie", on_remove=on_remove)
        assert badge is not None


class TestTagBadgeContainer:
    """Test tag badge container."""
    
    def test_container_creation(self, app):
        """Test creating tag container."""
        container = TagBadgeContainer()
        assert container is not None
    
    def test_add_single_tag(self, app):
        """Test adding a single tag."""
        container = TagBadgeContainer()
        container.add_tag("movie")
        tags = container.get_tags()
        assert 'movie' in tags
    
    def test_add_multiple_tags(self, app):
        """Test adding multiple tags."""
        container = TagBadgeContainer()
        container.add_tags(['movie', 'book', 'article'])
        tags = container.get_tags()
        assert len(tags) == 3
        assert 'movie' in tags
        assert 'book' in tags
        assert 'article' in tags
    
    def test_clear_tags(self, app):
        """Test clearing all tags."""
        container = TagBadgeContainer()
        container.add_tags(['movie', 'book'])
        container.clear_tags()
        tags = container.get_tags()
        assert len(tags) == 0
    
    def test_get_tags(self, app):
        """Test retrieving tags."""
        container = TagBadgeContainer()
        container.add_tags(['movie', 'book'])
        tags = container.get_tags()
        assert tags == ['movie', 'book']

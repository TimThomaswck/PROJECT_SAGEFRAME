"""Tests for tag parser module."""

import pytest
from app.modules.tag_management.parsers import TagParser


class TestTagParser:
    """Test suite for TagParser class."""
    
    def test_simple_tag_detection(self):
        """Test detection of simple @tag pattern."""
        text = "Watched @movie"
        tags = TagParser.parse_tags(text)
        assert len(tags) == 1
        assert tags[0]['tag_name'] == 'movie'
        assert tags[0]['content'] is None
    
    def test_tag_with_content(self):
        """Test detection of @tag: content pattern."""
        text = "@movie: Inception"
        tags = TagParser.parse_tags(text)
        assert len(tags) == 1
        assert tags[0]['tag_name'] == 'movie'
        assert tags[0]['content'] == 'Inception'
    
    def test_tag_case_insensitivity(self):
        """Test that tags are normalized to lowercase."""
        text = "@Movie: Inception"
        tags = TagParser.parse_tags(text)
        assert tags[0]['tag_name'] == 'movie'
    
    def test_multiple_tags(self):
        """Test extraction of multiple tags from text."""
        text = "Watched @movie: Inception and read @book: Dune"
        tags = TagParser.parse_tags(text)
        assert len(tags) == 2
        assert tags[0]['tag_name'] == 'movie'
        assert tags[0]['content'] == 'Inception'
        assert tags[1]['tag_name'] == 'book'
        assert tags[1]['content'] == 'Dune'
    
    def test_tags_in_context(self):
        """Test tags mixed with regular text."""
        text = "Today I watched @movie: Inception and it was great!"
        tags = TagParser.parse_tags(text)
        assert len(tags) == 1
        assert tags[0]['tag_name'] == 'movie'
        assert tags[0]['content'] == 'Inception'
    
    def test_empty_text(self):
        """Test parsing empty text."""
        tags = TagParser.parse_tags("")
        assert tags == []
    
    def test_no_tags(self):
        """Test text without tags."""
        tags = TagParser.parse_tags("Just some regular text")
        assert tags == []
    
    def test_extract_unique_tags(self):
        """Test extracting unique tag names."""
        text = "Watched @movie: Inception, also @movie: Matrix"
        unique = TagParser.extract_unique_tags(text)
        assert unique == ['movie']
    
    def test_extract_unique_multiple(self):
        """Test extracting multiple unique tags."""
        text = "@movie: Inception, @book: Dune, @movie: Matrix"
        unique = TagParser.extract_unique_tags(text)
        assert len(unique) == 2
        assert 'movie' in unique
        assert 'book' in unique
    
    def test_tag_with_hyphen(self):
        """Test tags with hyphens."""
        text = "@sci-fi: Space Odyssey"
        tags = TagParser.parse_tags(text)
        assert tags[0]['tag_name'] == 'sci-fi'
    
    def test_tag_with_underscore(self):
        """Test tags with underscores."""
        text = "@to_read: Dune"
        tags = TagParser.parse_tags(text)
        assert tags[0]['tag_name'] == 'to_read'
    
    def test_content_whitespace_trimming(self):
        """Test that content whitespace is trimmed."""
        text = "@movie:   Inception   "
        tags = TagParser.parse_tags(text)
        assert tags[0]['content'] == 'Inception'
    
    def test_content_punctuation_removal(self):
        """Test removal of trailing punctuation from content."""
        text = "@movie: Inception."
        tags = TagParser.parse_tags(text)
        assert tags[0]['content'] == 'Inception'
    
    def test_remove_tags_from_text(self):
        """Test removal of tag markup."""
        text = "Watched @movie: Inception last night"
        clean = TagParser.remove_tags_from_text(text)
        assert '@' not in clean
        assert 'Inception' in clean
    
    def test_remove_tags_simple(self):
        """Test removal of simple tags."""
        text = "Going to @work today"
        clean = TagParser.remove_tags_from_text(text)
        assert '@' not in clean
        assert 'Going to' in clean
    
    def test_highlight_positions(self):
        """Test getting highlight positions for tags."""
        text = "Watched @movie: Inception"
        positions = TagParser.highlight_positions(text)
        assert len(positions) > 0
        start, end = positions[0]
        assert text[start:end].startswith('@')
    
    def test_has_tags_true(self):
        """Test detection of tags present."""
        assert TagParser.has_tags("Going to @work")
    
    def test_has_tags_false(self):
        """Test detection of no tags."""
        assert not TagParser.has_tags("No tags here")
    
    def test_suggest_tags_matching(self):
        """Test tag suggestions for autocomplete."""
        existing = ['movie', 'music', 'book', 'article']
        suggestions = TagParser.suggest_tags("@mov", existing)
        assert 'movie' in suggestions
        assert 'music' not in suggestions
    
    def test_suggest_tags_partial(self):
        """Test partial matching suggestions."""
        existing = ['react', 'redux', 'ruby', 'rest']
        suggestions = TagParser.suggest_tags("@rea", existing)
        assert 'react' in suggestions
        assert 'ruby' not in suggestions
    
    def test_suggest_tags_empty_partial(self):
        """Test suggestions with no partial input."""
        existing = ['movie', 'book']
        suggestions = TagParser.suggest_tags("@", existing)
        # Should return empty or all tags depending on implementation
        assert isinstance(suggestions, list)

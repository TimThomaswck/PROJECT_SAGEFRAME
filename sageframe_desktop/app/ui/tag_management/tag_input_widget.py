"""Tag input widget with real-time highlighting and autocomplete."""

from typing import Optional, List, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QListWidget, QListWidgetItem,
    QCompleter
)
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import QTextCursor

from app.ui.tag_management.tag_syntax_highlighter import TagSyntaxHighlighter
from app.modules.tag_management.parsers import TagParser


class TagInputWidget(QWidget):
    """Input widget for entering text with smart tags.
    
    Features:
    - Real-time tag syntax highlighting (<100ms feedback)
    - Tag autocomplete suggestions
    - Extracted tags on demand
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()
        self._available_tags: List[str] = []
        self._on_text_changed_callback: Optional[Callable] = None
    
    def _init_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Text input area
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("Type here... Use @tag or @tag: content for tagging")
        self.text_edit.setMinimumHeight(100)
        self.text_edit.setObjectName("tagInputEdit")
        
        # Apply syntax highlighting
        self.highlighter = TagSyntaxHighlighter(self.text_edit.document())
        
        # Connect to text changes for autocomplete
        self.text_edit.textChanged.connect(self._on_text_changed)
        
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
    
    def set_available_tags(self, tags: List[str]):
        """Set the list of available tags for suggestions.
        
        Args:
            tags: List of tag names for autocomplete
        """
        self._available_tags = tags
    
    def _on_text_changed(self):
        """Handle text changes - trigger autocomplete suggestions."""
        if self._on_text_changed_callback:
            self._on_text_changed_callback(self.get_text())
    
    def on_text_changed(self, callback: Callable):
        """Register callback for text changes.
        
        Args:
            callback: Function to call with new text
        """
        self._on_text_changed_callback = callback
    
    def get_text(self) -> str:
        """Get the current text content."""
        return self.text_edit.toPlainText()
    
    def set_text(self, text: str):
        """Set the text content."""
        self.text_edit.setPlainText(text)
    
    def clear(self):
        """Clear the text input."""
        self.text_edit.clear()
    
    def append_text(self, text: str):
        """Append text to the current content."""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
    
    def get_extracted_tags(self) -> dict:
        """Extract and return all tags from current text.
        
        Returns:
            Dict with 'tags' (list of tag names) and 'tag_contents' (dict)
        """
        text = self.get_text()
        parsed = TagParser.parse_tags(text)
        
        tags = [t['tag_name'] for t in parsed]
        tag_contents = {t['tag_name']: t['content'] for t in parsed if t['content']}
        
        return {
            'tags': tags,
            'tag_contents': tag_contents
        }
    
    def get_clean_text(self) -> str:
        """Get text with all tag markup removed (content preserved).
        
        Example: "Watched @movie: Inception" → "Watched Inception"
        """
        text = self.get_text()
        return TagParser.remove_tags_from_text(text)
    
    def highlight_tag_at_cursor(self) -> Optional[str]:
        """Get the tag at current cursor position if any.
        
        Returns:
            Tag name if cursor is within a tag, None otherwise
        """
        cursor = self.text_edit.textCursor()
        pos = cursor.positionInBlock()
        text = self.text_edit.toPlainText()
        
        # Find tags at this position
        positions = TagParser.highlight_positions(text)
        abs_pos = cursor.position()
        
        for start, end in positions:
            if start <= abs_pos <= end:
                # Extract tag name
                match_text = text[start:end]
                import re
                match = re.match(r'@([a-zA-Z0-9_-]+)', match_text)
                if match:
                    return match.group(1)
        
        return None

"""Syntax highlighter for smart tags in text input."""

from PySide6.QtGui import QSyntaxHighlighter, QTextDocument, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt
import re


class TagSyntaxHighlighter(QSyntaxHighlighter):
    """Highlights @tag patterns in real-time as user types.
    
    Provides <100ms visual feedback for tag recognition (NFR1).
    """
    
    # Regex for tag pattern: @word or @word: content
    TAG_PATTERN = re.compile(
        r'@([a-zA-Z0-9_-]+)(?::\s*([^@\n]*?))?(?=\s*@|\s*$|\s+[^@]|\n)',
        re.IGNORECASE
    )
    
    def __init__(self, parent: QTextDocument = None):
        super().__init__(parent)
        self._setup_formats()
    
    def _setup_formats(self):
        """Set up text formatting for different parts of tags."""
        # Format for tag name (e.g., @movie)
        self.tag_format = QTextCharFormat()
        self.tag_format.setForeground(QColor("#0ea5e9"))  # Cyan
        self.tag_format.setFontWeight(QFont.Bold)
        
        # Format for tag content (e.g., "Inception" in @movie: Inception)
        self.content_format = QTextCharFormat()
        self.content_format.setForeground(QColor("#06b6d4"))  # Teal
        
        # Format for @ symbol
        self.at_format = QTextCharFormat()
        self.at_format.setForeground(QColor("#0ea5e9"))
        self.at_format.setFontWeight(QFont.Bold)
    
    def highlightBlock(self, text: str):
        """Highlight tags in the given text block.
        
        Called by Qt whenever the text changes. Uses compiled regex
        to minimize CPU usage and stay under 100ms feedback.
        """
        # Find all tags in this block
        for match in self.TAG_PATTERN.finditer(text):
            # Highlight @ symbol
            at_start = match.start()
            self.setFormat(at_start, 1, self.at_format)
            
            # Highlight tag name (group 1)
            tag_start = at_start + 1
            tag_end = tag_start + len(match.group(1))
            self.setFormat(tag_start, len(match.group(1)), self.tag_format)
            
            # Highlight colon if present
            if match.group(2) is not None:
                colon_pos = match.end(1) + 1
                self.setFormat(colon_pos, 1, self.at_format)
                
                # Highlight content (group 2)
                content_start = colon_pos + 1
                # Skip whitespace
                while content_start < match.end() and text[content_start] == ' ':
                    content_start += 1
                
                if content_start < match.end():
                    content_len = match.end() - content_start
                    self.setFormat(content_start, content_len, self.content_format)

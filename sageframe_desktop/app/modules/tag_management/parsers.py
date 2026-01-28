"""Tag parsing and recognition system.

This module provides regex-based parsing for smart tag patterns,
detecting and extracting tags from free-form text with <100ms latency.
"""

import re
from typing import List, Dict, Tuple, Optional


class TagParser:
    """Parses smart tag patterns from text.
    
    Supports:
    1. Simple tag: @movie
    2. Tag with content: @movie: Inception
    3. Tags in context: "Watched @movie: Inception last night"
    
    Performance: Uses compiled regex for sub-100ms parsing.
    """
    
    # Compiled regex pattern for tag detection
    # Matches: @word or @word: content_until_next_at_or_end
    # Uses negative lookahead to stop at next @ symbol
    TAG_PATTERN = re.compile(
        r'@([a-zA-Z0-9_-]+)(?::\s*([^@\n]*?))?(?=\s*@|\s*$|\s+[^@]|\n)',
        re.IGNORECASE
    )
    
    @classmethod
    def parse_tags(cls, text: str) -> List[Dict[str, Optional[str]]]:
        """Extract all tags and their content from text.
        
        Args:
            text: Raw text containing tags
            
        Returns:
            List of dicts with 'tag_name' and 'content' keys.
            Example: [{'tag_name': 'movie', 'content': 'Inception'}, ...]
        """
        if not text:
            return []
        
        tags = []
        for match in cls.TAG_PATTERN.finditer(text):
            tag_name = match.group(1).lower()
            content = match.group(2)
            
            # Clean up content: strip whitespace and remove trailing punctuation if present
            if content:
                content = content.strip()
                # Remove trailing punctuation if it looks like sentence end
                content = re.sub(r'[.,!?]+$', '', content)
            
            tags.append({
                'tag_name': tag_name,
                'content': content if content else None
            })
        
        return tags
    
    @classmethod
    def extract_unique_tags(cls, text: str) -> List[str]:
        """Extract unique tag names (lowercase) from text.
        
        Args:
            text: Raw text containing tags
            
        Returns:
            List of unique tag names (no duplicates)
        """
        tags = cls.parse_tags(text)
        seen = set()
        unique = []
        for tag_dict in tags:
            tag_name = tag_dict['tag_name']
            if tag_name not in seen:
                unique.append(tag_name)
                seen.add(tag_name)
        return unique
    
    @classmethod
    def remove_tags_from_text(cls, text: str) -> str:
        """Remove all tag markup from text, preserving tag content.
        
        Example:
            "Watched @movie: Inception last night" → "Watched Inception last night"
        
        Args:
            text: Text with tags
            
        Returns:
            Text with tag markup removed but content preserved
        """
        # Replace @tag: content with just content
        result = cls.TAG_PATTERN.sub(lambda m: m.group(2) or '', text)
        # Clean up extra whitespace
        result = re.sub(r'\s+', ' ', result).strip()
        return result
    
    @classmethod
    def highlight_positions(cls, text: str) -> List[Tuple[int, int]]:
        """Get positions of all tags for UI highlighting.
        
        Args:
            text: Text containing tags
            
        Returns:
            List of (start, end) tuples for each tag match
        """
        positions = []
        for match in cls.TAG_PATTERN.finditer(text):
            positions.append((match.start(), match.end()))
        return positions
    
    @classmethod
    def has_tags(cls, text: str) -> bool:
        """Quick check if text contains any tags.
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains at least one tag
        """
        return bool(cls.TAG_PATTERN.search(text))
    
    @classmethod
    def suggest_tags(cls, text: str, existing_tags: List[str]) -> List[str]:
        """Suggest tag completions based on partial input.
        
        For example, if user types "@mov", suggest tags starting with "mov".
        
        Args:
            text: Current input (typically ends with incomplete tag)
            existing_tags: List of existing tag names in system
            
        Returns:
            List of suggested tag names
        """
        # Find the last incomplete tag pattern
        last_at = text.rfind('@')
        if last_at == -1:
            return []
        
        partial = text[last_at + 1:].lower()
        
        # Filter suggestions: must start with partial and not contain spaces
        if ' ' in partial:
            return []
        
        suggestions = [tag for tag in existing_tags if tag.startswith(partial)]
        return sorted(suggestions)

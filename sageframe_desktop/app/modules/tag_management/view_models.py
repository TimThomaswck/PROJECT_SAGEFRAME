"""ViewModel for tag management UI operations."""

from typing import Optional, List, Dict, Any

from PySide6.QtCore import QObject, Signal

from app.modules.tag_management.services import TagService


class TagViewModel(QObject):
    """ViewModel for tag management in UI."""
    
    # Signals
    tagsChanged = Signal(list)  # Emitted when tags are updated
    suggestionsReady = Signal(list)  # Emitted with tag suggestions
    tagCreated = Signal(str)  # Emitted when a tag is created
    tagDeleted = Signal(str)  # Emitted when a tag is deleted
    
    def __init__(self, parent: Optional[QObject] = None):
        """Initialize TagViewModel."""
        super().__init__(parent)
        self._service = TagService()
        self._current_tags: List[str] = []
    
    def refresh_tags(self) -> List[str]:
        """Refresh all available tags."""
        try:
            tags = self._service.list_all_tags()
            self._current_tags = [t.tag_name for t in tags]
            self.tagsChanged.emit(self._current_tags)
            return self._current_tags
        except Exception:
            return []
    
    def get_suggestions(self, partial_input: str) -> List[str]:
        """Get tag suggestions for autocomplete."""
        try:
            suggestions = self._service.get_tag_suggestions(partial_input)
            self.suggestionsReady.emit(suggestions)
            return suggestions
        except Exception:
            return []
    
    def create_tag(self, tag_name: str, category: Optional[str] = None) -> bool:
        """Create a new tag."""
        try:
            tag = self._service.create_tag(tag_name, category)
            self.tagCreated.emit(tag.tag_name)
            self.refresh_tags()
            return True
        except Exception:
            return False
    
    def tag_item(
        self,
        tag_name: str,
        item_id: int,
        item_type: str = "task",
        content: Optional[str] = None
    ) -> bool:
        """Associate a tag with an item."""
        try:
            self._service.tag_item(tag_name, item_id, item_type, content)
            return True
        except Exception:
            return False
    
    def parse_and_tag(self, text: str, item_id: int, item_type: str = "task") -> bool:
        """Parse tags from text and apply to item."""
        try:
            self._service.parse_and_tag_text(text, item_id, item_type)
            return True
        except Exception:
            return False
    
    def get_item_tags(self, item_id: int, item_type: str = "task") -> List[str]:
        """Get tags for an item."""
        try:
            tags = self._service.get_item_tags(item_id, item_type)
            return [t.tag_name for t in tags]
        except Exception:
            return []
    
    def close(self):
        """Clean up resources."""
        if self._service:
            self._service.close()
    
    def __del__(self):
        """Destructor."""
        self.close()

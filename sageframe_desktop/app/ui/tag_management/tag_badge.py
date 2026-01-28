"""Tag badge display components."""

from typing import Optional, Callable

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class TagBadge(QWidget):
    """Single tag badge/chip for display.
    
    Atomic Design: Atom component
    Shows a tag name with optional remove button.
    """
    
    def __init__(
        self,
        tag_name: str,
        removable: bool = True,
        on_remove: Optional[Callable] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.tag_name = tag_name
        self.on_remove = on_remove
        self._init_ui(removable)
    
    def _init_ui(self, removable: bool):
        """Set up badge UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # Tag label
        label = QLabel(f"@{self.tag_name}")
        label.setObjectName("tagBadgeLabel")
        layout.addWidget(label)
        
        # Remove button (if removable)
        if removable:
            remove_btn = QPushButton("×")
            remove_btn.setObjectName("tagBadgeRemoveButton")
            remove_btn.setMaximumWidth(24)
            remove_btn.setMaximumHeight(20)
            remove_btn.setToolTip(f"Remove tag: {self.tag_name}")
            remove_btn.clicked.connect(self._on_remove_clicked)
            layout.addWidget(remove_btn)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Apply styling
        self.setStyleSheet("""
            #tagBadgeLabel {
                background-color: #e0f2fe;
                color: #0369a1;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10pt;
            }
            #tagBadgeRemoveButton {
                background-color: transparent;
                border: none;
                color: #0369a1;
                font-weight: bold;
                font-size: 11pt;
            }
            #tagBadgeRemoveButton:hover {
                color: #c2410c;
            }
        """)
    
    def _on_remove_clicked(self):
        """Handle remove button click."""
        if self.on_remove:
            self.on_remove(self.tag_name)


class TagBadgeContainer(QWidget):
    """Container for displaying multiple tag badges.
    
    Atomic Design: Molecule component
    Displays tags in a row with wrapping.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()
        self._on_tag_removed: Optional[Callable] = None
    
    def _init_ui(self):
        """Set up container UI."""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        self.layout.addStretch()
        self.setLayout(self.layout)
    
    def add_tag(self, tag_name: str, removable: bool = True):
        """Add a tag badge.
        
        Args:
            tag_name: Name of tag to display
            removable: Whether tag can be removed
        """
        badge = TagBadge(
            tag_name,
            removable=removable,
            on_remove=self._on_tag_remove if removable else None
        )
        # Insert before stretch
        self.layout.insertWidget(self.layout.count() - 1, badge)
    
    def add_tags(self, tag_names: list, removable: bool = True):
        """Add multiple tag badges.
        
        Args:
            tag_names: List of tag names
            removable: Whether tags can be removed
        """
        for tag_name in tag_names:
            self.add_tag(tag_name, removable)
    
    def clear_tags(self):
        """Remove all tag badges."""
        # Remove all widgets except the stretch
        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
    
    def get_tags(self) -> list:
        """Get list of current tag names.
        
        Returns:
            List of tag names displayed
        """
        tags = []
        for i in range(self.layout.count() - 1):  # Exclude stretch
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, TagBadge):
                tags.append(widget.tag_name)
        return tags
    
    def on_tag_removed(self, callback: Callable):
        """Register callback for tag removal.
        
        Args:
            callback: Function to call with removed tag name
        """
        self._on_tag_removed = callback
    
    def _on_tag_remove(self, tag_name: str):
        """Handle tag removal."""
        # Remove the badge
        for i in range(self.layout.count() - 1):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, TagBadge) and widget.tag_name == tag_name:
                widget.deleteLater()
                break
        
        # Notify callback
        if self._on_tag_removed:
            self._on_tag_removed(tag_name)

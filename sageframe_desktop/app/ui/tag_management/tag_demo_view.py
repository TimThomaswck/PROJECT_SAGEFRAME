"""Demo view showing tag components integrated."""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox
)
from PySide6.QtCore import Qt

from app.modules.tag_management.view_models import TagViewModel
from app.ui.tag_management.tag_input_widget import TagInputWidget
from app.ui.tag_management.tag_badge import TagBadgeContainer


class TagDemoView(QWidget):
    """Demo view for testing tag input and display."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.view_model = TagViewModel(parent=self)
        self._init_ui()
        self._setup_connections()
        self.view_model.refresh_tags()
    
    def _init_ui(self):
        """Set up the demo UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("Smart Tag Demo")
        title.setObjectName("demoTitle")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title)
        
        # Input section
        input_label = QLabel("Enter text with tags (e.g., 'Watched @movie: Inception'):")
        layout.addWidget(input_label)
        
        self.tag_input = TagInputWidget()
        layout.addWidget(self.tag_input)
        
        # Extracted tags display
        tags_label = QLabel("Extracted Tags:")
        layout.addWidget(tags_label)
        
        self.tag_container = TagBadgeContainer()
        layout.addWidget(self.tag_container)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        extract_btn = QPushButton("Extract Tags")
        extract_btn.clicked.connect(self._on_extract_tags)
        button_layout.addWidget(extract_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._on_clear)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Info section
        info_label = QLabel("Try typing: '@movie: Inception @director: Nolan'")
        info_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _setup_connections(self):
        """Set up signal/slot connections."""
        self.tag_input.on_text_changed(self._on_input_changed)
        self.view_model.suggestionsReady.connect(self._on_suggestions_ready)
    
    def _on_input_changed(self, text: str):
        """Handle text input changes."""
        # Get suggestions if text ends with @
        if text.endswith('@') or '@' in text:
            # Find last @ position
            last_at = text.rfind('@')
            partial = text[last_at + 1:]
            if partial and ' ' not in partial:
                self.view_model.get_suggestions(f"@{partial}")
    
    def _on_suggestions_ready(self, suggestions: list):
        """Handle suggestions from view model."""
        # Could implement autocomplete popup here
        pass
    
    def _on_extract_tags(self):
        """Extract and display tags from input."""
        extracted = self.tag_input.get_extracted_tags()
        tags = extracted['tags']
        
        # Clear and repopulate badge container
        self.tag_container.clear_tags()
        self.tag_container.add_tags(tags, removable=False)
        
        # Show message
        if tags:
            QMessageBox.information(
                self,
                "Tags Extracted",
                f"Found {len(tags)} tag(s): {', '.join(tags)}"
            )
        else:
            QMessageBox.information(self, "No Tags", "No tags found in text")
    
    def _on_clear(self):
        """Clear input and tags."""
        self.tag_input.clear()
        self.tag_container.clear_tags()

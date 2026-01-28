"""Filter panel UI component for tag-based filtering."""

from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from app.modules.tag_management.filtering.models import TagFilter, FilterGroup, FilterRule, FilterOperator
from app.modules.tag_management.view_models import TagViewModel


class FilterChip(QWidget):
    """Individual filter chip showing a tag filter rule."""
    
    removed = Signal(str)  # Emits tag_name when chip is removed
    
    def __init__(self, tag_name: str, include: bool = True, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tag_name = tag_name
        self.include = include
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Tag label
        prefix = "" if include else "NOT "
        label = QLabel(f"{prefix}@{tag_name}")
        label.setStyleSheet("color: #2563eb; font-weight: bold;")
        layout.addWidget(label)
        
        # Remove button
        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #666;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #dc2626;
            }
        """)
        remove_btn.clicked.connect(lambda: self.removed.emit(tag_name))
        layout.addWidget(remove_btn)
        
        # Chip styling
        self.setStyleSheet("""
            FilterChip {
                background: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 12px;
            }
        """)


class FilterPanel(QWidget):
    """Filter panel organism for tag-based filtering with AND/OR logic."""
    
    filterApplied = Signal(object)  # Emits TagFilter when filter is applied
    filterCleared = Signal()
    
    def __init__(self, tag_view_model: TagViewModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._tag_vm = tag_view_model
        self._active_tags: List[str] = []
        self._operator = FilterOperator.AND
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("🔍 Filter by Tags")
        title.setStyleSheet("font-size: 13pt; font-weight: bold;")
        layout.addWidget(title)
        
        # Tag selector row
        selector_layout = QHBoxLayout()
        
        self.tag_selector = QComboBox()
        self.tag_selector.setPlaceholderText("Select a tag...")
        self.tag_selector.setEditable(True)
        selector_layout.addWidget(self.tag_selector, 1)
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_tag)
        selector_layout.addWidget(add_btn)
        
        layout.addLayout(selector_layout)
        
        # Operator toggle
        operator_layout = QHBoxLayout()
        operator_label = QLabel("Combine with:")
        operator_layout.addWidget(operator_label)
        
        self.and_btn = QPushButton("AND")
        self.and_btn.setCheckable(True)
        self.and_btn.setChecked(True)
        self.and_btn.clicked.connect(lambda: self._set_operator(FilterOperator.AND))
        operator_layout.addWidget(self.and_btn)
        
        self.or_btn = QPushButton("OR")
        self.or_btn.setCheckable(True)
        self.or_btn.clicked.connect(lambda: self._set_operator(FilterOperator.OR))
        operator_layout.addWidget(self.or_btn)
        
        operator_layout.addStretch()
        layout.addLayout(operator_layout)
        
        # Active filters section
        active_label = QLabel("Active Filters:")
        active_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(active_label)
        
        # Chips container with scroll
        chips_scroll = QScrollArea()
        chips_scroll.setWidgetResizable(True)
        chips_scroll.setMaximumHeight(100)
        chips_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.chips_container = QWidget()
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        chips_scroll.setWidget(self.chips_container)
        layout.addWidget(chips_scroll)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Filter")
        apply_btn.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
        """)
        apply_btn.clicked.connect(self._apply_filter)
        action_layout.addWidget(apply_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_all)
        action_layout.addWidget(clear_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        layout.addStretch()
    
    def _connect_signals(self):
        """Connect view model signals."""
        self._tag_vm.tagsChanged.connect(self._refresh_tag_list)
        self._refresh_tag_list()
    
    def _refresh_tag_list(self):
        """Refresh tag selector with available tags."""
        tags = self._tag_vm.refresh_tags()
        self.tag_selector.clear()
        self.tag_selector.addItems(tags)
    
    def _set_operator(self, operator: FilterOperator):
        """Set the active operator."""
        self._operator = operator
        self.and_btn.setChecked(operator == FilterOperator.AND)
        self.or_btn.setChecked(operator == FilterOperator.OR)
    
    def _add_tag(self):
        """Add selected tag to active filters."""
        tag = self.tag_selector.currentText().strip().lower()
        if not tag or tag in self._active_tags:
            return
        
        self._active_tags.append(tag)
        self._add_chip(tag)
    
    def _add_chip(self, tag_name: str):
        """Add a filter chip to the display."""
        chip = FilterChip(tag_name)
        chip.removed.connect(self._remove_tag)
        self.chips_layout.addWidget(chip)
    
    def _remove_tag(self, tag_name: str):
        """Remove tag from active filters."""
        if tag_name in self._active_tags:
            self._active_tags.remove(tag_name)
        
        # Remove chip widget
        for i in range(self.chips_layout.count()):
            widget = self.chips_layout.itemAt(i).widget()
            if isinstance(widget, FilterChip) and widget.tag_name == tag_name:
                widget.deleteLater()
                break
    
    def _clear_all(self):
        """Clear all active filters."""
        self._active_tags.clear()
        
        # Remove all chips
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.filterCleared.emit()
    
    def _apply_filter(self):
        """Build and emit tag filter."""
        if not self._active_tags:
            self.filterCleared.emit()
            return
        
        # Build filter with single group
        rules = [FilterRule(tag_name=tag, include=True) for tag in self._active_tags]
        group = FilterGroup(rules=rules, operator=self._operator)
        tag_filter = TagFilter(groups=[group], group_operator=FilterOperator.OR)
        
        self.filterApplied.emit(tag_filter)
    
    def get_current_filter(self) -> TagFilter:
        """Get current filter configuration."""
        if not self._active_tags:
            return TagFilter()
        
        rules = [FilterRule(tag_name=tag, include=True) for tag in self._active_tags]
        group = FilterGroup(rules=rules, operator=self._operator)
        return TagFilter(groups=[group], group_operator=FilterOperator.OR)

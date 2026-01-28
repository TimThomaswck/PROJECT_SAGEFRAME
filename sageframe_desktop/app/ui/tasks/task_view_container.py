"""Task view container with view switcher (List/Kanban/Gantt)."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QStackedWidget, QPushButton, QListWidget, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon


class TaskViewContainer(QWidget):
    """Container for task views with dropdown switcher.
    
    Displays tasks in List, Kanban, or Gantt view modes.
    """
    
    # View modes
    LIST_VIEW = 0
    KANBAN_VIEW = 1
    GANTT_VIEW = 2
    
    # Signals
    viewChanged = Signal(int)  # Emits view mode index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_view = self.KANBAN_VIEW  # Default to Kanban
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the container layout."""
        self.setObjectName("taskViewContainer")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar with view switcher
        top_bar = self._create_top_bar()
        layout.addWidget(top_bar)
        
        # Stacked widget for different views
        self.view_stack = QStackedWidget()
        self.view_stack.setObjectName("taskViewStack")
        layout.addWidget(self.view_stack, stretch=1)
        
        # Add placeholder views (will be populated by MainWindow)
        self._add_placeholder_views()
    
    def _create_top_bar(self) -> QWidget:
        """Create top bar with title and view switcher."""
        top_bar = QWidget()
        top_bar.setObjectName("taskViewTopBar")
        top_bar.setStyleSheet("""
            QWidget#taskViewTopBar {
                background: #1e1e1e;
                border-bottom: 1px solid #333;
                padding: 8px 12px;
            }
        """)
        
        bar_layout = QHBoxLayout(top_bar)
        bar_layout.setContentsMargins(12, 8, 12, 8)
        bar_layout.setSpacing(12)
        
        # Title
        title_label = QLabel("Tasks")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #c69749;")
        bar_layout.addWidget(title_label)
        
        # Spacer
        bar_layout.addStretch()
        
        # View switcher dropdown
        view_label = QLabel("Display:")
        view_label.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        bar_layout.addWidget(view_label)
        
        self.view_switcher = QComboBox()
        self.view_switcher.setObjectName("taskViewSwitcher")
        self.view_switcher.addItems(["List", "Kanban", "Gantt"])
        self.view_switcher.setCurrentIndex(self.KANBAN_VIEW)  # Default Kanban
        self.view_switcher.currentIndexChanged.connect(self._on_view_changed)
        self.view_switcher.setMinimumWidth(120)
        self.view_switcher.setStyleSheet("""
            QComboBox {
                background: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #c69749;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #c69749;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background: #2d2d2d;
                color: #d4d4d4;
                selection-background-color: rgba(198, 151, 73, 0.3);
                border: 1px solid #3e3e3e;
            }
        """)
        bar_layout.addWidget(self.view_switcher)
        
        return top_bar
    
    def _add_placeholder_views(self):
        """Add placeholder widgets for each view type."""
        view_names = ["List View", "Kanban View", "Gantt View"]
        
        for view_name in view_names:
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            label = QLabel(f"{view_name}\n(Loading...)")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #888; font-size: 14px; padding: 40px;")
            placeholder_layout.addWidget(label)
            self.view_stack.addWidget(placeholder)
    
    def _on_view_changed(self, index: int):
        """Handle view switcher change."""
        self._current_view = index
        self.view_stack.setCurrentIndex(index)
        self.viewChanged.emit(index)
    
    def set_list_view(self, widget: QWidget):
        """Set the list view widget."""
        self._replace_view(self.LIST_VIEW, widget)
    
    def set_kanban_view(self, widget: QWidget):
        """Set the Kanban view widget."""
        self._replace_view(self.KANBAN_VIEW, widget)
    
    def set_gantt_view(self, widget: QWidget):
        """Set the Gantt view widget."""
        self._replace_view(self.GANTT_VIEW, widget)
    
    def _replace_view(self, index: int, widget: QWidget):
        """Replace a placeholder view with actual widget."""
        old_widget = self.view_stack.widget(index)
        if old_widget:
            self.view_stack.removeWidget(old_widget)
            old_widget.deleteLater()
        self.view_stack.insertWidget(index, widget)
        # Restore current view if it was active
        if self._current_view == index:
            self.view_stack.setCurrentIndex(index)
    
    def get_current_view(self) -> int:
        """Get current view mode."""
        return self._current_view

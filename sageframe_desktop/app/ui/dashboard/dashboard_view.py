"""Dashboard overview view."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QPushButton, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class DashboardCard(QFrame):
    """Individual dashboard stat card."""
    
    def __init__(self, title: str, value: str, icon: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon = icon
        self._setup_ui()
    
    def _setup_ui(self):
        """Build card UI."""
        self.setObjectName("dashboardCard")
        self.setFrameStyle(QFrame.Shape.Box)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Icon and title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(self.value)
        value_font = QFont()
        value_font.setPointSize(32)
        value_font.setBold(True)
        value_label.setFont(value_font)
        layout.addWidget(value_label)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("color: #888;")
        layout.addWidget(title_label)
        
        # Style
        self.setStyleSheet("""
            QFrame#dashboardCard {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
            }
        """)


class DashboardView(QWidget):
    """Dashboard overview showing key stats and quick access."""
    
    # Signals for quick add actions
    create_task_requested = Signal()
    create_note_requested = Signal()
    import_document_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build dashboard UI with only quick add button."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add stretch to push button to bottom
        layout.addStretch()
        
        # Quick Add button (bottom left)
        quick_add_layout = QHBoxLayout()
        
        self._quick_add_btn = QPushButton("➕")
        self._quick_add_btn.setFixedSize(60, 60)
        self._quick_add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._quick_add_btn.setStyleSheet("""
            QPushButton {
                background: #c69749;
                color: white;
                font-size: 24px;
                border: none;
                border-radius: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #d4a870;
            }
            QPushButton:pressed {
                background: #b8854a;
            }
        """)
        self._quick_add_btn.clicked.connect(self._show_quick_add_menu)
        
        quick_add_layout.addWidget(self._quick_add_btn, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        quick_add_layout.addStretch()
        layout.addLayout(quick_add_layout)
    
    def _show_quick_add_menu(self):
        """Show quick add context menu."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #c69749;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item:selected {
                background: #c69749;
                color: white;
            }
        """)
        
        # Add menu items
        task_action = menu.addAction("➕ New Task")
        note_action = menu.addAction("📝 New Note")
        import_action = menu.addAction("📤 Import Document")
        
        # Connect actions
        task_action.triggered.connect(self.create_task_requested.emit)
        note_action.triggered.connect(self.create_note_requested.emit)
        import_action.triggered.connect(self.import_document_requested.emit)
        
        # Show menu below button
        menu.exec(self._quick_add_btn.mapToGlobal(self._quick_add_btn.rect().bottomLeft()))

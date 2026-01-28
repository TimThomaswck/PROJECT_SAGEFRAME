"""Navigation sidebar with icon + text buttons."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon


class NavigationSidebar(QWidget):
    """Sidebar navigation with icon + text buttons.
    
    Signals:
        navigationChanged: Emitted when user selects a navigation item.
                          Payload: section_name (str)
    """
    
    navigationChanged = Signal(str)
    
    # Navigation sections
    DASHBOARD = "dashboard"
    CALENDAR = "calendar"
    TASKS = "tasks"
    NOTES = "notes"
    PROJECTS = "projects"
    HABITS = "habits"
    PROGRESS = "progress"
    SETTINGS = "settings"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_section = self.DASHBOARD
        self._buttons = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """Build the sidebar layout."""
        self.setObjectName("navigationSidebar")
        self.setFixedWidth(180)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)
        
        # Logo/Title area
        title_label = QLabel("SageFrame")
        title_label.setObjectName("sidebarTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel#sidebarTitle {
                font-size: 18px;
                font-weight: bold;
                color: #c69749;
                padding: 12px 0;
            }
        """)
        layout.addWidget(title_label)
        
        # Navigation buttons
        nav_items = [
            (self.DASHBOARD, "Dashboard", "📊"),
            (self.CALENDAR, "Calendar", "📅"),
            (self.TASKS, "Tasks", "✅"),
            (self.PROJECTS, "Projects", "📁"),
            (self.HABITS, "Habits", "🎯"),
            (self.PROGRESS, "Progress", "📈"),
        ]
        
        for section_id, label_text, icon_text in nav_items:
            btn = self._create_nav_button(section_id, label_text, icon_text)
            self._buttons[section_id] = btn
            layout.addWidget(btn)
        
        # Spacer to push settings to bottom
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Settings at bottom
        settings_btn = self._create_nav_button(self.SETTINGS, "Settings", "⚙️")
        self._buttons[self.SETTINGS] = settings_btn
        layout.addWidget(settings_btn)
        
        # Highlight default section
        self._highlight_button(self.DASHBOARD)
    
    def _create_nav_button(self, section_id: str, label: str, icon: str) -> QPushButton:
        """Create a navigation button with icon + text."""
        btn = QPushButton(f"{icon}  {label}")
        btn.setObjectName(f"navButton_{section_id}")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(44)
        btn.clicked.connect(lambda: self._on_nav_button_clicked(section_id))
        
        # Button styling
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 16px;
                border: none;
                border-radius: 6px;
                background: transparent;
                color: #c0c0c0;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(198, 151, 73, 0.1);
                color: #d4d4d4;
            }
            QPushButton:checked {
                background: rgba(198, 151, 73, 0.2);
                color: #c69749;
                font-weight: bold;
            }
        """)
        
        return btn
    
    def _on_nav_button_clicked(self, section_id: str):
        """Handle navigation button click."""
        if section_id != self._current_section:
            self._current_section = section_id
            self._highlight_button(section_id)
            self.navigationChanged.emit(section_id)
    
    def _highlight_button(self, section_id: str):
        """Highlight the active navigation button."""
        for sid, btn in self._buttons.items():
            btn.setChecked(sid == section_id)
    
    def set_active_section(self, section_id: str):
        """Programmatically set active section."""
        self._current_section = section_id
        # Only highlight button if it exists in sidebar
        if section_id in self._buttons:
            self._highlight_button(section_id)
        # Always emit change so content area updates (even for sections not in sidebar like Notes)
        self.navigationChanged.emit(section_id)
    
    def get_active_section(self) -> str:
        """Get currently active section."""
        return self._current_section

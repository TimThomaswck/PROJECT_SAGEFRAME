"""Central content area that displays different sections based on navigation."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QLabel
from PySide6.QtCore import Qt


class ContentArea(QWidget):
    """Stacked widget container that displays different sections.
    
    Manages switching between Dashboard, Calendar, Tasks, Projects, Habits, Progress, Settings.
    """
    
    # Content indices
    DASHBOARD_INDEX = 0
    CALENDAR_INDEX = 1
    TASKS_INDEX = 2
    NOTES_INDEX = 3
    PROJECTS_INDEX = 4
    HABITS_INDEX = 5
    PROGRESS_INDEX = 6
    SETTINGS_INDEX = 7
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the stacked widget layout."""
        self.setObjectName("contentArea")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create stacked widget for switching between sections
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("contentStack")
        layout.addWidget(self.stacked_widget)
        
        # Add placeholder pages (will be populated by MainWindow)
        self._add_placeholder_pages()
    
    def _add_placeholder_pages(self):
        """Add empty placeholder pages for each section."""
        sections = [
            "Dashboard",
            "Calendar",
            "Tasks",
            "Notes",
            "Projects",
            "Habits",
            "Progress",
            "Settings"
        ]
        
        for section_name in sections:
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            label = QLabel(f"{section_name} View\n(Loading...)")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #888; font-size: 16px; padding: 40px;")
            placeholder_layout.addWidget(label)
            self.stacked_widget.addWidget(placeholder)
    
    def show_dashboard(self):
        """Show dashboard view."""
        self.stacked_widget.setCurrentIndex(self.DASHBOARD_INDEX)
    
    def show_calendar(self):
        """Show calendar view."""
        self.stacked_widget.setCurrentIndex(self.CALENDAR_INDEX)
    
    def show_tasks(self):
        """Show tasks view."""
        self.stacked_widget.setCurrentIndex(self.TASKS_INDEX)
    
    def show_notes(self):
        """Show notes view."""
        self.stacked_widget.setCurrentIndex(self.NOTES_INDEX)
    
    def show_projects(self):
        """Show projects view."""
        self.stacked_widget.setCurrentIndex(self.PROJECTS_INDEX)
    
    def show_habits(self):
        """Show habits view."""
        self.stacked_widget.setCurrentIndex(self.HABITS_INDEX)
    
    def show_progress(self):
        """Show progress view."""
        self.stacked_widget.setCurrentIndex(self.PROGRESS_INDEX)
    
    def show_settings(self):
        """Show settings view."""
        self.stacked_widget.setCurrentIndex(self.SETTINGS_INDEX)
    
    def set_widget_for_section(self, section_name: str, widget: QWidget):
        """Replace placeholder with actual widget for a section.
        
        Args:
            section_name: One of 'dashboard', 'calendar', 'tasks', 'projects', 'habits', 'progress', 'settings'
            widget: The widget to display for this section
        """
        index_map = {
            "dashboard": self.DASHBOARD_INDEX,
            "calendar": self.CALENDAR_INDEX,
            "tasks": self.TASKS_INDEX,
            "notes": self.NOTES_INDEX,
            "projects": self.PROJECTS_INDEX,
            "habits": self.HABITS_INDEX,
            "progress": self.PROGRESS_INDEX,
            "settings": self.SETTINGS_INDEX,
        }
        
        if section_name in index_map:
            index = index_map[section_name]
            # Remove old widget
            old_widget = self.stacked_widget.widget(index)
            if old_widget:
                self.stacked_widget.removeWidget(old_widget)
                old_widget.deleteLater()
            # Insert new widget at same index
            self.stacked_widget.insertWidget(index, widget)
            # Set current to maintain view if this was active
            if self.stacked_widget.currentIndex() == index:
                self.stacked_widget.setCurrentIndex(index)

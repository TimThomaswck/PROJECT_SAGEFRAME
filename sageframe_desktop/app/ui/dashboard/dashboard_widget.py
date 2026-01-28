"""Dashboard overview with stats and co-pilot action panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from app.ui.dashboard.dashboard_view import DashboardView


class DashboardWidget(QWidget):
    """Dashboard overview showing co-pilot action panel and stats.
    
    The main hub for user interaction with the co-pilot.
    """
    
    # Forward signals from dashboard view
    create_task_requested = Signal()
    create_note_requested = Signal()
    import_document_requested = Signal()
    
    def __init__(self, action_panel=None, parent=None):
        super().__init__(parent)
        self.action_panel = action_panel
        self.dashboard_view = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Build dashboard layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create dashboard view with quick add button
        self.dashboard_view = DashboardView(parent=self)
        
        # Forward signals from dashboard view
        self.dashboard_view.create_task_requested.connect(self.create_task_requested.emit)
        self.dashboard_view.create_note_requested.connect(self.create_note_requested.emit)
        self.dashboard_view.import_document_requested.connect(self.import_document_requested.emit)
        
        # If action panel was provided, add it
        if self.action_panel:
            layout.addWidget(self.action_panel, stretch=1)
        
        # Add dashboard view
        layout.addWidget(self.dashboard_view, stretch=1)
    
    def update_stats(self, tasks: int = 0, xp: int = 0, level: int = 1, habits: int = 0):
        """Update dashboard statistics (future enhancement)."""
        pass

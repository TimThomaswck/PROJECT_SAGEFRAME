"""Habits tracking view."""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from app.ui.habits.habit_tracker_grid import HabitTrackerGrid


class HabitsView(QWidget):
    """Habits tracking view with Habitica-style grid layout.
    
    Story 7.1: Simple Habit Tracker
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the habits tracking UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add habit tracker grid
        self.habit_tracker = HabitTrackerGrid(self)
        layout.addWidget(self.habit_tracker)

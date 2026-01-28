"""Habits tracking view."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class HabitsView(QWidget):
    """Habits tracking view.
    
    Will be implemented in Epic 7, Story 7.1.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build placeholder UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel("🎯 Habits Tracker")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Track daily habits and build streaks\n\n"
            "Coming soon in Epic 7, Story 7.1"
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
        layout.addWidget(desc_label)
        
        features_label = QLabel(
            "Features:\n"
            "• Daily habit check-ins\n"
            "• Streak tracking\n"
            "• Habit recommendations based on mood\n"
            "• Visual progress indicators"
        )
        features_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(features_label)

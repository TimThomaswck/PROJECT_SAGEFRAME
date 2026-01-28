"""Progress and gamification view."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ProgressView(QWidget):
    """Progress tracking and gamification view.
    
    Will show XP, levels, achievements from Epic 2, Story 2.6.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build placeholder UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel("📈 Progress & Achievements")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Track your productivity journey\n\n"
            "Enhanced in Epic 2, Story 2.6"
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
        layout.addWidget(desc_label)
        
        features_label = QLabel(
            "Features:\n"
            "• XP and Level system\n"
            "• Achievement badges\n"
            "• Productivity streaks\n"
            "• Weekly/monthly statistics\n"
            "• Task completion analytics"
        )
        features_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(features_label)

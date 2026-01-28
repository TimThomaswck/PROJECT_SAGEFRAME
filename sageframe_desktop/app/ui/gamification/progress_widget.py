"""UI widget to display gamified progress (level, XP, progress bar)."""

from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame
from PySide6.QtCore import Qt


class ProgressWidget(QWidget):
    """Simple progress display for XP/level."""

    def __init__(self, view_model, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._vm = view_model
        self._init_ui()
        if hasattr(self._vm, "progressChanged"):
            self._vm.progressChanged.connect(self._on_progress_changed)
        # Initial load
        self._on_progress_changed(self._vm.refresh())

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Lightweight notification banner for level-ups or achievements
        self._banner = QLabel()
        self._banner.setWordWrap(True)
        self._banner.setVisible(False)
        self._banner.setObjectName("progressBanner")
        self._banner.setStyleSheet(
            "QLabel#progressBanner {"
            " background-color: #0ea5e9;"
            " color: white;"
            " border-radius: 6px;"
            " padding: 8px;"
            " font-weight: bold;"
            "}"
        )

        self._level_label = QLabel("Level: -")
        self._level_label.setAlignment(Qt.AlignLeft)

        self._xp_label = QLabel("XP: -")
        self._xp_label.setAlignment(Qt.AlignLeft)

        self._next_label = QLabel("Next level: - XP remaining")
        self._next_label.setAlignment(Qt.AlignLeft)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFormat("Progress to next level: %p%")

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)

        layout.addWidget(self._banner)
        layout.addWidget(self._level_label)
        layout.addWidget(self._xp_label)
        layout.addWidget(self._next_label)
        layout.addWidget(self._progress_bar)
        layout.addWidget(divider)
        layout.addStretch()

        self.setLayout(layout)

    def _on_progress_changed(self, stats: dict):
        if not stats:
            return
        level = stats.get("current_level", 1)
        xp = stats.get("current_xp", 0)
        progress_pct = stats.get("progress_percentage", 0)
        xp_for_next = stats.get("xp_for_next_level", 0)
        xp_in_level = stats.get("xp_in_current_level", 0)
        remaining = max(xp_for_next - xp_in_level, 0)
        self._level_label.setText(f"Level: {level}")
        self._xp_label.setText(f"XP: {xp}")
        self._next_label.setText(f"Next level: {remaining} XP remaining")
        self._progress_bar.setValue(progress_pct)

    def show_level_up(self, level: int):
        """Display a short-lived banner for level-ups."""
        self._banner.setText(f"Level up! You reached level {level}.")
        self._banner.setVisible(True)

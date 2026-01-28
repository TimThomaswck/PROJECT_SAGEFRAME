"""ViewModel for gamification progress (XP, levels).

Provides simple getters to retrieve current progress stats for UI widgets.
"""

from typing import Optional, Dict

from PySide6.QtCore import QObject, Signal

from app.modules.gamification.services import GamificationService


class ProgressViewModel(QObject):
    """Expose gamification progress for UI consumption."""

    progressChanged = Signal(dict)
    levelUp = Signal(int)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._service = GamificationService()
        self._latest: Dict = {}
        self._last_level: int = 1

    def refresh(self) -> Dict:
        """Refresh progress stats and emit change signal."""
        stats = self._service.get_progress_stats()
        self._latest = stats
        current_level = stats.get("current_level", self._last_level)
        if current_level > self._last_level:
            self._last_level = current_level
            self.levelUp.emit(current_level)
        else:
            self._last_level = current_level
        self.progressChanged.emit(stats)
        return stats

    def get_cached(self) -> Dict:
        """Return last fetched stats without hitting the DB."""
        return self._latest

    def close(self):
        if self._service:
            self._service.close()

    def __del__(self):
        self.close()

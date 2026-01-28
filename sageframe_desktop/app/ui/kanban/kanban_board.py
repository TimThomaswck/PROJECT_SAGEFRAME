"""Kanban board UI widget for tasks.

Implements a simple Kanban board with columns per task status.
Uses TaskViewModel for data access and status updates.
"""

from typing import Dict, List, Optional, Any

from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
)


class KanbanTaskList(QListWidget):
    """List widget representing a Kanban column."""

    def __init__(self, status: str, move_callback, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._status = status
        self._move_callback = move_callback
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setObjectName(f"kanbanList_{status}")
        self.setUniformItemSizes(True)

    def startDrag(self, supported_actions: Qt.DropActions) -> None:
        item = self.currentItem()
        if item is None:
            return
        task_id = item.data(Qt.UserRole)
        if task_id is None:
            return
        mime_data = QMimeData()
        mime_data.setText(str(task_id))
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(supported_actions)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasText():
            event.ignore()
            return
        task_id = event.mimeData().text()
        try:
            task_id_int = int(task_id)
        except ValueError:
            event.ignore()
            return
        if self._move_callback(task_id_int, self._status):
            event.acceptProposedAction()
        else:
            event.ignore()


class KanbanBoardWidget(QWidget):
    """Kanban board component displaying tasks grouped by status."""

    def __init__(self, view_model, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._view_model = view_model
        self._columns: Dict[str, KanbanTaskList] = {}
        self._statuses: List[tuple[str, str]] = [
            ("todo", self.tr("To Do")),
            ("in_progress", self.tr("In Progress")),
            ("done", self.tr("Done")),
            ("blocked", self.tr("Blocked")),
        ]
        self._init_ui()
        # Keep in sync with ViewModel cache updates
        if hasattr(self._view_model, "tasksListChanged"):
            self._view_model.tasksListChanged.connect(self.refresh)
        self.refresh()

    def _init_ui(self) -> None:
        layout = QHBoxLayout()
        layout.setObjectName("kanbanLayout")
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)

        for status, label in self._statuses:
            column_widget = QWidget(self)
            column_layout = QVBoxLayout(column_widget)
            column_layout.setSpacing(6)
            column_layout.setContentsMargins(4, 4, 4, 4)

            header = QLabel(label)
            header.setObjectName(f"kanbanHeader_{status}")
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet("font-weight: bold;")

            list_widget = KanbanTaskList(status=status, move_callback=self._handle_move, parent=self)
            self._columns[status] = list_widget

            column_layout.addWidget(header)
            column_layout.addWidget(list_widget)
            layout.addWidget(column_widget)

        self.setLayout(layout)
        self.setObjectName("kanbanBoard")

    def refresh(self) -> None:
        """Populate columns from the ViewModel cache (no DB refresh)."""
        tasks_by_status = (
            self._view_model.get_tasks_grouped_by_status()
            if hasattr(self._view_model, "get_tasks_grouped_by_status")
            else {}
        )

        for status, list_widget in self._columns.items():
            list_widget.clear()
            for task in tasks_by_status.get(status, []):
                item = QListWidgetItem(self._format_task_text(task))
                item.setData(Qt.UserRole, task.get("id"))
                list_widget.addItem(item)

    def _format_task_text(self, task: Dict[str, Any]) -> str:
        title = task.get("title", "")
        priority = task.get("priority", "") or ""
        complexity = task.get("complexity", "") or ""
        return f"{title}\nPriority: {priority}\nComplexity: {complexity}"

    def _handle_move(self, task_id: int, new_status: str) -> bool:
        """Handle move event from a column."""
        if hasattr(self._view_model, "update_task_status"):
            return bool(self._view_model.update_task_status(task_id, new_status))
        return False

    # Utility exposed for tests
    def move_task(self, task_id: int, new_status: str) -> bool:
        return self._handle_move(task_id, new_status)

    def column_items(self, status: str) -> List[str]:
        """Return the list of item titles for a column (for testing)."""
        widget = self._columns.get(status)
        if widget is None:
            return []
        return [widget.item(i).text() for i in range(widget.count())]

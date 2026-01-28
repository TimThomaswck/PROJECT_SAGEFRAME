import pytest
from PySide6.QtCore import QObject, Signal

from app.ui.kanban.kanban_board import KanbanBoardWidget
from app.modules.tasks.view_models import TaskViewModel


class FakeKanbanViewModel(QObject):
    tasksListChanged = Signal()

    def __init__(self):
        super().__init__()
        self.calls = []
        self.tasks_by_status = {
            "todo": [
                {"id": 1, "title": "Todo Task", "priority": "medium", "complexity": "moderate"}
            ],
            "in_progress": [
                {"id": 2, "title": "Doing Task", "priority": "high", "complexity": "complex"}
            ],
            "done": [],
            "blocked": [],
        }

    def refresh_tasks(self):
        self.calls.append("refresh")
        return True

    def get_tasks_grouped_by_status(self):
        return self.tasks_by_status

    def update_task_status(self, task_id: int, new_status: str):
        self.calls.append((task_id, new_status))
        return True


@pytest.fixture
def fake_view_model():
    return FakeKanbanViewModel()


def test_kanban_board_renders_columns(qtbot, fake_view_model):
    widget = KanbanBoardWidget(fake_view_model)
    qtbot.addWidget(widget)

    todo_items = widget.column_items("todo")
    in_progress_items = widget.column_items("in_progress")

    assert any("Todo Task" in text for text in todo_items)
    assert any("Doing Task" in text for text in in_progress_items)
    # refresh_tasks should be invoked during initialization
    assert "refresh" in fake_view_model.calls


def test_kanban_board_move_updates_status(qtbot, fake_view_model):
    widget = KanbanBoardWidget(fake_view_model)
    qtbot.addWidget(widget)

    moved = widget.move_task(1, "done")

    assert moved is True
    assert (1, "done") in fake_view_model.calls


def test_task_viewmodel_groups_tasks_by_status(monkeypatch):
    vm = TaskViewModel()

    # Inject fake cache to avoid DB access
    vm._tasks_cache = [
        {"id": 1, "title": "t1", "status": "todo"},
        {"id": 2, "title": "t2", "status": "in_progress"},
        {"id": 3, "title": "t3", "status": "done"},
    ]

    grouped = vm.get_tasks_grouped_by_status()

    assert len(grouped["todo"]) == 1
    assert len(grouped["in_progress"]) == 1
    assert len(grouped["done"]) == 1

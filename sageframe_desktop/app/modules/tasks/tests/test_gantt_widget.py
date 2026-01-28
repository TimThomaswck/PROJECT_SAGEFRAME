"""UI tests for GanttChartWidget layout and interactions."""

from datetime import datetime, timedelta, timezone

import pytest

from app.ui.gantt.gantt_view import GanttChartWidget


class DummyGanttViewModel:
    def __init__(self):
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.tasks = [
            {
                "id": 1,
                "title": "Task A",
                "start_date": base,
                "end_date": base + timedelta(days=2),
                "depends_on_task_id": None,
                "dependency_type": None,
                "project_id": None,
            },
            {
                "id": 2,
                "title": "Task B",
                "start_date": base + timedelta(days=1),
                "end_date": base + timedelta(days=3),
                "depends_on_task_id": 1,
                "dependency_type": "finish_to_start",
                "project_id": None,
            },
        ]
        self.last_update = None

    def load_tasks(self):
        return self.tasks

    def update_task_dates(self, task_id, start_date, end_date):
        self.last_update = (task_id, start_date, end_date)
        for task in self.tasks:
            if task["id"] == task_id:
                task["start_date"] = start_date
                task["end_date"] = end_date
        return True


def test_widget_renders_tasks(qtbot):
    vm = DummyGanttViewModel()
    widget = GanttChartWidget(view_model=vm)
    qtbot.addWidget(widget)

    widget.refresh()
    assert widget.task_count() == 2


def test_scale_switch_updates_state(qtbot):
    vm = DummyGanttViewModel()
    widget = GanttChartWidget(view_model=vm)
    qtbot.addWidget(widget)

    widget.set_time_scale("Weekly")
    assert widget.current_scale() == "weekly"


def test_apply_task_time_change_calls_view_model(qtbot):
    vm = DummyGanttViewModel()
    widget = GanttChartWidget(view_model=vm)
    qtbot.addWidget(widget)

    start = vm.tasks[0]["start_date"] + timedelta(days=1)
    end = start + timedelta(days=2)
    result = widget.apply_task_time_change(1, start, end)

    assert result is True
    assert vm.last_update == (1, start, end)
    assert vm.tasks[0]["start_date"] == start
    assert vm.tasks[0]["end_date"] == end

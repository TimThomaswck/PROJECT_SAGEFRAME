"""Tests for GanttViewModel timeline and dependency handling."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.database import Base
from app.modules.tasks.gantt_view_model import GanttViewModel
from app.modules.tasks.services import TaskService
from app.modules.tasks.models import TaskDependencyType


@pytest.fixture
def test_db_session():
    """In-memory database for Gantt tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    yield session
    session.close()
    Session.remove()
    engine.dispose()


@pytest.fixture
def task_service(test_db_session):
    return TaskService(session=test_db_session)


@pytest.fixture
def gantt_vm(task_service):
    return GanttViewModel(task_service)


def _make_task(task_service, title: str, start: datetime, end: datetime, dependency=None):
    return task_service.create_task(
        title=title,
        start_date=start,
        end_date=end,
        depends_on_task_id=dependency,
        dependency_type=TaskDependencyType.FINISH_TO_START,
    )


def test_load_tasks_returns_timeline_dicts(gantt_vm, task_service):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _make_task(task_service, "A", base, base + timedelta(days=2))
    _make_task(task_service, "B", base + timedelta(days=1), base + timedelta(days=3), dependency=1)

    tasks = gantt_vm.load_tasks()
    assert len(tasks) == 2
    ids = {t["id"] for t in tasks}
    assert ids == {1, 2}
    assert tasks[0]["start_date"] <= tasks[0]["end_date"]
    assert tasks[1]["depends_on_task_id"] == 1


def test_update_task_dates_persists(gantt_vm, task_service):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    task = _make_task(task_service, "A", base, base + timedelta(days=2))

    new_start = base + timedelta(days=2)
    new_end = new_start + timedelta(days=1)
    result = gantt_vm.update_task_dates(task.id, new_start, new_end)
    assert result is True

    updated = task_service.get_task(task.id)
    assert updated.start_date == new_start
    assert updated.end_date == new_end


def test_update_task_dates_invalid_range(gantt_vm):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = gantt_vm.update_task_dates(123, base + timedelta(days=2), base)
    assert result is False

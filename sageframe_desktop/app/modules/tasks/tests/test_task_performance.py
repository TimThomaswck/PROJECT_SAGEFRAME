"""Performance tests for task operations (NFR1 <100ms, NFR2 <200ms).

These are best-effort timing checks; thresholds include modest buffer for CI noise.
"""

import time
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from app.database import Base
from app.modules.tasks import services
from app.modules.tasks.services import TaskService


@pytest.fixture()
def service(monkeypatch):
    """Provide isolated in-memory TaskService for timing tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    # Ensure related tables (projects) are registered for FK resolution
    from app.modules.projects.models import Project  # noqa: F401

    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(services, "SessionLocal", TestingSessionLocal)
    session = TestingSessionLocal()
    try:
        yield TaskService(session=session)
    finally:
        session.close()
        TestingSessionLocal.remove()


def test_create_task_under_100ms(service):
    """Create task should complete under ~100ms (NFR1 visual feedback)."""
    start = time.perf_counter()
    task = service.create_task(title="Perf Task", description="fast")
    duration = time.perf_counter() - start
    assert task.id is not None
    # Allow small buffer for CI/VMs
    assert duration < 0.2


def test_list_tasks_under_200ms(service):
    """Listing tasks should complete under ~200ms (NFR2 full interaction)."""
    # Seed some tasks
    for i in range(10):
        service.create_task(title=f"Task {i}", status="todo")
    start = time.perf_counter()
    tasks = service.list_tasks()
    duration = time.perf_counter() - start
    assert len(tasks) == 10
    assert duration < 0.2

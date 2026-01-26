"""Integration tests for TaskService with real SQLite (in-memory)."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from app.database import Base
from app.modules.projects.models import Project
from app.modules.tasks import services
from app.modules.tasks.models import Task
from app.modules.tasks.services import TaskService


@pytest.fixture()
def db_session(monkeypatch):
    """Provide an isolated in-memory database session and patch SessionLocal."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    # Create all tables for tasks and projects
    Base.metadata.create_all(bind=engine)

    # Patch SessionLocal used in services
    monkeypatch.setattr(services, "SessionLocal", TestingSessionLocal)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        TestingSessionLocal.remove()


def test_task_crud_end_to_end(db_session):
    """End-to-end CRUD flow for standalone task."""
    service = TaskService(session=db_session)

    # Create
    task = service.create_task(title="Integration Task", description="End-to-end")
    assert task.id is not None
    assert task.title == "Integration Task"

    # Read
    fetched = service.get_task(task.id)
    assert fetched is not None
    assert fetched.title == "Integration Task"

    # Update
    updated = service.update_task(task.id, title="Updated Title", status="in_progress")
    assert updated.title == "Updated Title"
    assert updated.status == "in_progress"

    # Delete
    deleted = service.delete_task(task.id)
    assert deleted is True
    assert service.get_task(task.id) is None


def test_task_with_project_association(db_session):
    """End-to-end task with project association and foreign key integrity."""
    # Create project
    project = Project(name="Integration Project", description="Proj desc")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    service = TaskService(session=db_session)

    # Create task linked to project
    task = service.create_task(
        title="Project Task",
        description="linked",
        project_id=project.id,
        status="todo",
    )
    assert task.project_id == project.id

    # Ensure relationship is maintained
    fetched = service.get_task(task.id)
    assert fetched.project_id == project.id

    # Delete task and ensure project still exists
    service.delete_task(task.id)
    still_project = db_session.get(Project, project.id)
    assert still_project is not None


def test_task_listing_filters(db_session):
    """Verify list filters by project and status with real DB."""
    service = TaskService(session=db_session)

    # Create sample tasks
    t1 = service.create_task(title="T1", status="todo")
    t2 = service.create_task(title="T2", status="done")

    # List all
    all_tasks = service.list_tasks()
    assert {t.id for t in all_tasks} == {t1.id, t2.id}

    # Filter by status
    done_tasks = service.list_tasks(status="done")
    assert len(done_tasks) == 1
    assert done_tasks[0].status == "done"

    # Filter standalone tasks
    standalone = service.list_standalone_tasks()
    assert len(standalone) == 2

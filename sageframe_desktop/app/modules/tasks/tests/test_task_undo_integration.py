"""Undo/Redo integration tests for task operations using UndoManager and commands."""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.core.undo_manager import UndoManager
from app.core.undo_commands import CreateTaskCommand, EditTaskCommand, DeleteTaskCommand, EditTaskPropertiesCommand
from app.database import Base
from app.modules.tasks import services
from app.modules.tasks.services import TaskService
from app.modules.tasks.models import TaskPriority, TaskComplexity


@pytest.fixture()
def undo_manager():
    return UndoManager()


@pytest.fixture()
def service(monkeypatch):
    """Provide isolated in-memory TaskService for undo tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    # Ensure FK dependencies are loaded
    from app.modules.projects.models import Project  # noqa: F401

    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(services, "SessionLocal", TestingSessionLocal)
    session = TestingSessionLocal()
    try:
        yield TaskService(session=session)
    finally:
        session.close()
        TestingSessionLocal.remove()


def test_create_task_undo_redo(service, undo_manager):
    """Create task via command, undo deletes it, redo recreates it."""
    from app.modules.tasks.models import TaskPriority, TaskComplexity
    cmd = CreateTaskCommand(
        service=service,
        title="Undo Task",
        description="desc",
        status="todo",
        priority=TaskPriority.MEDIUM,
        complexity=TaskComplexity.MODERATE
    )

    # Execute command (create)
    undo_manager.push(cmd)
    created_id = cmd.get_task_id()
    assert created_id is not None
    assert service.get_task(created_id) is not None

    # Undo should delete
    undo_manager.undo()
    assert service.get_task(created_id) is None

    # Redo should recreate
    undo_manager.redo()
    recreated = service.get_task(cmd.get_task_id())
    assert recreated is not None
    assert recreated.title == "Undo Task"


def test_edit_task_undo_redo(service, undo_manager):
    """Edit task and verify undo/redo restores titles."""
    base = service.create_task(title="Original", status="todo")
    cmd = EditTaskCommand(
        service=service,
        task_id=base.id,
        new_title="Updated",
        new_status="done"
    )

    undo_manager.push(cmd)
    updated = service.get_task(base.id)
    assert updated.title == "Updated"
    assert updated.status == "done"

    undo_manager.undo()
    reverted = service.get_task(base.id)
    assert reverted.title == "Original"

    undo_manager.redo()
    redone = service.get_task(base.id)
    assert redone.title == "Updated"


def test_delete_task_undo_redo(service, undo_manager):
    """Delete task and undo should restore it."""
    base = service.create_task(title="To Delete", status="todo")
    cmd = DeleteTaskCommand(service=service, task_id=base.id)

    undo_manager.push(cmd)
    assert service.get_task(base.id) is None

    undo_manager.undo()
    restored = service.get_task(base.id)
    assert restored is not None
    assert restored.title == "To Delete"


def test_edit_task_property_priority_undo_redo(service, undo_manager):
    """Edit task priority and verify undo/redo."""
    base = service.create_task(title="Priority Task", priority=TaskPriority.LOW)
    assert base.priority == TaskPriority.LOW
    
    cmd = EditTaskCommand(
        service=service,
        task_id=base.id,
        new_priority=TaskPriority.HIGH
    )
    
    undo_manager.push(cmd)
    updated = service.get_task(base.id)
    assert updated.priority == TaskPriority.HIGH
    
    # Undo should restore
    undo_manager.undo()
    reverted = service.get_task(base.id)
    assert reverted.priority == TaskPriority.LOW
    
    # Redo should re-apply
    undo_manager.redo()
    redone = service.get_task(base.id)
    assert redone.priority == TaskPriority.HIGH


def test_edit_task_property_complexity_undo_redo(service, undo_manager):
    """Edit task complexity and verify undo/redo."""
    base = service.create_task(title="Complexity Task", complexity=TaskComplexity.SIMPLE)
    assert base.complexity == TaskComplexity.SIMPLE
    
    cmd = EditTaskCommand(
        service=service,
        task_id=base.id,
        new_complexity=TaskComplexity.COMPLEX
    )
    
    undo_manager.push(cmd)
    updated = service.get_task(base.id)
    assert updated.complexity == TaskComplexity.COMPLEX
    
    undo_manager.undo()
    reverted = service.get_task(base.id)
    assert reverted.complexity == TaskComplexity.SIMPLE
    
    undo_manager.redo()
    redone = service.get_task(base.id)
    assert redone.complexity == TaskComplexity.COMPLEX


def test_edit_task_both_properties_undo_redo(service, undo_manager):
    """Edit both priority and complexity, verify undo/redo."""
    base = service.create_task(
        title="Multi Property Task",
        priority=TaskPriority.LOW,
        complexity=TaskComplexity.SIMPLE
    )
    
    cmd = EditTaskCommand(
        service=service,
        task_id=base.id,
        new_priority=TaskPriority.HIGH,
        new_complexity=TaskComplexity.COMPLEX
    )
    
    undo_manager.push(cmd)
    updated = service.get_task(base.id)
    assert updated.priority == TaskPriority.HIGH
    assert updated.complexity == TaskComplexity.COMPLEX
    
    undo_manager.undo()
    reverted = service.get_task(base.id)
    assert reverted.priority == TaskPriority.LOW
    assert reverted.complexity == TaskComplexity.SIMPLE


def test_edit_task_properties_command_undo_redo(service, undo_manager):
    """Test EditTaskPropertiesCommand specifically for properties."""
    base = service.create_task(
        title="Properties Command Task",
        priority=TaskPriority.MEDIUM,
        complexity=TaskComplexity.MODERATE
    )
    
    cmd = EditTaskPropertiesCommand(
        service=service,
        task_id=base.id,
        new_priority=TaskPriority.HIGH,
        new_complexity=TaskComplexity.COMPLEX
    )
    
    undo_manager.push(cmd)
    updated = service.get_task(base.id)
    assert updated.priority == TaskPriority.HIGH
    assert updated.complexity == TaskComplexity.COMPLEX
    
    undo_manager.undo()
    reverted = service.get_task(base.id)
    assert reverted.priority == TaskPriority.MEDIUM
    assert reverted.complexity == TaskComplexity.MODERATE
    
    undo_manager.redo()
    redone = service.get_task(base.id)
    assert redone.priority == TaskPriority.HIGH
    assert redone.complexity == TaskComplexity.COMPLEX


def test_multiple_property_changes_stack_in_undo(service, undo_manager):
    """Test that multiple property changes can be undone in sequence."""
    task = service.create_task(
        title="Multi-change Task",
        priority=TaskPriority.LOW,
        complexity=TaskComplexity.SIMPLE
    )
    
    # Change 1: Priority only
    cmd1 = EditTaskPropertiesCommand(
        service=service,
        task_id=task.id,
        new_priority=TaskPriority.HIGH
    )
    undo_manager.push(cmd1)
    
    # Change 2: Complexity only
    cmd2 = EditTaskPropertiesCommand(
        service=service,
        task_id=task.id,
        new_complexity=TaskComplexity.COMPLEX
    )
    undo_manager.push(cmd2)
    
    # Verify both changes applied
    updated = service.get_task(task.id)
    assert updated.priority == TaskPriority.HIGH
    assert updated.complexity == TaskComplexity.COMPLEX
    
    # Undo change 2 (complexity)
    undo_manager.undo()
    after_undo1 = service.get_task(task.id)
    assert after_undo1.priority == TaskPriority.HIGH
    assert after_undo1.complexity == TaskComplexity.SIMPLE
    
    # Undo change 1 (priority)
    undo_manager.undo()
    after_undo2 = service.get_task(task.id)
    assert after_undo2.priority == TaskPriority.LOW
    assert after_undo2.complexity == TaskComplexity.SIMPLE

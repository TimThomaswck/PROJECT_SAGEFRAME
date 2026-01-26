"""Unit tests for TaskService.

Tests cover:
- CRUD operations (create, read, update, delete)
- Task properties: priority and complexity
- Project association and standalone tasks
- Filtering and listing
- Validation and error handling
- Context manager pattern
"""

import pytest
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from app.database import Base
from app.modules.tasks.models import Task, TaskPriority, TaskComplexity
from app.modules.tasks.services import TaskService
from app.modules.projects.models import Project


@pytest.fixture
def test_db():
    """Create an in-memory test database."""
    # Use in-memory database to avoid Windows file locking issues
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    
    yield session
    
    session.close()
    Session.remove()
    engine.dispose()


@pytest.fixture
def task_service(test_db):
    """Create TaskService with test database."""
    service = TaskService(session=test_db)
    yield service
    # Don't close - session is managed by test_db fixture


@pytest.fixture
def project(test_db):
    """Create a test project for task association."""
    project = Project(
        name="Test Project",
        description="A test project",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)
    return project


class TestTaskServiceCreate:
    """Tests for TaskService.create_task()."""
    
    def test_create_task_minimal(self, task_service):
        """Test creating task with only required fields."""
        task = task_service.create_task(title="Simple Task")
        
        assert task.id is not None
        assert task.title == "Simple Task"
        assert task.description is None
        assert task.due_date is None
        assert task.status == "todo"
        assert task.project_id is None
    
    def test_create_task_full(self, task_service, project):
        """Test creating task with all fields."""
        due = datetime.now(timezone.utc) + timedelta(days=7)
        
        task = task_service.create_task(
            title="Full Task",
            description="Detailed description",
            due_date=due,
            status="in_progress",
            project_id=project.id,
            user_id=1
        )
        
        assert task.title == "Full Task"
        assert task.description == "Detailed description"
        assert task.due_date is not None
        assert task.status == "in_progress"
        assert task.project_id == project.id
        assert task.user_id == 1
    
    def test_create_task_title_whitespace_stripped(self, task_service):
        """Test that title whitespace is stripped."""
        task = task_service.create_task(title="  Whitespace Task  ")
        assert task.title == "Whitespace Task"
    
    def test_create_task_empty_title_fails(self, task_service):
        """Test that empty title raises error."""
        with pytest.raises(ValueError):
            task_service.create_task(title="")
    
    def test_create_task_whitespace_only_title_fails(self, task_service):
        """Test that whitespace-only title raises error."""
        with pytest.raises(ValueError):
            task_service.create_task(title="   ")
    
    def test_create_task_invalid_status_fails(self, task_service):
        """Test that invalid status raises error."""
        with pytest.raises(ValueError):
            task_service.create_task(title="Task", status="invalid")
    
    def test_create_standalone_task(self, task_service):
        """Test creating task without project association."""
        task = task_service.create_task(title="Standalone")
        assert task.project_id is None
    
    def test_create_task_with_project(self, task_service, project):
        """Test creating task with project association."""
        task = task_service.create_task(
            title="Project Task",
            project_id=project.id
        )
        assert task.project_id == project.id


class TestTaskServiceRead:
    """Tests for TaskService read operations."""
    
    def test_get_task_success(self, task_service):
        """Test getting existing task."""
        created = task_service.create_task(title="Test")
        retrieved = task_service.get_task(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test"
    
    def test_get_task_not_found(self, task_service):
        """Test getting non-existent task returns None."""
        result = task_service.get_task(99999)
        assert result is None
    
    def test_list_tasks_empty(self, task_service):
        """Test listing tasks when none exist."""
        tasks = task_service.list_tasks()
        assert tasks == []
    
    def test_list_tasks_multiple(self, task_service):
        """Test listing multiple tasks."""
        task_service.create_task(title="Task 1")
        task_service.create_task(title="Task 2")
        task_service.create_task(title="Task 3")
        
        tasks = task_service.list_tasks()
        assert len(tasks) == 3
    
    def test_list_tasks_ordered_by_created_desc(self, task_service):
        """Test tasks are ordered newest first."""
        import time
        task1 = task_service.create_task(title="First")
        time.sleep(0.01)  # Ensure distinct timestamps
        task2 = task_service.create_task(title="Second")
        time.sleep(0.01)  # Ensure distinct timestamps
        task3 = task_service.create_task(title="Third")
        
        tasks = task_service.list_tasks()
        # Newest first
        assert tasks[0].id == task3.id
        assert tasks[1].id == task2.id
        assert tasks[2].id == task1.id
    
    def test_list_tasks_filter_by_project(self, task_service, project):
        """Test filtering tasks by project."""
        task_service.create_task(title="Project Task", project_id=project.id)
        task_service.create_task(title="Standalone Task")
        
        project_tasks = task_service.list_tasks(project_id=project.id)
        assert len(project_tasks) == 1
        assert project_tasks[0].title == "Project Task"
    
    def test_list_tasks_filter_by_status(self, task_service):
        """Test filtering tasks by status."""
        task_service.create_task(title="Todo 1", status="todo")
        task_service.create_task(title="Todo 2", status="todo")
        task_service.create_task(title="Done", status="done")
        
        todo_tasks = task_service.list_tasks(status="todo")
        assert len(todo_tasks) == 2
    
    def test_list_standalone_tasks(self, task_service, project):
        """Test listing only standalone tasks."""
        task_service.create_task(title="Project Task", project_id=project.id)
        task_service.create_task(title="Standalone 1")
        task_service.create_task(title="Standalone 2")
        
        standalone = task_service.list_standalone_tasks()
        assert len(standalone) == 2
    
    def test_get_tasks_by_project(self, task_service, project):
        """Test getting tasks for specific project."""
        task_service.create_task(title="Task 1", project_id=project.id)
        task_service.create_task(title="Task 2", project_id=project.id)
        task_service.create_task(title="Other")
        
        project_tasks = task_service.get_tasks_by_project(project.id)
        assert len(project_tasks) == 2
    
    def test_count_tasks_by_project(self, task_service, project):
        """Test counting tasks in a project."""
        task_service.create_task(title="Task 1", project_id=project.id)
        task_service.create_task(title="Task 2", project_id=project.id)
        task_service.create_task(title="Other")
        
        count = task_service.count_tasks_by_project(project.id)
        assert count == 2
    
    def test_count_tasks_empty_project(self, task_service, project):
        """Test counting tasks in project with no tasks."""
        count = task_service.count_tasks_by_project(project.id)
        assert count == 0


class TestTaskServiceUpdate:
    """Tests for TaskService.update_task()."""
    
    def test_update_task_title(self, task_service):
        """Test updating task title."""
        task = task_service.create_task(title="Original")
        updated = task_service.update_task(task.id, title="Updated")
        
        assert updated is not None
        assert updated.title == "Updated"
    
    def test_update_task_description(self, task_service):
        """Test updating task description."""
        task = task_service.create_task(title="Task", description="Old")
        updated = task_service.update_task(task.id, description="New")
        
        assert updated.description == "New"
    
    def test_update_task_status(self, task_service):
        """Test updating task status."""
        task = task_service.create_task(title="Task", status="todo")
        updated = task_service.update_task(task.id, status="done")
        
        assert updated.status == "done"
    
    def test_update_task_project(self, task_service, project):
        """Test updating task project association."""
        task = task_service.create_task(title="Task")
        updated = task_service.update_task(task.id, project_id=project.id)
        
        assert updated.project_id == project.id
    
    def test_update_task_multiple_fields(self, task_service):
        """Test updating multiple fields at once."""
        task = task_service.create_task(title="Old", status="todo")
        updated = task_service.update_task(
            task.id,
            title="New",
            status="in_progress"
        )
        
        assert updated.title == "New"
        assert updated.status == "in_progress"
    
    def test_update_task_not_found(self, task_service):
        """Test updating non-existent task returns None."""
        result = task_service.update_task(99999, title="Test")
        assert result is None
    
    def test_update_task_empty_title_fails(self, task_service):
        """Test updating with empty title fails."""
        task = task_service.create_task(title="Original")
        with pytest.raises(ValueError):
            task_service.update_task(task.id, title="")
    
    def test_update_task_invalid_status_fails(self, task_service):
        """Test updating with invalid status fails."""
        task = task_service.create_task(title="Task")
        with pytest.raises(ValueError):
            task_service.update_task(task.id, status="invalid")
    
    def test_update_task_updates_timestamp(self, task_service):
        """Test that update changes updated_at timestamp."""
        task = task_service.create_task(title="Task")
        original_updated = task.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        updated = task_service.update_task(task.id, title="Updated")
        assert updated.updated_at >= original_updated
    
    def test_update_task_only_provided_fields(self, task_service, project):
        """Test that only provided fields are updated."""
        task = task_service.create_task(
            title="Original",
            description="Keep this",
            status="todo",
            project_id=project.id
        )
        
        # Only update title
        updated = task_service.update_task(task.id, title="New Title")
        
        # Other fields should be unchanged
        assert updated.title == "New Title"
        assert updated.description == "Keep this"
        assert updated.status == "todo"
        assert updated.project_id == project.id


class TestTaskServiceDelete:
    """Tests for TaskService.delete_task()."""
    
    def test_delete_task_success(self, task_service):
        """Test deleting existing task."""
        task = task_service.create_task(title="To Delete")
        result = task_service.delete_task(task.id)
        
        assert result is True
        assert task_service.get_task(task.id) is None
    
    def test_delete_task_not_found(self, task_service):
        """Test deleting non-existent task."""
        result = task_service.delete_task(99999)
        assert result is False
    
    def test_delete_task_removes_from_list(self, task_service):
        """Test that deleted task is removed from list."""
        task1 = task_service.create_task(title="Keep")
        task2 = task_service.create_task(title="Delete")
        
        task_service.delete_task(task2.id)
        
        tasks = task_service.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == task1.id


class TestTaskServiceContextManager:
    """Tests for TaskService context manager."""
    
    def test_context_manager_basic(self, test_db):
        """Test that context manager works with provided session."""
        with TaskService(session=test_db) as service:
            # Service should be usable
            task = service.create_task(title="Test")
            assert task.id is not None
        
        # Service can still work since we provided external session
    
    def test_multiple_operations_same_service(self, task_service):
        """Test multiple operations on same service instance."""
        task1 = task_service.create_task(title="Task 1")
        task2 = task_service.create_task(title="Task 2")
        
        task_service.update_task(task1.id, status="done")
        task_service.delete_task(task2.id)
        
        tasks = task_service.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].status == "done"


class TestTaskServiceWithProperties:
    """Tests for task property management (priority and complexity)."""
    
    def test_create_task_with_priority_enum(self, task_service):
        """Test creating task with priority enum."""
        task = task_service.create_task(
            title="Priority Task",
            priority=TaskPriority.HIGH
        )
        
        assert task.priority == TaskPriority.HIGH
    
    def test_create_task_with_priority_string(self, task_service):
        """Test creating task with priority as string."""
        task = task_service.create_task(
            title="Priority Task",
            priority="low"
        )
        
        assert task.priority == TaskPriority.LOW
    
    def test_create_task_priority_defaults(self, task_service):
        """Test task priority defaults to MEDIUM."""
        task = task_service.create_task(title="Task")
        assert task.priority == TaskPriority.MEDIUM
    
    def test_create_task_all_priority_levels(self, task_service):
        """Test creating tasks with all priority levels."""
        for priority in TaskPriority:
            task = task_service.create_task(
                title=f"Task {priority.value}",
                priority=priority
            )
            assert task.priority == priority
    
    def test_create_task_with_complexity_enum(self, task_service):
        """Test creating task with complexity enum."""
        task = task_service.create_task(
            title="Complex Task",
            complexity=TaskComplexity.COMPLEX
        )
        
        assert task.complexity == TaskComplexity.COMPLEX
    
    def test_create_task_with_complexity_string(self, task_service):
        """Test creating task with complexity as string."""
        task = task_service.create_task(
            title="Simple Task",
            complexity="simple"
        )
        
        assert task.complexity == TaskComplexity.SIMPLE
    
    def test_create_task_complexity_defaults(self, task_service):
        """Test task complexity defaults to MODERATE."""
        task = task_service.create_task(title="Task")
        assert task.complexity == TaskComplexity.MODERATE
    
    def test_create_task_all_complexity_levels(self, task_service):
        """Test creating tasks with all complexity levels."""
        for complexity in TaskComplexity:
            task = task_service.create_task(
                title=f"Task {complexity.value}",
                complexity=complexity
            )
            assert task.complexity == complexity
    
    def test_create_task_with_all_properties(self, task_service):
        """Test creating task with priority and complexity."""
        task = task_service.create_task(
            title="Complex High Priority Task",
            description="Needs attention",
            priority=TaskPriority.HIGH,
            complexity=TaskComplexity.COMPLEX
        )
        
        assert task.title == "Complex High Priority Task"
        assert task.priority == TaskPriority.HIGH
        assert task.complexity == TaskComplexity.COMPLEX
    
    def test_update_task_priority(self, task_service):
        """Test updating task priority."""
        task = task_service.create_task(title="Task", priority=TaskPriority.LOW)
        assert task.priority == TaskPriority.LOW
        
        updated = task_service.update_task(task.id, priority=TaskPriority.HIGH)
        assert updated.priority == TaskPriority.HIGH
    
    def test_update_task_priority_with_string(self, task_service):
        """Test updating task priority with string value."""
        task = task_service.create_task(title="Task")
        
        updated = task_service.update_task(task.id, priority="high")
        assert updated.priority == TaskPriority.HIGH
    
    def test_update_task_complexity(self, task_service):
        """Test updating task complexity."""
        task = task_service.create_task(title="Task", complexity=TaskComplexity.SIMPLE)
        assert task.complexity == TaskComplexity.SIMPLE
        
        updated = task_service.update_task(task.id, complexity=TaskComplexity.COMPLEX)
        assert updated.complexity == TaskComplexity.COMPLEX
    
    def test_update_task_complexity_with_string(self, task_service):
        """Test updating task complexity with string value."""
        task = task_service.create_task(title="Task")
        
        updated = task_service.update_task(task.id, complexity="simple")
        assert updated.complexity == TaskComplexity.SIMPLE
    
    def test_update_both_properties(self, task_service):
        """Test updating both priority and complexity."""
        task = task_service.create_task(title="Task")
        
        updated = task_service.update_task(
            task.id,
            priority=TaskPriority.HIGH,
            complexity=TaskComplexity.COMPLEX
        )
        
        assert updated.priority == TaskPriority.HIGH
        assert updated.complexity == TaskComplexity.COMPLEX
    
    def test_update_properties_only(self, task_service):
        """Test updating only properties, leaving other fields unchanged."""
        task = task_service.create_task(
            title="Original Title",
            description="Original Description",
            priority=TaskPriority.LOW,
            complexity=TaskComplexity.SIMPLE
        )
        
        updated = task_service.update_task(
            task.id,
            priority=TaskPriority.HIGH,
            complexity=TaskComplexity.COMPLEX
        )
        
        # Properties updated
        assert updated.priority == TaskPriority.HIGH
        assert updated.complexity == TaskComplexity.COMPLEX
        # Other fields unchanged
        assert updated.title == "Original Title"
        assert updated.description == "Original Description"
    
    def test_list_tasks_by_priority(self, task_service, project):
        """Test listing tasks filtered by priority."""
        # Create tasks with different priorities
        task_service.create_task(title="Low Priority", priority=TaskPriority.LOW, project_id=project.id)
        task_service.create_task(title="High Priority 1", priority=TaskPriority.HIGH, project_id=project.id)
        task_service.create_task(title="High Priority 2", priority=TaskPriority.HIGH, project_id=project.id)
        task_service.create_task(title="Medium Priority", priority=TaskPriority.MEDIUM, project_id=project.id)
        
        # List high priority tasks
        high_priority_tasks = task_service.list_tasks_by_priority(TaskPriority.HIGH)
        assert len(high_priority_tasks) == 2
        assert all(t.priority == TaskPriority.HIGH for t in high_priority_tasks)
        
        # List low priority tasks
        low_priority_tasks = task_service.list_tasks_by_priority(TaskPriority.LOW)
        assert len(low_priority_tasks) == 1
        assert low_priority_tasks[0].priority == TaskPriority.LOW
    
    def test_list_tasks_by_priority_with_project_filter(self, task_service, test_db):
        """Test listing tasks filtered by priority and project."""
        project1 = Project(
            name="Project 1",
            description="First project",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        test_db.add(project1)
        test_db.commit()
        test_db.refresh(project1)
        
        project2 = Project(
            name="Project 2",
            description="Second project",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        test_db.add(project2)
        test_db.commit()
        test_db.refresh(project2)
        
        service = TaskService(session=test_db)
        
        # Create tasks in different projects
        service.create_task(title="P1 High", priority=TaskPriority.HIGH, project_id=project1.id)
        service.create_task(title="P2 High", priority=TaskPriority.HIGH, project_id=project2.id)
        service.create_task(title="P1 Low", priority=TaskPriority.LOW, project_id=project1.id)
        
        # List high priority tasks in project1
        p1_high = service.list_tasks_by_priority(TaskPriority.HIGH, project_id=project1.id)
        assert len(p1_high) == 1
        assert p1_high[0].project_id == project1.id
        
        # List high priority tasks in project2
        p2_high = service.list_tasks_by_priority(TaskPriority.HIGH, project_id=project2.id)
        assert len(p2_high) == 1
        assert p2_high[0].project_id == project2.id
    
    def test_list_tasks_by_complexity(self, task_service, project):
        """Test listing tasks filtered by complexity."""
        # Create tasks with different complexities
        task_service.create_task(title="Simple", complexity=TaskComplexity.SIMPLE, project_id=project.id)
        task_service.create_task(title="Complex 1", complexity=TaskComplexity.COMPLEX, project_id=project.id)
        task_service.create_task(title="Complex 2", complexity=TaskComplexity.COMPLEX, project_id=project.id)
        task_service.create_task(title="Moderate", complexity=TaskComplexity.MODERATE, project_id=project.id)
        
        # List complex tasks
        complex_tasks = task_service.list_tasks_by_complexity(TaskComplexity.COMPLEX)
        assert len(complex_tasks) == 2
        assert all(t.complexity == TaskComplexity.COMPLEX for t in complex_tasks)
        
        # List simple tasks
        simple_tasks = task_service.list_tasks_by_complexity(TaskComplexity.SIMPLE)
        assert len(simple_tasks) == 1
        assert simple_tasks[0].complexity == TaskComplexity.SIMPLE
    
    def test_list_high_priority_tasks_convenience(self, task_service, project):
        """Test convenience method list_high_priority_tasks."""
        task_service.create_task(title="Low", priority=TaskPriority.LOW, project_id=project.id)
        task_service.create_task(title="High 1", priority=TaskPriority.HIGH, project_id=project.id)
        task_service.create_task(title="High 2", priority=TaskPriority.HIGH, project_id=project.id)
        
        high_tasks = task_service.list_high_priority_tasks()
        assert len(high_tasks) == 2
        assert all(t.priority == TaskPriority.HIGH for t in high_tasks)
    
    def test_list_complex_tasks_convenience(self, task_service, project):
        """Test convenience method list_complex_tasks."""
        task_service.create_task(title="Simple", complexity=TaskComplexity.SIMPLE, project_id=project.id)
        task_service.create_task(title="Complex 1", complexity=TaskComplexity.COMPLEX, project_id=project.id)
        task_service.create_task(title="Complex 2", complexity=TaskComplexity.COMPLEX, project_id=project.id)
        
        complex_tasks = task_service.list_complex_tasks()
        assert len(complex_tasks) == 2
        assert all(t.complexity == TaskComplexity.COMPLEX for t in complex_tasks)
    
    def test_invalid_priority_string_fails(self, task_service):
        """Test that invalid priority string raises error."""
        with pytest.raises(ValueError):
            task_service.create_task(title="Task", priority="invalid_priority")
    
    def test_invalid_complexity_string_fails(self, task_service):
        """Test that invalid complexity string raises error."""
        with pytest.raises(ValueError):
            task_service.create_task(title="Task", complexity="invalid_complexity")

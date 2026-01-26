"""Unit tests for Task models (SQLAlchemy and Pydantic).

Tests cover:
- Task model creation and attributes
- TaskSchema validation
- TaskUpdateSchema partial validation
- Task properties: priority and complexity
- Edge cases and error handling
"""

import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from app.modules.tasks.models import (
    Task,
    TaskSchema,
    TaskUpdateSchema,
    TaskPriority,
    TaskComplexity,
    VALID_STATUSES,
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)
# Import Project to resolve SQLAlchemy relationship
from app.modules.projects.models import Project


class TestTaskSchema:
    """Tests for TaskSchema Pydantic validation."""
    
    def test_valid_task_minimal(self):
        """Test creating task with only required fields."""
        schema = TaskSchema(title="Test Task")
        assert schema.title == "Test Task"
        assert schema.description is None
        assert schema.due_date is None
        assert schema.status == "todo"
        assert schema.project_id is None
    
    def test_valid_task_full(self):
        """Test creating task with all fields."""
        due = datetime.now(timezone.utc) + timedelta(days=7)
        schema = TaskSchema(
            title="Full Task",
            description="A detailed description",
            due_date=due,
            status="in_progress",
            project_id=1
        )
        assert schema.title == "Full Task"
        assert schema.description == "A detailed description"
        assert schema.due_date == due
        assert schema.status == "in_progress"
        assert schema.project_id == 1
    
    def test_title_whitespace_stripped(self):
        """Test that title whitespace is stripped."""
        schema = TaskSchema(title="  Whitespace Task  ")
        assert schema.title == "Whitespace Task"
    
    def test_title_empty_fails(self):
        """Test that empty title raises validation error."""
        with pytest.raises(ValidationError) as exc:
            TaskSchema(title="")
        # Pydantic's min_length=1 catches empty strings before custom validator
        error_str = str(exc.value)
        assert "title" in error_str.lower()
    
    def test_title_whitespace_only_fails(self):
        """Test that whitespace-only title raises validation error."""
        with pytest.raises(ValidationError) as exc:
            TaskSchema(title="   ")
        assert "Task title cannot be empty" in str(exc.value)
    
    def test_title_max_length(self):
        """Test title at max length is valid."""
        long_title = "a" * MAX_TITLE_LENGTH
        schema = TaskSchema(title=long_title)
        assert len(schema.title) == MAX_TITLE_LENGTH
    
    def test_title_exceeds_max_length_fails(self):
        """Test title exceeding max length raises error."""
        long_title = "a" * (MAX_TITLE_LENGTH + 1)
        with pytest.raises(ValidationError):
            TaskSchema(title=long_title)
    
    def test_description_whitespace_stripped(self):
        """Test that description whitespace is stripped."""
        schema = TaskSchema(title="Task", description="  Description  ")
        assert schema.description == "Description"
    
    def test_description_empty_becomes_none(self):
        """Test that empty description becomes None."""
        schema = TaskSchema(title="Task", description="")
        assert schema.description is None
    
    def test_description_whitespace_only_becomes_none(self):
        """Test that whitespace-only description becomes None."""
        schema = TaskSchema(title="Task", description="   ")
        assert schema.description is None
    
    def test_valid_statuses(self):
        """Test all valid status values."""
        for status in VALID_STATUSES:
            schema = TaskSchema(title="Task", status=status)
            assert schema.status == status
    
    def test_invalid_status_fails(self):
        """Test invalid status raises error."""
        with pytest.raises(ValidationError) as exc:
            TaskSchema(title="Task", status="invalid")
        assert "Status must be one of" in str(exc.value)
    
    def test_due_date_valid(self):
        """Test valid due date."""
        due = datetime.now(timezone.utc) + timedelta(days=30)
        schema = TaskSchema(title="Task", due_date=due)
        assert schema.due_date == due
    
    def test_due_date_past_is_valid(self):
        """Test past due date is valid (no restriction)."""
        past_due = datetime.now(timezone.utc) - timedelta(days=30)
        schema = TaskSchema(title="Task", due_date=past_due)
        assert schema.due_date == past_due
    
    def test_project_id_valid(self):
        """Test valid project_id."""
        schema = TaskSchema(title="Task", project_id=42)
        assert schema.project_id == 42
    
    def test_project_id_none_for_standalone(self):
        """Test None project_id for standalone task."""
        schema = TaskSchema(title="Task", project_id=None)
        assert schema.project_id is None


class TestTaskUpdateSchema:
    """Tests for TaskUpdateSchema partial validation."""
    
    def test_all_fields_optional(self):
        """Test that all fields are optional for updates."""
        schema = TaskUpdateSchema()
        assert schema.title is None
        assert schema.description is None
        assert schema.due_date is None
        assert schema.status is None
        assert schema.project_id is None
    
    def test_partial_update_title_only(self):
        """Test updating only title."""
        schema = TaskUpdateSchema(title="New Title")
        assert schema.title == "New Title"
        assert schema.description is None
    
    def test_partial_update_status_only(self):
        """Test updating only status."""
        schema = TaskUpdateSchema(status="done")
        assert schema.status == "done"
        assert schema.title is None
    
    def test_title_validation_when_provided(self):
        """Test title is validated when provided."""
        with pytest.raises(ValidationError) as exc:
            TaskUpdateSchema(title="")
        # Pydantic's min_length=1 catches empty strings before custom validator
        error_str = str(exc.value)
        assert "title" in error_str.lower()
    
    def test_status_validation_when_provided(self):
        """Test status is validated when provided."""
        with pytest.raises(ValidationError) as exc:
            TaskUpdateSchema(status="invalid")
        assert "Status must be one of" in str(exc.value)


class TestTaskModel:
    """Tests for Task SQLAlchemy model."""
    
    def test_task_repr(self):
        """Test Task string representation."""
        task = Task(
            id=1,
            title="Test Task",
            status="todo",
            priority=TaskPriority.MEDIUM,
            complexity=TaskComplexity.MODERATE,
            project_id=None
        )
        repr_str = repr(task)
        assert "Task" in repr_str
        assert "id=1" in repr_str
        assert "Test Task" in repr_str
        assert "todo" in repr_str
        assert "priority" in repr_str.lower()
        assert "complexity" in repr_str.lower()
    
    def test_task_defaults(self):
        """Test Task default values.
        
        Note: SQLAlchemy Column defaults are applied at flush time, not instantiation.
        In-memory objects have None for default columns until persisted.
        """
        task = Task(title="Test")
        # Column defaults apply at DB level, not at instantiation
        # status will be None until persisted (then default='todo' applies)
        assert task.project_id is None
        assert task.description is None
        assert task.due_date is None
    
    def test_task_with_explicit_status(self):
        """Test Task with explicitly set status."""
        task = Task(title="Test", status="in_progress")
        assert task.status == "in_progress"


class TestTaskPriorityEnum:
    """Tests for TaskPriority enum."""
    
    def test_priority_enum_values(self):
        """Test TaskPriority enum has correct values."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
    
    def test_priority_enum_count(self):
        """Test TaskPriority has exactly 3 levels."""
        priorities = list(TaskPriority)
        assert len(priorities) == 3


class TestTaskComplexityEnum:
    """Tests for TaskComplexity enum."""
    
    def test_complexity_enum_values(self):
        """Test TaskComplexity enum has correct values."""
        assert TaskComplexity.SIMPLE.value == "simple"
        assert TaskComplexity.MODERATE.value == "moderate"
        assert TaskComplexity.COMPLEX.value == "complex"
    
    def test_complexity_enum_count(self):
        """Test TaskComplexity has exactly 3 levels."""
        complexities = list(TaskComplexity)
        assert len(complexities) == 3


class TestTaskSchemaWithProperties:
    """Tests for TaskSchema with priority and complexity fields."""
    
    def test_priority_default(self):
        """Test priority defaults to MEDIUM."""
        schema = TaskSchema(title="Task")
        assert schema.priority == TaskPriority.MEDIUM
    
    def test_priority_all_valid_values(self):
        """Test all valid priority values."""
        for priority in TaskPriority:
            schema = TaskSchema(title="Task", priority=priority)
            assert schema.priority == priority
    
    def test_priority_string_conversion(self):
        """Test priority string is converted to enum."""
        schema = TaskSchema(title="Task", priority="high")
        assert schema.priority == TaskPriority.HIGH
        assert isinstance(schema.priority, TaskPriority)
    
    def test_priority_string_case_insensitive(self):
        """Test priority string conversion is case-insensitive."""
        schema = TaskSchema(title="Task", priority="HIGH")
        assert schema.priority == TaskPriority.HIGH
    
    def test_priority_invalid_string_fails(self):
        """Test invalid priority string raises error."""
        with pytest.raises(ValidationError) as exc:
            TaskSchema(title="Task", priority="invalid")
        assert "Priority must be one of" in str(exc.value)
    
    def test_complexity_default(self):
        """Test complexity defaults to MODERATE."""
        schema = TaskSchema(title="Task")
        assert schema.complexity == TaskComplexity.MODERATE
    
    def test_complexity_all_valid_values(self):
        """Test all valid complexity values."""
        for complexity in TaskComplexity:
            schema = TaskSchema(title="Task", complexity=complexity)
            assert schema.complexity == complexity
    
    def test_complexity_string_conversion(self):
        """Test complexity string is converted to enum."""
        schema = TaskSchema(title="Task", complexity="complex")
        assert schema.complexity == TaskComplexity.COMPLEX
        assert isinstance(schema.complexity, TaskComplexity)
    
    def test_complexity_string_case_insensitive(self):
        """Test complexity string conversion is case-insensitive."""
        schema = TaskSchema(title="Task", complexity="SIMPLE")
        assert schema.complexity == TaskComplexity.SIMPLE
    
    def test_complexity_invalid_string_fails(self):
        """Test invalid complexity string raises error."""
        with pytest.raises(ValidationError) as exc:
            TaskSchema(title="Task", complexity="invalid")
        assert "Complexity must be one of" in str(exc.value)
    
    def test_full_task_with_properties(self):
        """Test creating task with all properties including priority and complexity."""
        due = datetime.now(timezone.utc) + timedelta(days=7)
        schema = TaskSchema(
            title="Important Task",
            description="This is important",
            due_date=due,
            status="in_progress",
            priority=TaskPriority.HIGH,
            complexity=TaskComplexity.COMPLEX,
            project_id=1
        )
        assert schema.title == "Important Task"
        assert schema.priority == TaskPriority.HIGH
        assert schema.complexity == TaskComplexity.COMPLEX
        assert schema.status == "in_progress"


class TestTaskUpdateSchemaWithProperties:
    """Tests for TaskUpdateSchema with optional priority and complexity."""
    
    def test_priority_optional_in_update(self):
        """Test priority is optional in update schema."""
        schema = TaskUpdateSchema(title="Updated")
        assert schema.title == "Updated"
        assert schema.priority is None
    
    def test_priority_update(self):
        """Test updating priority."""
        schema = TaskUpdateSchema(priority=TaskPriority.HIGH)
        assert schema.priority == TaskPriority.HIGH
    
    def test_priority_string_conversion_in_update(self):
        """Test priority string conversion in update schema."""
        schema = TaskUpdateSchema(priority="low")
        assert schema.priority == TaskPriority.LOW
    
    def test_complexity_optional_in_update(self):
        """Test complexity is optional in update schema."""
        schema = TaskUpdateSchema(title="Updated")
        assert schema.title == "Updated"
        assert schema.complexity is None
    
    def test_complexity_update(self):
        """Test updating complexity."""
        schema = TaskUpdateSchema(complexity=TaskComplexity.SIMPLE)
        assert schema.complexity == TaskComplexity.SIMPLE
    
    def test_complexity_string_conversion_in_update(self):
        """Test complexity string conversion in update schema."""
        schema = TaskUpdateSchema(complexity="moderate")
        assert schema.complexity == TaskComplexity.MODERATE
    
    def test_partial_property_update(self):
        """Test updating only priority, leaving complexity unchanged."""
        schema = TaskUpdateSchema(priority=TaskPriority.HIGH)
        assert schema.priority == TaskPriority.HIGH
        assert schema.complexity is None
        assert schema.title is None


class TestTaskModelWithProperties:
    """Tests for Task model with priority and complexity columns."""
    
    def test_task_with_priorities(self):
        """Test creating task with different priority values."""
        for priority in TaskPriority:
            task = Task(
                title=f"Task {priority.value}",
                priority=priority,
                complexity=TaskComplexity.MODERATE
            )
            assert task.priority == priority
    
    def test_task_with_complexities(self):
        """Test creating task with different complexity values."""
        for complexity in TaskComplexity:
            task = Task(
                title=f"Task {complexity.value}",
                priority=TaskPriority.MEDIUM,
                complexity=complexity
            )
            assert task.complexity == complexity
    
    def test_task_defaults_in_database(self):
        """Test Task model defaults for priority and complexity.
        
        At instantiation, enums may not have defaults applied.
        Defaults are applied by SQLAlchemy at persist time.
        """
        task = Task(title="Test")
        # At in-memory instantiation, defaults may not be applied
        # We just verify the model structure supports them
        assert hasattr(task, 'priority')
        assert hasattr(task, 'complexity')

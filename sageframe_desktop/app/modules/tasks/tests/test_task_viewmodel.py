"""Tests for TaskViewModel (MVVM pattern)."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from PySide6.QtCore import QObject, SignalInstance

from app.modules.tasks.view_models import TaskViewModel
from app.modules.tasks.models import Task


@pytest.fixture
def mock_undo_manager():
    """Mock UndoManager for testing."""
    manager = Mock()
    manager.push = Mock(return_value=None)  # push() doesn't return a value
    return manager


@pytest.fixture
def task_viewmodel(qtbot, mock_undo_manager):
    """Create TaskViewModel instance for testing."""
    viewmodel = TaskViewModel(undo_manager=mock_undo_manager)
    # ViewModel is QObject, not QWidget - no need to add to qtbot
    return viewmodel


@pytest.fixture
def task_viewmodel_no_undo(qtbot):
    """Create TaskViewModel without undo manager."""
    viewmodel = TaskViewModel(undo_manager=None)
    # ViewModel is QObject, not QWidget - no need to add to qtbot
    return viewmodel


class TestTaskViewModelInitialization:
    """Test TaskViewModel initialization."""
    
    def test_initialization_default_values(self, task_viewmodel):
        """Test ViewModel initializes with correct default values."""
        assert task_viewmodel.taskTitle == ""
        assert task_viewmodel.taskDescription == ""
        assert task_viewmodel.taskStatus == "todo"
        assert task_viewmodel.taskProjectId == 0
        assert task_viewmodel.currentTaskId == 0
        assert not task_viewmodel.isSubmitting
    
    def test_has_required_signals(self, task_viewmodel):
        """Test ViewModel has all required signals."""
        assert hasattr(task_viewmodel, 'taskCreated')
        assert hasattr(task_viewmodel, 'taskUpdated')
        assert hasattr(task_viewmodel, 'taskDeleted')
        assert hasattr(task_viewmodel, 'tasksListChanged')
        assert hasattr(task_viewmodel, 'validationError')
        assert hasattr(task_viewmodel, 'operationError')
        
        # Verify they are signals
        assert isinstance(task_viewmodel.taskCreated, SignalInstance)
        assert isinstance(task_viewmodel.taskUpdated, SignalInstance)
        assert isinstance(task_viewmodel.taskDeleted, SignalInstance)


class TestTaskViewModelProperties:
    """Test TaskViewModel properties and setters."""
    
    def test_task_title_property(self, task_viewmodel):
        """Test taskTitle property getter/setter."""
        task_viewmodel.taskTitle = "Test Task"
        assert task_viewmodel.taskTitle == "Test Task"
    
    def test_task_description_property(self, task_viewmodel):
        """Test taskDescription property getter/setter."""
        task_viewmodel.taskDescription = "Test description"
        assert task_viewmodel.taskDescription == "Test description"
    
    def test_task_status_property(self, task_viewmodel):
        """Test taskStatus property getter/setter."""
        task_viewmodel.taskStatus = "in_progress"
        assert task_viewmodel.taskStatus == "in_progress"
    
    def test_task_project_id_property_zero_becomes_none(self, task_viewmodel):
        """Test taskProjectId property converts 0 to None internally."""
        task_viewmodel.taskProjectId = 0
        assert task_viewmodel.taskProjectId == 0  # Getter returns 0
        assert task_viewmodel._task_project_id is None  # Internal is None
    
    def test_task_project_id_property_positive_value(self, task_viewmodel):
        """Test taskProjectId property with positive value."""
        task_viewmodel.taskProjectId = 42
        assert task_viewmodel.taskProjectId == 42
        assert task_viewmodel._task_project_id == 42
    
    def test_current_task_id_property(self, task_viewmodel):
        """Test currentTaskId property."""
        task_viewmodel.currentTaskId = 123
        assert task_viewmodel.currentTaskId == 123


class TestTaskViewModelCreateTask:
    """Test create_task method."""
    
    @patch('app.modules.tasks.services.TaskService')
    def test_create_task_with_undo_manager(self, mock_service_class, task_viewmodel, qtbot):
        """Test creating task with undo manager."""
        # Setup mock service
        mock_service = Mock()
        mock_task = Task(id=1, title="New Task", status="todo", description=None, created_at=datetime.now(), updated_at=datetime.now())
        mock_service.create_task.return_value = mock_task
        mock_service.get_task.return_value = mock_task
        mock_service.list_tasks.return_value = [mock_task]
        task_viewmodel._service = mock_service
        
        # Setup signal spy
        with qtbot.waitSignal(task_viewmodel.taskCreated, timeout=1000) as blocker:
            result = task_viewmodel.create_task(
                title="New Task",
                description="Test description",
                status="todo"
            )
        
        assert result is True
        # Check signal was emitted
        assert blocker.args == [1, "New Task"]
        
        # Check undo manager was called
        task_viewmodel._undo_manager.push.assert_called_once()
    
    @patch('app.modules.tasks.services.TaskService')
    def test_create_task_without_undo_manager(self, mock_service_class, task_viewmodel_no_undo, qtbot):
        """Test creating task without undo manager."""
        # Setup mock service
        mock_service = Mock()
        mock_task = Task(id=2, title="Direct Task", status="todo", description=None, created_at=datetime.now(), updated_at=datetime.now())
        mock_service.create_task.return_value = mock_task
        mock_service.list_tasks.return_value = [mock_task]
        task_viewmodel_no_undo._service = mock_service
        
        # Setup signal spy
        with qtbot.waitSignal(task_viewmodel_no_undo.taskCreated, timeout=1000) as blocker:
            result = task_viewmodel_no_undo.create_task(
                title="Direct Task",
                description=None
            )
        
        assert result is True
        assert blocker.args == [2, "Direct Task"]
        
        # Service should be called directly
        mock_service.create_task.assert_called_once()
    
    def test_create_task_empty_title_fails(self, task_viewmodel, qtbot):
        """Test creating task with empty title emits validation error."""
        with qtbot.waitSignal(task_viewmodel.validationError, timeout=1000) as blocker:
            result = task_viewmodel.create_task(title="")
        
        assert result is False
        assert "cannot be empty" in blocker.args[0].lower()
    
    def test_create_task_whitespace_only_title_fails(self, task_viewmodel, qtbot):
        """Test creating task with whitespace-only title emits validation error."""
        with qtbot.waitSignal(task_viewmodel.validationError, timeout=1000) as blocker:
            result = task_viewmodel.create_task(title="   ")
        
        assert result is False
    
    @patch('app.modules.tasks.services.TaskService')
    def test_create_task_with_project_association(self, mock_service_class, task_viewmodel, qtbot):
        """Test creating task associated with a project."""
        # Setup mock
        mock_service = Mock()
        mock_task = Task(id=3, title="Project Task", status="todo", project_id=10, created_at=datetime.now(), updated_at=datetime.now())
        mock_service.create_task.return_value = mock_task
        mock_service.get_task.return_value = mock_task
        mock_service.list_tasks.return_value = [mock_task]
        task_viewmodel._service = mock_service
        
        with qtbot.waitSignal(task_viewmodel.taskCreated, timeout=1000):
            result = task_viewmodel.create_task(
                title="Project Task",
                project_id=10
            )
        
        assert result is True
    
    @patch('app.modules.tasks.services.TaskService')
    def test_create_task_prevents_double_submission(self, mock_service_class, task_viewmodel):
        """Test that double submission is prevented."""
        task_viewmodel._is_submitting = True
        
        result = task_viewmodel.create_task(title="Task")
        
        assert result is False


class TestTaskViewModelUpdateTask:
    """Test update_task method."""
    
    @patch('app.modules.tasks.services.TaskService')
    def test_update_task_with_undo_manager(self, mock_service_class, task_viewmodel, qtbot):
        """Test updating task with undo manager."""
        # Setup
        mock_service = Mock()
        mock_task = Task(id=5, title="Updated Task", status="in_progress", created_at=datetime.now(), updated_at=datetime.now())
        mock_service.update_task.return_value = mock_task
        mock_service.get_task.return_value = mock_task
        mock_service.list_tasks.return_value = [mock_task]
        task_viewmodel._service = mock_service
        task_viewmodel.currentTaskId = 5
        
        with qtbot.waitSignal(task_viewmodel.taskUpdated, timeout=1000) as blocker:
            result = task_viewmodel.update_task(
                task_id=5,
                title="Updated Task",
                status="in_progress"
            )
        
        assert result is True
        assert blocker.args == [5, "Updated Task"]
        
        # Undo manager should be called
        task_viewmodel._undo_manager.push.assert_called_once()
    
    @patch('app.modules.tasks.services.TaskService')
    def test_update_task_without_undo_manager(self, mock_service_class, task_viewmodel_no_undo, qtbot):
        """Test updating task without undo manager."""
        # Setup
        mock_service = Mock()
        mock_task = Task(id=6, title="Direct Update", status="done", created_at=datetime.now(), updated_at=datetime.now())
        mock_service.update_task.return_value = mock_task
        mock_service.list_tasks.return_value = [mock_task]
        task_viewmodel_no_undo._service = mock_service
        
        with qtbot.waitSignal(task_viewmodel_no_undo.taskUpdated, timeout=1000):
            result = task_viewmodel_no_undo.update_task(
                task_id=6,
                title="Direct Update"
            )
        
        assert result is True
        mock_service.update_task.assert_called_once()
    
    @patch('app.modules.tasks.services.TaskService')
    def test_update_task_not_found(self, mock_service_class, task_viewmodel, qtbot):
        """Test updating non-existent task emits error."""
        # Setup
        mock_service = Mock()
        mock_service.update_task.return_value = None
        mock_service.get_task.return_value = None
        mock_service.list_tasks.return_value = []
        task_viewmodel._service = mock_service
        
        with qtbot.waitSignal(task_viewmodel.validationError, timeout=1000) as blocker:
            result = task_viewmodel.update_task(task_id=999, title="Not Found")
        
        assert result is False
        assert "not found" in blocker.args[0].lower()


class TestTaskViewModelDeleteTask:
    """Test delete_task method."""
    
    @patch('app.modules.tasks.services.TaskService')
    def test_delete_task_with_undo_manager(self, mock_service_class, task_viewmodel, qtbot):
        """Test deleting task with undo manager."""
        # Setup
        mock_service = Mock()
        mock_task = Task(id=7, title="To Delete", status="todo", created_at=datetime.now(), updated_at=datetime.now())
        mock_service.get_task.return_value = mock_task
        mock_service.delete_task.return_value = True
        mock_service.list_tasks.return_value = []
        task_viewmodel._service = mock_service
        
        with qtbot.waitSignal(task_viewmodel.taskDeleted, timeout=1000) as blocker:
            result = task_viewmodel.delete_task(task_id=7)
        
        assert result is True
        assert blocker.args == [7]
        
        # Undo manager should be called
        task_viewmodel._undo_manager.push.assert_called_once()
    
    @patch('app.modules.tasks.services.TaskService')
    def test_delete_task_without_undo_manager(self, mock_service_class, task_viewmodel_no_undo, qtbot):
        """Test deleting task without undo manager."""
        # Setup
        mock_service = Mock()
        mock_service.delete_task.return_value = True
        mock_service.list_tasks.return_value = []
        task_viewmodel_no_undo._service = mock_service
        
        with qtbot.waitSignal(task_viewmodel_no_undo.taskDeleted, timeout=1000):
            result = task_viewmodel_no_undo.delete_task(task_id=8)
        
        assert result is True
        mock_service.delete_task.assert_called_once_with(8)
    
    @patch('app.modules.tasks.services.TaskService')
    def test_delete_task_not_found(self, mock_service_class, task_viewmodel_no_undo, qtbot):
        """Test deleting non-existent task emits error."""
        # Setup
        mock_service = Mock()
        mock_service.delete_task.return_value = False
        mock_service.list_tasks.return_value = []
        task_viewmodel_no_undo._service = mock_service
        
        with qtbot.waitSignal(task_viewmodel_no_undo.validationError, timeout=1000) as blocker:
            result = task_viewmodel_no_undo.delete_task(task_id=999)
        
        assert result is False
        assert "not found" in blocker.args[0].lower()


class TestTaskViewModelListTasks:
    """Test list_tasks and filtering methods."""
    
    @patch('app.modules.tasks.services.TaskService')
    def test_load_all_tasks(self, mock_service_class, task_viewmodel, qtbot):
        """Test loading all tasks."""
        # Setup
        mock_service = Mock()
        mock_tasks = [
            Task(id=1, title="Task 1", status="todo", created_at=datetime.now(), updated_at=datetime.now()),
            Task(id=2, title="Task 2", status="in_progress", created_at=datetime.now(), updated_at=datetime.now()),
        ]
        mock_service.list_tasks.return_value = mock_tasks
        task_viewmodel._service = mock_service
        
        with qtbot.waitSignal(task_viewmodel.tasksListChanged, timeout=1000):
            task_viewmodel.refresh_tasks()
        
        assert len(task_viewmodel._tasks_cache) == 2
        mock_service.list_tasks.assert_called_once()
    
    @patch('app.modules.tasks.services.TaskService')
    def test_filter_tasks_by_project(self, mock_service_class, task_viewmodel, qtbot):
        """Test filtering tasks by project."""
        # Setup
        mock_service = Mock()
        mock_tasks = [Task(id=10, title="Project Task", status="todo", project_id=5, created_at=datetime.now(), updated_at=datetime.now())]
        mock_service.list_tasks.return_value = mock_tasks
        task_viewmodel._service = mock_service
        
        with qtbot.waitSignal(task_viewmodel.tasksListChanged, timeout=1000):
            task_viewmodel.set_filter(project_id=5)
        
        assert task_viewmodel._current_filter_project_id == 5
        mock_service.list_tasks.assert_called_once_with(project_id=5, status=None)
    
    @patch('app.modules.tasks.services.TaskService')
    def test_filter_tasks_by_status(self, mock_service_class, task_viewmodel, qtbot):
        """Test filtering tasks by status."""
        # Setup
        mock_service = Mock()
        mock_tasks = [Task(id=11, title="Done Task", status="done", created_at=datetime.now(), updated_at=datetime.now())]
        mock_service.list_tasks.return_value = mock_tasks
        task_viewmodel._service = mock_service
        
        with qtbot.waitSignal(task_viewmodel.tasksListChanged, timeout=1000):
            task_viewmodel.set_filter(status="done")
        
        assert task_viewmodel._current_filter_status == "done"
        mock_service.list_tasks.assert_called_once_with(project_id=None, status="done")


class TestTaskViewModelLoadTask:
    """Test load_task method."""
    
    @patch('app.modules.tasks.services.TaskService')
    def test_load_task_success(self, mock_service_class, task_viewmodel):
        """Test loading task details by ID."""
        # Setup
        mock_service = Mock()
        mock_task = Task(
            id=20,
            title="Loaded Task",
            description="Description",
            status="in_progress",
            project_id=3,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_service.get_task.return_value = mock_task
        task_viewmodel._service = mock_service
        
        result = task_viewmodel.load_task(task_id=20)
        
        assert result is True
        assert task_viewmodel.currentTaskId == 20
        assert task_viewmodel.taskTitle == "Loaded Task"
        assert task_viewmodel.taskDescription == "Description"
        assert task_viewmodel.taskStatus == "in_progress"
        assert task_viewmodel.taskProjectId == 3
    
    @patch('app.modules.tasks.services.TaskService')
    def test_load_task_not_found(self, mock_service_class, task_viewmodel, qtbot):
        """Test loading non-existent task emits error."""
        # Setup
        mock_service = Mock()
        mock_service.get_task.return_value = None
        task_viewmodel._service = mock_service
        
        with qtbot.waitSignal(task_viewmodel.validationError, timeout=1000) as blocker:
            result = task_viewmodel.load_task(task_id=999)
        
        assert result is False
        assert "not found" in blocker.args[0].lower()


class TestTaskViewModelCleanup:
    """Test resource cleanup."""
    
    @patch('app.modules.tasks.services.TaskService')
    def test_close_event_cleanup(self, mock_service_class, task_viewmodel):
        """Test closeEvent performs cleanup."""
        # Setup
        mock_service = Mock()
        task_viewmodel._service = mock_service
        
        # Call close
        task_viewmodel.close()
        
        # Service should be closed
        mock_service.close.assert_called_once()


class TestTaskViewModelValidation:
    """Test validation methods."""
    
    def test_validate_title_sets_error_when_empty(self, task_viewmodel):
        """Test title validation sets error for empty title."""
        task_viewmodel.taskTitle = ""
        task_viewmodel._validate_title()
        
        assert "title" in task_viewmodel._validation_errors
    
    def test_validate_title_clears_error_when_valid(self, task_viewmodel):
        """Test title validation clears error for valid title."""
        task_viewmodel.taskTitle = "Valid Title"
        task_viewmodel._validate_title()
        
        assert "title" not in task_viewmodel._validation_errors

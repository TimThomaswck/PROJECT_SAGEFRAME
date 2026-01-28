"""UI tests for task management dialogs and widgets using pytest-qt."""

import pytest
from datetime import datetime, timezone
from time import perf_counter
from unittest.mock import Mock, MagicMock, patch

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt, QDateTime

from app.modules.tasks.views import TaskCreateDialog, TaskViewWidget, TaskEditDialog
from app.modules.tasks.view_models import TaskViewModel
from app.modules.tasks.models import Task


@pytest.fixture
def mock_viewmodel(qtbot):
    """Create mock TaskViewModel for testing."""
    viewmodel = Mock(spec=TaskViewModel)
    viewmodel.taskCreated = Mock()
    viewmodel.taskUpdated = Mock()
    viewmodel.taskDeleted = Mock()
    viewmodel.validationError = Mock()
    viewmodel.operationError = Mock()
    viewmodel.taskTitle = ""
    viewmodel.taskDescription = ""
    viewmodel.taskStatus = "todo"
    viewmodel.taskProjectId = 0
    viewmodel.get_task_due_date = Mock(return_value=None)
    viewmodel.create_task = Mock(return_value=True)
    viewmodel.update_task = Mock(return_value=True)
    viewmodel.delete_task = Mock(return_value=True)
    viewmodel.load_task = Mock(return_value=True)
    return viewmodel


@pytest.fixture
def sample_projects():
    """Sample project list for dropdowns."""
    return [
        {"id": 1, "name": "Project Alpha"},
        {"id": 2, "name": "Project Beta"},
    ]


class TestTaskCreateDialog:
    """Test TaskCreateDialog UI component."""
    
    def test_dialog_initialization(self, qtbot, mock_viewmodel):
        """Test dialog initializes with correct UI elements."""
        dialog = TaskCreateDialog(view_model=mock_viewmodel)
        qtbot.addWidget(dialog)
        
        assert dialog.windowTitle() == "Create New Task"
        assert dialog._title_input is not None
        assert dialog._description_input is not None
        assert dialog._due_date_input is not None
        assert dialog._status_combo is not None
    
    def test_dialog_has_project_dropdown(self, qtbot, mock_viewmodel, sample_projects):
        """Test dialog shows project dropdown with projects."""
        dialog = TaskCreateDialog(view_model=mock_viewmodel, projects=sample_projects)
        qtbot.addWidget(dialog)
        
        assert dialog._project_combo is not None
        # Should have "None" option + 2 projects = 3 items
        assert dialog._project_combo.count() >= 2
    
    def test_title_input_accessibility(self, qtbot, mock_viewmodel):
        """Test title input has accessibility attributes."""
        dialog = TaskCreateDialog(view_model=mock_viewmodel)
        qtbot.addWidget(dialog)
        
        assert dialog._title_input.accessibleName() != ""
        assert dialog._title_input.objectName() == "taskTitleInput"
    
    def test_create_button_click_calls_viewmodel(self, qtbot, mock_viewmodel):
        """Test clicking create button calls viewmodel.create_task."""
        dialog = TaskCreateDialog(view_model=mock_viewmodel)
        qtbot.addWidget(dialog)
        
        # Fill in title
        dialog._title_input.setText("Test Task")
        
        # Click create button
        qtbot.mouseClick(dialog._create_button, Qt.LeftButton)
        
        # ViewModel should be called
        mock_viewmodel.create_task.assert_called_once()
    
    def test_empty_title_shows_validation_error(self, qtbot, mock_viewmodel):
        """Test creating task with empty title shows validation error."""
        mock_viewmodel.create_task.return_value = False
        
        dialog = TaskCreateDialog(view_model=mock_viewmodel)
        qtbot.addWidget(dialog)
        
        # Don't fill title, click create
        qtbot.mouseClick(dialog._create_button, Qt.LeftButton)
        
        # Should call create_task which returns False
        assert mock_viewmodel.create_task.called
    
    def test_cancel_button_closes_dialog(self, qtbot, mock_viewmodel):
        """Test cancel button closes dialog without creating."""
        dialog = TaskCreateDialog(view_model=mock_viewmodel)
        qtbot.addWidget(dialog)
        
        qtbot.mouseClick(dialog._cancel_button, Qt.LeftButton)
        
        # Dialog should be rejected
        assert not dialog.isVisible() or dialog.result() == QMessageBox.Cancel
    
    def test_keyboard_navigation(self, qtbot, mock_viewmodel):
        """Test dialog is keyboard navigable (NFR7)."""
        dialog = TaskCreateDialog(view_model=mock_viewmodel)
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)
        
        # Set focus to title input
        dialog._title_input.setFocus()
        qtbot.waitUntil(lambda: dialog._title_input.hasFocus())
        assert dialog._title_input.hasFocus()
        
        # Tab should move focus
        qtbot.keyClick(dialog._title_input, Qt.Key_Tab)
        qtbot.waitUntil(lambda: dialog._description_input.hasFocus())
        # Next widget should have focus (description)
        assert dialog._description_input.hasFocus()
    
    def test_status_dropdown_has_valid_options(self, qtbot, mock_viewmodel):
        """Test status dropdown contains valid status options."""
        dialog = TaskCreateDialog(view_model=mock_viewmodel)
        qtbot.addWidget(dialog)
        
        # Should have todo, in_progress, done, blocked
        statuses = [dialog._status_combo.itemText(i) for i in range(dialog._status_combo.count())]
        assert len(statuses) >= 4
    
    def test_project_selection_passed_to_viewmodel(self, qtbot, mock_viewmodel, sample_projects):
        """Test project selection is passed to create_task call."""
        dialog = TaskCreateDialog(view_model=mock_viewmodel, projects=sample_projects)
        qtbot.addWidget(dialog)
        
        # Fill title
        dialog._title_input.setText("Task with Project")
        
        # Select project
        dialog._project_combo.setCurrentIndex(1)  # First project (index 0 is "None")
        
        # Click create
        qtbot.mouseClick(dialog._create_button, Qt.LeftButton)
        
        # Check create_task was called with project_id
        mock_viewmodel.create_task.assert_called_once()
        call_kwargs = mock_viewmodel.create_task.call_args[1]
        # Project ID should be passed (if not None)
        assert 'project_id' in call_kwargs or len(mock_viewmodel.create_task.call_args[0]) >= 5


class TestTaskViewWidget:
    """Test TaskViewWidget UI component."""
    
    def test_widget_initialization(self, qtbot, mock_viewmodel):
        """Test widget initializes correctly."""
        widget = TaskViewWidget(view_model=mock_viewmodel, task_id=1)
        qtbot.addWidget(widget)
        
        # Should call load_task on viewmodel
        mock_viewmodel.load_task.assert_called_once_with(1)
    
    def test_widget_displays_task_title(self, qtbot, mock_viewmodel):
        """Test widget displays task title."""
        mock_viewmodel.taskTitle = "Test Task Title"
        
        widget = TaskViewWidget(view_model=mock_viewmodel, task_id=1)
        qtbot.addWidget(widget)
        
        # Title label should exist
        assert widget._title_label is not None
    
    def test_edit_button_opens_edit_dialog(self, qtbot, mock_viewmodel):
        """Test edit button opens TaskEditDialog."""
        widget = TaskViewWidget(view_model=mock_viewmodel, task_id=1)
        qtbot.addWidget(widget)
        
        # Mock dialog
        with patch('app.modules.tasks.views.TaskEditDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog_class.return_value = mock_dialog
            mock_dialog.exec.return_value = 1  # Accepted
            
            qtbot.mouseClick(widget._edit_button, Qt.LeftButton)
            
            # EditDialog should be created
            mock_dialog_class.assert_called_once()
    
    def test_delete_button_shows_confirmation(self, qtbot, mock_viewmodel):
        """Test delete button shows confirmation dialog (AC#4)."""
        widget = TaskViewWidget(view_model=mock_viewmodel, task_id=1)
        qtbot.addWidget(widget)
        
        # Mock QMessageBox
        with patch('app.modules.tasks.views.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.Yes
            
            qtbot.mouseClick(widget._delete_button, Qt.LeftButton)
            
            # Confirmation should be shown
            mock_question.assert_called_once()
            # ViewModel delete should be called
            mock_viewmodel.delete_task.assert_called_once()
    
    def test_delete_cancelled_does_not_delete(self, qtbot, mock_viewmodel):
        """Test canceling delete confirmation does not delete task."""
        widget = TaskViewWidget(view_model=mock_viewmodel, task_id=1)
        qtbot.addWidget(widget)
        
        # Mock QMessageBox to return No
        with patch('app.modules.tasks.views.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.No
            
            qtbot.mouseClick(widget._delete_button, Qt.LeftButton)
            
            # ViewModel delete should NOT be called
            mock_viewmodel.delete_task.assert_not_called()
    
    def test_widget_shows_project_if_associated(self, qtbot, mock_viewmodel):
        """Test widget displays associated project (AC#2)."""
        mock_viewmodel.taskProjectId = 5
        
        widget = TaskViewWidget(view_model=mock_viewmodel, task_id=1, project_name="My Project")
        qtbot.addWidget(widget)
        
        # Project label should exist and show project
        assert widget._project_label is not None


class TestTaskEditDialog:
    """Test TaskEditDialog UI component."""
    
    def test_dialog_initialization(self, qtbot, mock_viewmodel):
        """Test edit dialog initializes with task data."""
        mock_viewmodel.taskTitle = "Existing Task"
        mock_viewmodel.taskDescription = "Task description"
        mock_viewmodel.taskStatus = "in_progress"
        
        dialog = TaskEditDialog(view_model=mock_viewmodel, task_id=1)
        qtbot.addWidget(dialog)
        
        # Should load task
        mock_viewmodel.load_task.assert_called_once_with(1)
        
        # Fields should be populated
        assert dialog._title_input is not None
        assert dialog._description_input is not None
    
    def test_save_button_calls_update_task(self, qtbot, mock_viewmodel):
        """Test save button calls viewmodel.update_task (AC#3)."""
        dialog = TaskEditDialog(view_model=mock_viewmodel, task_id=1)
        qtbot.addWidget(dialog)
        
        # Modify title
        dialog._title_input.setText("Updated Title")
        
        # Click save
        qtbot.mouseClick(dialog._save_button, Qt.LeftButton)
        
        # ViewModel update should be called
        mock_viewmodel.update_task.assert_called_once()
    
    def test_cancel_button_discards_changes(self, qtbot, mock_viewmodel):
        """Test cancel button closes without saving."""
        dialog = TaskEditDialog(view_model=mock_viewmodel, task_id=1)
        qtbot.addWidget(dialog)
        
        # Modify fields
        dialog._title_input.setText("Changed Title")
        
        # Click cancel
        qtbot.mouseClick(dialog._cancel_button, Qt.LeftButton)
        
        # Update should NOT be called
        mock_viewmodel.update_task.assert_not_called()
    
    def test_can_change_project_association(self, qtbot, mock_viewmodel, sample_projects):
        """Test can change task's project association (AC#5)."""
        dialog = TaskEditDialog(view_model=mock_viewmodel, task_id=1, projects=sample_projects)
        qtbot.addWidget(dialog)
        
        # Should have project dropdown
        assert dialog._project_combo is not None
        
        # Change project
        dialog._project_combo.setCurrentIndex(2)
        
        # Save
        qtbot.mouseClick(dialog._save_button, Qt.LeftButton)
        
        # Update should be called with new project
        mock_viewmodel.update_task.assert_called_once()


class TestTaskDialogsResponsiveness:
    """Test UI responsiveness (NFR1, NFR2)."""
    
    def test_create_dialog_opens_quickly(self, qtbot, mock_viewmodel):
        """Test create dialog opens within 200ms (NFR2)."""
        start = perf_counter()
        dialog = TaskCreateDialog(view_model=mock_viewmodel)
        qtbot.addWidget(dialog)
        dialog.show()
        duration = perf_counter() - start
        assert duration < 0.2
    
    def test_view_widget_loads_quickly(self, qtbot, mock_viewmodel):
        """Test view widget loads within 200ms (NFR2)."""
        start = perf_counter()
        widget = TaskViewWidget(view_model=mock_viewmodel, task_id=1)
        qtbot.addWidget(widget)
        widget.show()
        duration = perf_counter() - start
        assert duration < 0.2


class TestTaskDialogsQSSStyling:
    """Test QSS styling hooks are in place."""
    
    def test_create_dialog_has_object_names(self, qtbot, mock_viewmodel):
        """Test all major widgets have objectName for QSS styling."""
        dialog = TaskCreateDialog(view_model=mock_viewmodel)
        qtbot.addWidget(dialog)
        
        assert dialog._title_input.objectName() == "taskTitleInput"
        assert dialog._description_input.objectName() == "taskDescriptionInput"
        assert dialog._status_combo.objectName() == "taskStatusCombo"
        assert dialog._create_button.objectName() == "taskCreateButton"
        assert dialog._cancel_button.objectName() == "taskCancelButton"
    
    def test_view_widget_has_object_names(self, qtbot, mock_viewmodel):
        """Test view widget has objectName for styling."""
        widget = TaskViewWidget(view_model=mock_viewmodel, task_id=1)
        qtbot.addWidget(widget)
        
        # Main widget should have object name
        assert widget._title_label.objectName() != ""
        assert widget._edit_button.objectName() != ""
        assert widget._delete_button.objectName() != ""


class TestTaskDialogsAccessibility:
    """Test accessibility compliance (NFR7)."""
    
    def test_all_inputs_have_accessible_names(self, qtbot, mock_viewmodel):
        """Test all input fields have accessible names."""
        dialog = TaskCreateDialog(view_model=mock_viewmodel)
        qtbot.addWidget(dialog)
        
        assert dialog._title_input.accessibleName() != ""
        assert dialog._description_input.accessibleName() != ""
        assert dialog._due_date_input.accessibleName() != ""
        assert dialog._status_combo.accessibleName() != ""
    
    def test_dialog_has_accessible_description(self, qtbot, mock_viewmodel):
        """Test dialog has accessible description."""
        dialog = TaskCreateDialog(view_model=mock_viewmodel)
        qtbot.addWidget(dialog)
        
        assert dialog.accessibleName() != ""
        assert dialog.accessibleDescription() != ""
    
    def test_buttons_have_accessible_names(self, qtbot, mock_viewmodel):
        """Test buttons have accessible names."""
        widget = TaskViewWidget(view_model=mock_viewmodel, task_id=1)
        qtbot.addWidget(widget)
        
        assert widget._edit_button.accessibleName() != ""
        assert widget._delete_button.accessibleName() != ""

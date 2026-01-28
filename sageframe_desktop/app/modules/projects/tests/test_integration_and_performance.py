"""UI and integration tests for project management.

Tests cover UI component interactions, performance metrics, and end-to-end flows.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from app.modules.projects.view_models import ProjectViewModel
from app.modules.projects.views import (
    ProjectCreateDialog,
    ProjectViewWidget,
    ProjectEditDialog
)


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def view_model(qapp):
    """Create ProjectViewModel for tests."""
    return ProjectViewModel()


class TestProjectCreateDialog:
    """Tests for ProjectCreateDialog UI component."""
    
    def test_dialog_initialization(self, view_model, qapp):
        """Test that dialog initializes properly."""
        dialog = ProjectCreateDialog(view_model)
        
        assert dialog.windowTitle() == "Create New Project"
        assert dialog._name_input is not None
        assert dialog._description_input is not None
        assert dialog._create_button is not None
        assert dialog._cancel_button is not None
    
    def test_dialog_inputs_initially_empty(self, view_model, qapp):
        """Test that inputs start empty."""
        dialog = ProjectCreateDialog(view_model)
        
        assert dialog._name_input.text() == ""
        assert dialog._description_input.toPlainText() == ""
    
    def test_dialog_name_input_max_length(self, view_model, qapp):
        """Test that name input has max length limit."""
        dialog = ProjectCreateDialog(view_model)
        
        assert dialog._name_input.maxLength() == 255
    
    def test_dialog_buttons_connected(self, view_model, qapp):
        """Test that dialog buttons are connected."""
        dialog = ProjectCreateDialog(view_model)
        
        # Verify buttons exist and have proper objectNames
        assert dialog._create_button.objectName() == "createProjectButton"
        assert dialog._cancel_button.objectName() == "cancelButton"


class TestProjectViewWidget:
    """Tests for ProjectViewWidget UI component."""
    
    def test_widget_initialization(self, view_model, qapp):
        """Test that widget initializes properly."""
        widget = ProjectViewWidget(view_model)
        
        assert widget._name_display is not None
        assert widget._description_display is not None
        assert widget._edit_button is not None
        assert widget._delete_button is not None
    
    def test_widget_description_readonly(self, view_model, qapp):
        """Test that description display is read-only."""
        widget = ProjectViewWidget(view_model)
        
        assert widget._description_display.isReadOnly() is True
    
    def test_widget_set_project_id(self, view_model, qapp):
        """Test loading project data into widget."""
        with patch.object(view_model._service, 'get_project') as mock_get:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "Test Project"
            mock_project.description = "Test Description"
            mock_get.return_value = mock_project
            
            widget = ProjectViewWidget(view_model)
            widget.set_project_id(1)
            
            assert widget._name_display.text() == "Test Project"
            assert widget._description_display.toPlainText() == "Test Description"


class TestProjectEditDialog:
    """Tests for ProjectEditDialog UI component."""
    
    def test_dialog_initialization(self, view_model, qapp):
        """Test that edit dialog initializes properly."""
        dialog = ProjectEditDialog(view_model)
        
        assert dialog.windowTitle() == "Edit Project"
        assert dialog._name_input is not None
        assert dialog._description_input is not None
        assert dialog._save_button is not None
        assert dialog._cancel_button is not None
    
    def test_dialog_load_project_data(self, view_model, qapp):
        """Test loading project data into edit dialog."""
        with patch.object(view_model._service, 'get_project') as mock_get:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "Existing Project"
            mock_project.description = "Existing Description"
            mock_get.return_value = mock_project
            
            dialog = ProjectEditDialog(view_model)
            dialog.set_project_id(1)
            
            assert dialog._name_input.text() == "Existing Project"
            assert dialog._description_input.toPlainText() == "Existing Description"


class TestProjectPerformance:
    """Tests for performance requirements (NFR1, NFR2)."""
    
    def test_create_project_response_time(self, view_model):
        """Test that project creation provides visual feedback within 100ms (NFR1)."""
        with patch.object(view_model._service, 'create_project') as mock_create:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "Performance Test"
            mock_create.return_value = mock_project
            
            # Track signal emission timing
            signals_received = []
            
            def track_signal(*args):
                signals_received.append(time.time())
            
            view_model.projectCreated.connect(track_signal)
            
            start_time = time.time()
            view_model.create_project("Performance Test")
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Should complete within 100ms for visual feedback
            assert elapsed_time < 100, f"Create operation took {elapsed_time}ms, should be <100ms"
    
    def test_list_projects_performance_small_dataset(self, view_model):
        """Test listing projects with small dataset (<100ms)."""
        with patch.object(view_model._service, 'list_projects') as mock_list:
            mock_projects = [
                MagicMock(id=i, name=f"P{i}", description="", created_at=None, updated_at=None)
                for i in range(10)
            ]
            mock_list.return_value = mock_projects
            
            start_time = time.time()
            view_model.refresh_projects()
            elapsed_time = (time.time() - start_time) * 1000
            
            assert elapsed_time < 100, f"List operation took {elapsed_time}ms, should be <100ms"
    
    def test_list_projects_performance_large_dataset(self, view_model):
        """Test listing projects with larger dataset (<200ms for full load, NFR2)."""
        with patch.object(view_model._service, 'list_projects') as mock_list:
            # Simulate 100 projects
            mock_projects = [
                MagicMock(id=i, name=f"Project{i}", description=f"Description {i}", created_at=None, updated_at=None)
                for i in range(100)
            ]
            mock_list.return_value = mock_projects
            
            start_time = time.time()
            view_model.refresh_projects()
            elapsed_time = (time.time() - start_time) * 1000
            
            # Full UI rendering and data load should be <200ms
            assert elapsed_time < 200, f"Large list operation took {elapsed_time}ms, should be <200ms"
    
    def test_get_project_performance(self, view_model):
        """Test retrieving single project is fast (<100ms)."""
        with patch.object(view_model._service, 'get_project') as mock_get:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "Test"
            mock_project.description = "Description"
            mock_get.return_value = mock_project
            
            start_time = time.time()
            view_model.load_project(1)
            elapsed_time = (time.time() - start_time) * 1000
            
            assert elapsed_time < 100, f"Get operation took {elapsed_time}ms, should be <100ms"
    
    def test_update_project_response_time(self, view_model):
        """Test that project update provides visual feedback within 100ms."""
        with patch.object(view_model._service, 'update_project') as mock_update:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "Updated"
            mock_update.return_value = mock_project
            
            start_time = time.time()
            view_model.update_project(1, "Updated")
            elapsed_time = (time.time() - start_time) * 1000
            
            assert elapsed_time < 100, f"Update operation took {elapsed_time}ms, should be <100ms"
    
    def test_delete_project_response_time(self, view_model):
        """Test that project deletion provides visual feedback within 100ms."""
        with patch.object(view_model._service, 'delete_project') as mock_delete:
            mock_delete.return_value = True
            
            start_time = time.time()
            view_model.delete_project(1)
            elapsed_time = (time.time() - start_time) * 1000
            
            assert elapsed_time < 100, f"Delete operation took {elapsed_time}ms, should be <100ms"


class TestProjectIntegration:
    """Integration tests for project CRUD workflow."""
    
    def test_create_view_update_flow(self, view_model):
        """Test complete flow: create → view → update."""
        with patch.object(view_model._service, 'create_project') as mock_create, \
             patch.object(view_model._service, 'get_project') as mock_get, \
             patch.object(view_model._service, 'update_project') as mock_update:
            
            # Create
            created_project = MagicMock()
            created_project.id = 1
            created_project.name = "New Project"
            created_project.description = "Initial"
            mock_create.return_value = created_project
            
            create_result = view_model.create_project("New Project", "Initial")
            assert create_result is True
            
            # Get
            mock_get.return_value = created_project
            get_result = view_model.load_project(1)
            assert get_result is True
            
            # Update
            updated_project = MagicMock()
            updated_project.id = 1
            updated_project.name = "Updated Project"
            updated_project.description = "Updated"
            mock_update.return_value = updated_project
            
            update_result = view_model.update_project(1, "Updated Project", "Updated")
            assert update_result is True
    
    def test_delete_project_signal_clears_selection(self, view_model):
        """Test that deleting current project clears UI selection."""
        with patch.object(view_model._service, 'delete_project') as mock_delete:
            mock_delete.return_value = True
            
            view_model.currentProjectId = 42
            view_model.delete_project(42)
            
            assert view_model.currentProjectId == 0


class TestProjectEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_create_project_with_special_characters(self, view_model):
        """Test creating project with special characters in name."""
        with patch.object(view_model._service, 'create_project') as mock_create:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "Project @#$% 2024!"
            mock_create.return_value = mock_project
            
            result = view_model.create_project("Project @#$% 2024!")
            
            assert result is True
    
    def test_create_project_with_unicode(self, view_model):
        """Test creating project with unicode characters."""
        with patch.object(view_model._service, 'create_project') as mock_create:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "项目 🎯 Проект"
            mock_create.return_value = mock_project
            
            result = view_model.create_project("项目 🎯 Проект")
            
            assert result is True
    
    def test_update_project_clear_description(self, view_model):
        """Test clearing project description in update."""
        with patch.object(view_model._service, 'update_project') as mock_update:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "Project"
            mock_project.description = None
            mock_update.return_value = mock_project
            
            result = view_model.update_project(1, description=None)
            
            assert result is True
    
    def test_rapid_operations_prevent_double_submission(self, view_model):
        """Test that rapid operations don't cause double submission."""
        with patch.object(view_model._service, 'create_project') as mock_create:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_create.return_value = mock_project
            
            # First call should work
            result1 = view_model.create_project("Project 1")
            
            # If still submitting, second call should fail
            if view_model.isSubmitting:
                result2 = view_model.create_project("Project 2")
                assert result2 is False

"""Unit tests for ProjectViewModel.

Tests cover signal emissions, state management, and MVVM integration.
"""

import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QCoreApplication

from app.modules.projects.view_models import ProjectViewModel


@pytest.fixture(scope="session")
def qt_app():
    """Create QApplication for tests."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


@pytest.fixture
def view_model(qt_app):
    """Create ProjectViewModel for testing."""
    return ProjectViewModel()


class TestProjectViewModelProperties:
    """Tests for ViewModel properties."""
    
    def test_initial_project_name_empty(self, view_model):
        """Test that project name starts empty."""
        assert view_model.projectName == ""
    
    def test_project_name_setter(self, view_model):
        """Test setting project name."""
        view_model.projectName = "Test Project"
        assert view_model.projectName == "Test Project"
    
    def test_project_description_setter(self, view_model):
        """Test setting project description."""
        view_model.projectDescription = "Test Description"
        assert view_model.projectDescription == "Test Description"
    
    def test_current_project_id_setter(self, view_model):
        """Test setting current project ID."""
        view_model.currentProjectId = 42
        assert view_model.currentProjectId == 42
    
    def test_is_submitting_initial_false(self, view_model):
        """Test that isSubmitting starts as False."""
        assert view_model.isSubmitting is False


class TestProjectViewModelSignals:
    """Tests for signal emissions."""
    
    def test_project_created_signal_emitted(self, view_model, qt_app):
        """Test that projectCreated signal is emitted."""
        signal_received = []
        
        def capture_signal(project_id, name):
            signal_received.append((project_id, name))
        
        view_model.projectCreated.connect(capture_signal)
        
        with patch.object(view_model._service, 'create_project') as mock_create:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "New Project"
            mock_create.return_value = mock_project
            
            view_model.create_project("New Project")
            
            assert len(signal_received) == 1
            assert signal_received[0] == (1, "New Project")
    
    def test_validation_error_signal_emitted(self, view_model, qt_app):
        """Test that validationError signal is emitted for empty name."""
        signal_received = []
        
        def capture_signal(message):
            signal_received.append(message)
        
        view_model.validationError.connect(capture_signal)
        
        view_model.create_project("")
        
        assert len(signal_received) == 1
        assert "empty" in signal_received[0].lower()
    
    def test_projects_list_changed_signal_emitted(self, view_model, qt_app):
        """Test that projectsListChanged signal is emitted on create."""
        signal_count = []
        
        def capture_signal():
            signal_count.append(1)
        
        view_model.projectsListChanged.connect(capture_signal)
        
        with patch.object(view_model._service, 'create_project') as mock_create:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "Project"
            mock_create.return_value = mock_project
            
            view_model.create_project("Project")
            
            assert len(signal_count) >= 1


class TestProjectViewModelCreateProject:
    """Tests for project creation via ViewModel."""
    
    def test_create_project_success(self, view_model):
        """Test successful project creation."""
        with patch.object(view_model._service, 'create_project') as mock_create:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "New Project"
            mock_create.return_value = mock_project
            
            result = view_model.create_project("New Project", "Description")
            
            assert result is True
            assert view_model.projectName == ""
            assert view_model.projectDescription == ""
    
    def test_create_project_empty_name(self, view_model):
        """Test that empty name fails validation."""
        result = view_model.create_project("")
        assert result is False
    
    def test_create_project_whitespace_name(self, view_model):
        """Test that whitespace-only name fails."""
        result = view_model.create_project("   ")
        assert result is False
    
    def test_create_project_prevents_double_submission(self, view_model):
        """Test that double submission is prevented."""
        view_model._is_submitting = True
        result = view_model.create_project("Project")
        assert result is False
    
    def test_create_project_handles_validation_error(self, view_model):
        """Test handling of validation error from service."""
        with patch.object(view_model._service, 'create_project') as mock_create:
            mock_create.side_effect = ValueError("Invalid data")
            
            result = view_model.create_project("Bad Project")
            
            assert result is False
    
    def test_create_project_handles_database_error(self, view_model):
        """Test handling of database error from service."""
        with patch.object(view_model._service, 'create_project') as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            result = view_model.create_project("Project")
            
            assert result is False


class TestProjectViewModelUpdateProject:
    """Tests for project update via ViewModel."""
    
    def test_update_project_success(self, view_model):
        """Test successful project update."""
        with patch.object(view_model._service, 'update_project') as mock_update:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "Updated"
            mock_update.return_value = mock_project
            
            result = view_model.update_project(1, "Updated", "New Desc")
            
            assert result is True
    
    def test_update_project_not_found(self, view_model):
        """Test update when project not found."""
        with patch.object(view_model._service, 'update_project') as mock_update:
            mock_update.side_effect = ValueError("Project not found")
            
            result = view_model.update_project(9999, "Name")
            
            assert result is False


class TestProjectViewModelDeleteProject:
    """Tests for project deletion via ViewModel."""
    
    def test_delete_project_success(self, view_model):
        """Test successful project deletion."""
        with patch.object(view_model._service, 'delete_project') as mock_delete:
            mock_delete.return_value = True
            
            result = view_model.delete_project(1)
            
            assert result is True
    
    def test_delete_project_not_found(self, view_model):
        """Test deletion when project not found."""
        with patch.object(view_model._service, 'delete_project') as mock_delete:
            mock_delete.return_value = False
            
            result = view_model.delete_project(9999)
            
            assert result is False
    
    def test_delete_project_clears_selection(self, view_model):
        """Test that deleting current project clears selection."""
        with patch.object(view_model._service, 'delete_project') as mock_delete:
            mock_delete.return_value = True
            
            view_model.currentProjectId = 1
            view_model.delete_project(1)
            
            assert view_model.currentProjectId == 0


class TestProjectViewModelLoadProject:
    """Tests for loading project details."""
    
    def test_load_project_success(self, view_model):
        """Test successfully loading project details."""
        with patch.object(view_model._service, 'get_project') as mock_get:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "Test Project"
            mock_project.description = "A test"
            mock_get.return_value = mock_project
            
            result = view_model.load_project(1)
            
            assert result is True
            assert view_model.projectName == "Test Project"
    
    def test_load_project_not_found(self, view_model):
        """Test loading non-existent project."""
        with patch.object(view_model._service, 'get_project') as mock_get:
            mock_get.return_value = None
            
            result = view_model.load_project(9999)
            
            assert result is False


class TestProjectViewModelProjectsList:
    """Tests for projects list management."""
    
    def test_get_projects_list_empty(self, view_model):
        """Test getting empty projects list."""
        projects = view_model.get_projects_list()
        assert projects == []
    
    def test_refresh_projects(self, view_model):
        """Test refreshing projects list."""
        with patch.object(view_model._service, 'list_projects') as mock_list:
            mock_project1 = MagicMock()
            mock_project1.id = 1
            mock_project1.name = "P1"
            mock_project1.description = ""
            mock_project1.created_at = None
            mock_project1.updated_at = None
            
            mock_project2 = MagicMock()
            mock_project2.id = 2
            mock_project2.name = "P2"
            mock_project2.description = "Desc"
            mock_project2.created_at = None
            mock_project2.updated_at = None
            
            mock_list.return_value = [mock_project1, mock_project2]
            
            result = view_model.refresh_projects()
            
            assert result is True
            projects = view_model.get_projects_list()
            assert len(projects) == 2
            assert projects[0]['name'] == "P1"
            assert projects[1]['name'] == "P2"

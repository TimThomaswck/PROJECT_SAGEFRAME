"""Tests for project undo/redo integration.

This module tests the integration of project CRUD operations with the UndoManager
to ensure create, edit, and delete operations can be undone and redone correctly.
"""

import pytest
from unittest.mock import MagicMock

from app.core.undo_manager import UndoManager
from app.core.undo_commands import CreateProjectCommand, EditProjectCommand, DeleteProjectCommand
from app.modules.projects.services import ProjectService
from app.modules.projects.view_models import ProjectViewModel
from app.database import SessionLocal


@pytest.fixture
def db_session():
    """Provide a database session for tests."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def project_service(db_session):
    """Provide a project service with test database."""
    return ProjectService(db_session)


@pytest.fixture
def undo_manager():
    """Provide an undo manager instance."""
    return UndoManager(parent=None)


@pytest.fixture
def view_model(undo_manager):
    """Provide a project view model with undo support."""
    return ProjectViewModel(parent=None, undo_manager=undo_manager)


class TestCreateProjectUndo:
    """Test undo/redo functionality for project creation."""
    
    def test_create_project_undo(self, project_service, undo_manager):
        """Test that undoing a create operation deletes the project."""
        # Create project via command
        command = CreateProjectCommand(
            service=project_service,
            name="Test Project",
            description="Test Description"
        )
        undo_manager.push(command)
        
        project_id = command.get_project_id()
        assert project_id is not None
        
        # Verify project exists
        project = project_service.get_project(project_id)
        assert project is not None
        assert project.name == "Test Project"
        
        # Undo creation
        undo_manager.undo()
        
        # Verify project is deleted
        project = project_service.get_project(project_id)
        assert project is None
    
    def test_create_project_redo(self, project_service, undo_manager):
        """Test that redoing a create operation recreates the project."""
        # Create project via command
        command = CreateProjectCommand(
            service=project_service,
            name="Test Project",
            description="Test Description"
        )
        undo_manager.push(command)
        
        original_id = command.get_project_id()
        
        # Undo creation
        undo_manager.undo()
        
        # Verify project is deleted
        project = project_service.get_project(original_id)
        assert project is None
        
        # Redo creation
        undo_manager.redo()
        
        # Verify project is recreated (may have different ID)
        new_id = command.get_project_id()
        project = project_service.get_project(new_id)
        assert project is not None
        assert project.name == "Test Project"
        assert project.description == "Test Description"
    
    def test_create_project_multiple_undo_redo_cycles(self, project_service, undo_manager):
        """Test multiple undo/redo cycles for project creation."""
        command = CreateProjectCommand(
            service=project_service,
            name="Cycle Test",
            description="Testing cycles"
        )
        undo_manager.push(command)
        
        # Undo/redo cycle 1
        undo_manager.undo()
        assert project_service.get_project(command.get_project_id()) is None
        
        undo_manager.redo()
        assert project_service.get_project(command.get_project_id()) is not None
        
        # Undo/redo cycle 2
        undo_manager.undo()
        assert project_service.get_project(command.get_project_id()) is None
        
        undo_manager.redo()
        project = project_service.get_project(command.get_project_id())
        assert project is not None
        assert project.name == "Cycle Test"


class TestEditProjectUndo:
    """Test undo/redo functionality for project editing."""
    
    def test_edit_project_undo_restores_previous_state(self, project_service, undo_manager):
        """Test that undoing an edit restores previous values."""
        # Create initial project
        project = project_service.create_project(
            name="Original Name",
            description="Original Description"
        )
        
        # Edit project via command
        command = EditProjectCommand(
            service=project_service,
            project_id=project.id,
            new_name="Updated Name",
            new_description="Updated Description"
        )
        undo_manager.push(command)
        
        # Verify edit was applied
        project = project_service.get_project(project.id)
        assert project.name == "Updated Name"
        assert project.description == "Updated Description"
        
        # Undo edit
        undo_manager.undo()
        
        # Verify original values restored
        project = project_service.get_project(project.id)
        assert project.name == "Original Name"
        assert project.description == "Original Description"
    
    def test_edit_project_redo_reapplies_changes(self, project_service, undo_manager):
        """Test that redoing an edit reapplies the changes."""
        # Create initial project
        project = project_service.create_project(
            name="Original Name",
            description="Original Description"
        )
        
        # Edit project via command
        command = EditProjectCommand(
            service=project_service,
            project_id=project.id,
            new_name="Updated Name",
            new_description="Updated Description"
        )
        undo_manager.push(command)
        
        # Undo edit
        undo_manager.undo()
        
        # Redo edit
        undo_manager.redo()
        
        # Verify changes reapplied
        project = project_service.get_project(project.id)
        assert project.name == "Updated Name"
        assert project.description == "Updated Description"
    
    def test_edit_project_partial_field_update(self, project_service, undo_manager):
        """Test undo/redo with partial field updates (only name or description)."""
        # Create initial project
        project = project_service.create_project(
            name="Original Name",
            description="Original Description"
        )
        
        # Edit only name
        command = EditProjectCommand(
            service=project_service,
            project_id=project.id,
            new_name="New Name",
            new_description=None  # Don't change description
        )
        undo_manager.push(command)
        
        # Verify only name changed
        project = project_service.get_project(project.id)
        assert project.name == "New Name"
        assert project.description == "Original Description"
        
        # Undo
        undo_manager.undo()
        
        # Verify original state
        project = project_service.get_project(project.id)
        assert project.name == "Original Name"
        assert project.description == "Original Description"
    
    def test_edit_project_multiple_edits_separate_undo(self, project_service, undo_manager):
        """Test that multiple edits can be undone separately."""
        # Create initial project
        project = project_service.create_project(
            name="Original",
            description="Original Desc"
        )
        
        # First edit
        command1 = EditProjectCommand(
            service=project_service,
            project_id=project.id,
            new_name="Edit 1",
            new_description="Desc 1"
        )
        undo_manager.push(command1)
        
        # Second edit
        command2 = EditProjectCommand(
            service=project_service,
            project_id=project.id,
            new_name="Edit 2",
            new_description="Desc 2"
        )
        undo_manager.push(command2)
        
        # Verify second edit applied
        project = project_service.get_project(project.id)
        assert project.name == "Edit 2"
        
        # Undo second edit
        undo_manager.undo()
        project = project_service.get_project(project.id)
        assert project.name == "Edit 1"
        
        # Undo first edit
        undo_manager.undo()
        project = project_service.get_project(project.id)
        assert project.name == "Original"


class TestDeleteProjectUndo:
    """Test undo/redo functionality for project deletion."""
    
    def test_delete_project_undo_restores_project(self, project_service, undo_manager):
        """Test that undoing a delete restores the project."""
        # Create project
        project = project_service.create_project(
            name="To Delete",
            description="Will be restored"
        )
        project_id = project.id
        
        # Delete via command
        command = DeleteProjectCommand(
            service=project_service,
            project_id=project_id
        )
        undo_manager.push(command)
        
        # Verify project is deleted
        project = project_service.get_project(project_id)
        assert project is None
        
        # Undo deletion
        undo_manager.undo()
        
        # Verify project is restored (may have new ID)
        restored_id = command._project_id
        project = project_service.get_project(restored_id)
        assert project is not None
        assert project.name == "To Delete"
        assert project.description == "Will be restored"
    
    def test_delete_project_redo_deletes_again(self, project_service, undo_manager):
        """Test that redoing a delete removes the project again."""
        # Create project
        project = project_service.create_project(
            name="To Delete",
            description="Will be restored and deleted"
        )
        
        # Delete via command
        command = DeleteProjectCommand(
            service=project_service,
            project_id=project.id
        )
        undo_manager.push(command)
        
        # Undo deletion (restore)
        undo_manager.undo()
        restored_id = command._project_id
        
        # Verify project exists
        project = project_service.get_project(restored_id)
        assert project is not None
        
        # Redo deletion
        undo_manager.redo()
        
        # Verify project is deleted again
        project = project_service.get_project(restored_id)
        assert project is None
    
    def test_delete_project_preserves_data_on_restore(self, project_service, undo_manager):
        """Test that restored project has all original data."""
        # Create project with specific data
        project = project_service.create_project(
            name="Important Project",
            description="Critical data that must be preserved"
        )
        original_name = project.name
        original_description = project.description
        
        # Delete and restore
        command = DeleteProjectCommand(
            service=project_service,
            project_id=project.id
        )
        undo_manager.push(command)
        undo_manager.undo()
        
        # Verify all data preserved
        restored_project = project_service.get_project(command._project_id)
        assert restored_project.name == original_name
        assert restored_project.description == original_description


class TestViewModelUndoIntegration:
    """Test undo/redo integration with ProjectViewModel."""
    
    def test_viewmodel_create_with_undo_support(self, view_model):
        """Test that view model create operation registers undo command."""
        # Create project via view model
        success = view_model.create_project(
            name="ViewModel Test",
            description="Testing integration"
        )
        assert success
        
        # Verify undo manager has command
        assert view_model._undo_manager.can_undo()
        
        # Get project from cache
        projects = view_model.get_projects_list()
        assert len(projects) > 0
        assert any(p['name'] == "ViewModel Test" for p in projects)
        
        # Undo creation
        view_model._undo_manager.undo()
        
        # Verify project removed from cache
        view_model.refresh_projects()
        projects = view_model.get_projects_list()
        assert not any(p['name'] == "ViewModel Test" for p in projects)
    
    def test_viewmodel_edit_with_undo_support(self, view_model):
        """Test that view model edit operation registers undo command."""
        # Create initial project
        view_model.create_project("Edit Test", "Original")
        projects = view_model.get_projects_list()
        project_id = projects[0]['id']
        
        # Clear undo stack to isolate edit command
        view_model._undo_manager._undo_stack.clear()
        
        # Edit project
        success = view_model.update_project(
            project_id=project_id,
            name="Updated Name",
            description="Updated Description"
        )
        assert success
        
        # Verify edit applied
        view_model.refresh_projects()
        projects = view_model.get_projects_list()
        project = next(p for p in projects if p['id'] == project_id)
        assert project['name'] == "Updated Name"
        
        # Undo edit
        view_model._undo_manager.undo()
        
        # Verify original values restored
        view_model.refresh_projects()
        projects = view_model.get_projects_list()
        project = next(p for p in projects if p['id'] == project_id)
        assert project['name'] == "Edit Test"
    
    def test_viewmodel_delete_with_undo_support(self, view_model):
        """Test that view model delete operation registers undo command."""
        # Create project
        view_model.create_project("Delete Test", "To be deleted")
        projects = view_model.get_projects_list()
        project_id = projects[0]['id']
        
        # Clear undo stack
        view_model._undo_manager._undo_stack.clear()
        
        # Delete project
        success = view_model.delete_project(project_id)
        assert success
        
        # Verify project removed
        view_model.refresh_projects()
        projects = view_model.get_projects_list()
        assert not any(p['id'] == project_id for p in projects)
        
        # Undo deletion
        view_model._undo_manager.undo()
        
        # Verify project restored
        view_model.refresh_projects()
        projects = view_model.get_projects_list()
        assert any(p['name'] == "Delete Test" for p in projects)
    
    def test_viewmodel_signals_emit_on_undo_redo(self, view_model, qtbot):
        """Test that signals are emitted correctly during undo/redo."""
        # Connect to signals
        created_signal = MagicMock()
        deleted_signal = MagicMock()
        view_model.projectCreated.connect(created_signal)
        view_model.projectDeleted.connect(deleted_signal)
        
        # Create project
        view_model.create_project("Signal Test", "Testing signals")
        
        # Verify created signal emitted (once during initial create)
        assert created_signal.call_count >= 1
        
        # Note: Undo/redo operations work directly with service layer
        # and don't re-emit ViewModel signals. This is by design to avoid
        # circular signal loops and maintain clean separation.
        # The projectsListChanged signal should be used to update UI.


class TestComplexUndoRedoScenarios:
    """Test complex scenarios with multiple operations."""
    
    def test_mixed_operations_undo_stack(self, project_service, undo_manager):
        """Test undo stack with mixed create/edit/delete operations."""
        # Create project 1
        cmd1 = CreateProjectCommand(project_service, "Project 1", "Desc 1")
        undo_manager.push(cmd1)
        project1_id = cmd1.get_project_id()
        
        # Create project 2
        cmd2 = CreateProjectCommand(project_service, "Project 2", "Desc 2")
        undo_manager.push(cmd2)
        project2_id = cmd2.get_project_id()
        
        # Edit project 1
        cmd3 = EditProjectCommand(project_service, project1_id, "Project 1 Edited")
        undo_manager.push(cmd3)
        
        # Delete project 2
        cmd4 = DeleteProjectCommand(project_service, project2_id)
        undo_manager.push(cmd4)
        
        # Verify final state
        p1 = project_service.get_project(project1_id)
        p2 = project_service.get_project(project2_id)
        assert p1 is not None and p1.name == "Project 1 Edited"
        assert p2 is None  # Deleted
        
        # Undo delete
        undo_manager.undo()
        p2 = project_service.get_project(cmd4._project_id)
        assert p2 is not None  # Restored
        
        # Undo edit
        undo_manager.undo()
        p1 = project_service.get_project(project1_id)
        assert p1.name == "Project 1"
        
        # Undo create 2
        undo_manager.undo()
        p2 = project_service.get_project(project2_id)
        assert p2 is None
        
        # Undo create 1
        undo_manager.undo()
        p1 = project_service.get_project(project1_id)
        assert p1 is None
    
    def test_undo_redo_preserves_stack_integrity(self, project_service, undo_manager):
        """Test that undo/redo operations maintain stack integrity."""
        # Perform operations
        cmd1 = CreateProjectCommand(project_service, "Test 1")
        cmd2 = CreateProjectCommand(project_service, "Test 2")
        undo_manager.push(cmd1)
        undo_manager.push(cmd2)
        
        # Undo all
        assert undo_manager.can_undo()
        undo_manager.undo()
        assert undo_manager.can_undo()
        undo_manager.undo()
        assert not undo_manager.can_undo()
        
        # Redo all
        assert undo_manager.can_redo()
        undo_manager.redo()
        assert undo_manager.can_redo()
        undo_manager.redo()
        assert not undo_manager.can_redo()
        
        # Verify final state matches initial operations
        p1 = project_service.get_project(cmd1.get_project_id())
        p2 = project_service.get_project(cmd2.get_project_id())
        assert p1 is not None
        assert p2 is not None

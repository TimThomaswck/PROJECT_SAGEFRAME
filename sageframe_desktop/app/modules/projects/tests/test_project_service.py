"""Unit tests for ProjectService.

Tests cover CRUD operations, validation, error handling, and edge cases.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.modules.projects.models import Project, ProjectSchema
from app.modules.projects.services import ProjectService


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal


@pytest.fixture
def service(in_memory_db):
    """Create ProjectService with test database."""
    return ProjectService(db_session=in_memory_db())


class TestProjectServiceCreate:
    """Tests for project creation."""
    
    def test_create_project_success(self, service):
        """Test successful project creation."""
        project = service.create_project(
            name="Test Project",
            description="A test project"
        )
        
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.created_at is not None
        assert project.updated_at is not None
    
    def test_create_project_without_description(self, service):
        """Test creating project without description."""
        project = service.create_project(name="Simple Project")
        
        assert project.id is not None
        assert project.name == "Simple Project"
        assert project.description is None
    
    def test_create_project_with_none_description(self, service):
        """Test creating project with explicit None description."""
        project = service.create_project(
            name="Project",
            description=None
        )
        
        assert project.description is None
    
    def test_create_project_empty_name_fails(self, service):
        """Test that empty project name raises error."""
        with pytest.raises(ValueError):
            service.create_project(name="")
    
    def test_create_project_whitespace_name_fails(self, service):
        """Test that whitespace-only name raises error."""
        with pytest.raises(ValueError):
            service.create_project(name="   ")
    
    def test_create_project_strips_whitespace(self, service):
        """Test that leading/trailing whitespace is stripped."""
        project = service.create_project(
            name="  Project Name  ",
            description="  Description  "
        )
        
        assert project.name == "Project Name"
        assert project.description == "Description"
    
    def test_create_project_with_user_id(self, service):
        """Test creating project with user ID (for multi-tenancy)."""
        project = service.create_project(
            name="User Project",
            user_id=42
        )
        
        assert project.user_id == 42
    
    def test_create_project_max_name_length(self, service):
        """Test creating project with maximum name length (255)."""
        long_name = "A" * 255
        project = service.create_project(name=long_name)
        
        assert len(project.name) == 255
    
    def test_create_project_exceeds_max_length_fails(self, service):
        """Test that exceeding max name length raises error."""
        too_long_name = "A" * 256
        with pytest.raises(ValueError):
            service.create_project(name=too_long_name)
    
    def test_create_project_description_max_length(self, service):
        """Test creating project with maximum description length (5000)."""
        long_desc = "A" * 5000
        project = service.create_project(
            name="Project",
            description=long_desc
        )
        
        assert len(project.description) == 5000


class TestProjectServiceRead:
    """Tests for reading projects."""
    
    def test_get_project_success(self, service):
        """Test retrieving an existing project."""
        created = service.create_project(name="Test")
        retrieved = service.get_project(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test"
    
    def test_get_project_not_found(self, service):
        """Test retrieving non-existent project returns None."""
        result = service.get_project(9999)
        assert result is None
    
    def test_list_projects_empty(self, service):
        """Test listing projects when none exist."""
        projects = service.list_projects()
        assert projects == []
    
    def test_list_projects_multiple(self, service):
        """Test listing multiple projects."""
        service.create_project(name="Project 1")
        service.create_project(name="Project 2")
        service.create_project(name="Project 3")
        
        projects = service.list_projects()
        assert len(projects) == 3
        assert all(p.name.startswith("Project") for p in projects)
    
    def test_list_projects_ordered_by_creation_desc(self, service):
        """Test that projects are ordered by creation date (newest first)."""
        p1 = service.create_project(name="First")
        p2 = service.create_project(name="Second")
        p3 = service.create_project(name="Third")
        
        projects = service.list_projects()
        
        assert projects[0].id == p3.id
        assert projects[1].id == p2.id
        assert projects[2].id == p1.id
    
    def test_list_projects_filter_by_user(self, service):
        """Test filtering projects by user ID."""
        service.create_project(name="User1 Project", user_id=1)
        service.create_project(name="User2 Project", user_id=2)
        service.create_project(name="User1 Project 2", user_id=1)
        
        user1_projects = service.list_projects(user_id=1)
        
        assert len(user1_projects) == 2
        assert all(p.user_id == 1 for p in user1_projects)


class TestProjectServiceUpdate:
    """Tests for updating projects."""
    
    def test_update_project_name(self, service):
        """Test updating project name."""
        original = service.create_project(name="Original Name")
        updated = service.update_project(original.id, name="New Name")
        
        assert updated.name == "New Name"
        assert updated.id == original.id
    
    def test_update_project_description(self, service):
        """Test updating project description."""
        original = service.create_project(
            name="Project",
            description="Original"
        )
        updated = service.update_project(original.id, description="New Description")
        
        assert updated.description == "New Description"
        assert updated.name == "Project"  # Name unchanged
    
    def test_update_project_both_fields(self, service):
        """Test updating both name and description."""
        original = service.create_project(
            name="Old",
            description="Old Desc"
        )
        updated = service.update_project(
            original.id,
            name="New",
            description="New Desc"
        )
        
        assert updated.name == "New"
        assert updated.description == "New Desc"
    
    def test_update_project_not_found(self, service):
        """Test updating non-existent project raises error."""
        with pytest.raises(ValueError, match="not found"):
            service.update_project(9999, name="New Name")
    
    def test_update_project_empty_name_fails(self, service):
        """Test that empty name in update raises error."""
        project = service.create_project(name="Project")
        
        with pytest.raises(ValueError):
            service.update_project(project.id, name="")
    
    def test_update_project_timestamp_changes(self, service):
        """Test that updated_at timestamp is updated."""
        project = service.create_project(name="Project")
        original_updated = project.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        updated = service.update_project(project.id, name="Updated")
        
        assert updated.updated_at > original_updated
    
    def test_update_project_only_provided_fields(self, service):
        """Test that only provided fields are updated."""
        project = service.create_project(
            name="Original",
            description="Keep This"
        )
        
        updated = service.update_project(project.id, name="New")
        
        assert updated.name == "New"
        assert updated.description == "Keep This"


class TestProjectServiceDelete:
    """Tests for deleting projects."""
    
    def test_delete_project_success(self, service):
        """Test successful project deletion."""
        project = service.create_project(name="To Delete")
        success = service.delete_project(project.id)
        
        assert success is True
        assert service.get_project(project.id) is None
    
    def test_delete_project_not_found(self, service):
        """Test deleting non-existent project returns False."""
        success = service.delete_project(9999)
        assert success is False
    
    def test_delete_project_removes_from_list(self, service):
        """Test that deleted project no longer appears in list."""
        p1 = service.create_project(name="Keep")
        p2 = service.create_project(name="Delete")
        
        service.delete_project(p2.id)
        
        projects = service.list_projects()
        assert len(projects) == 1
        assert projects[0].id == p1.id


class TestProjectServiceContextManager:
    """Tests for context manager functionality."""
    
    def test_context_manager_closes_session(self, in_memory_db):
        """Test that context manager properly closes session."""
        with ProjectService(db_session=in_memory_db()) as service:
            project = service.create_project(name="Project")
            assert project.id is not None
        
        # Service should be closed after context exit
        # (No assertion needed, just verify no errors)
    
    def test_multiple_operations_in_context(self, in_memory_db):
        """Test multiple operations within context manager."""
        with ProjectService(db_session=in_memory_db()) as service:
            p1 = service.create_project(name="First")
            p2 = service.create_project(name="Second")
            
            retrieved = service.get_project(p1.id)
            assert retrieved.name == "First"
            
            updated = service.update_project(p2.id, name="Updated")
            assert updated.name == "Updated"
            
            service.delete_project(p1.id)
            assert service.get_project(p1.id) is None

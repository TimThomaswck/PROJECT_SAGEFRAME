"""Business logic service for project management.

This module provides service layer functionality for managing project data.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.modules.projects.models import Project, ProjectSchema


class ProjectService:
    """Service class for project business logic.
    
    Handles data validation, persistence, and retrieval for projects.
    Follows the service pattern to separate business logic from UI (MVVM).
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """Initialize service with optional database session.
        
        Args:
            db_session: SQLAlchemy session (optional, creates new if not provided)
            
        Raises:
            Exception: If database session cannot be created
        """
        if db_session is not None:
            self._db = db_session
            self._owns_session = False
        else:
            try:
                self._db = SessionLocal()
                self._owns_session = True
            except Exception as e:
                raise Exception(f"Failed to initialize database session: {e}") from e
    
    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        user_id: Optional[int] = None,
        id: Optional[int] = None
    ) -> Project:
        """Create and save a new project.
        
        Args:
            name: Project name (required)
            description: Optional project description
            user_id: Optional user ID (for future multi-tenancy)
            id: Optional project ID (used for undo/redo to preserve original ID)
        
        Returns:
            Project: The created project record
        
        Raises:
            ValueError: If validation fails
            Exception: If database operation fails
        """
        try:
            # Validate input using Pydantic schema (hybrid validation approach)
            validated_data = ProjectSchema(
                name=name,
                description=description
            )
            
            # Create SQLAlchemy model instance
            project = Project(
                name=validated_data.name,
                description=validated_data.description,
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # If ID is provided (from undo/redo), set it to preserve data integrity
            if id is not None:
                project.id = id
            
            # Persist to database
            self._db.add(project)
            self._db.commit()
            self._db.refresh(project)
            
            return project
            
        except ValidationError as e:
            # Pydantic validation failed
            raise ValueError(f"Project validation failed: {e}")
        except Exception as e:
            # Database or other error
            self._db.rollback()
            raise Exception(f"Failed to create project: {e}") from e
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """Get a project by ID.
        
        Args:
            project_id: The project ID to retrieve
        
        Returns:
            Project or None: The project if found, None otherwise
        
        Raises:
            Exception: If database operation fails
        """
        try:
            stmt = select(Project).where(Project.id == project_id)
            return self._db.execute(stmt).scalar_one_or_none()
        except Exception as e:
            raise Exception(f"Failed to retrieve project {project_id}: {e}") from e
    
    def list_projects(self, user_id: Optional[int] = None) -> List[Project]:
        """Get all projects, optionally filtered by user.
        
        Args:
            user_id: Optional user ID filter (for future multi-tenancy)
        
        Returns:
            List[Project]: List of all projects, ordered by creation date (newest first)
        """
        stmt = select(Project).order_by(Project.created_at.desc())
        
        if user_id is not None:
            stmt = stmt.where(Project.user_id == user_id)
        
        return list(self._db.execute(stmt).scalars().all())
    
    def update_project(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Project:
        """Update project attributes.
        
        Args:
            project_id: The project ID to update
            name: New project name (optional)
            description: New project description (optional)
        
        Returns:
            Project: The updated project
        
        Raises:
            ValueError: If project not found or validation fails
            Exception: If database operation fails
        """
        try:
            # Find existing project
            project = self.get_project(project_id)
            if project is None:
                raise ValueError(f"Project {project_id} not found")
            
            # Prepare update data (only non-None values)
            update_data = {}
            if name is not None:
                update_data['name'] = name
            if description is not None:
                update_data['description'] = description
            
            # Validate updated fields
            validated_data = ProjectSchema(
                name=update_data.get('name', project.name),
                description=update_data.get('description', project.description)
            )
            
            # Apply updates
            project.name = validated_data.name
            project.description = validated_data.description
            project.updated_at = datetime.now(timezone.utc)
            
            # Persist
            self._db.commit()
            self._db.refresh(project)
            
            return project
            
        except ValueError:
            raise
        except ValidationError as e:
            self._db.rollback()
            raise ValueError(f"Project validation failed: {e}") from e
        except Exception as e:
            self._db.rollback()
            raise Exception(f"Failed to update project {project_id}: {e}") from e
    
    def delete_project(self, project_id: int) -> bool:
        """Delete a project by ID.
        
        Args:
            project_id: The project ID to delete
        
        Returns:
            bool: True if deleted, False if not found
        
        Raises:
            Exception: If database operation fails
        """
        try:
            project = self.get_project(project_id)
            if project is None:
                return False
            
            # Check if project has associated tasks (future validation)
            # For now, allow deletion - Task 2.2 will handle task relationships
            
            self._db.delete(project)
            self._db.commit()
            
            return True
            
        except Exception as e:
            self._db.rollback()
            raise Exception(f"Failed to delete project {project_id}: {e}") from e
    
    def close(self):
        """Close database session if owned by this service."""
        if self._owns_session:
            self._db.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.close()

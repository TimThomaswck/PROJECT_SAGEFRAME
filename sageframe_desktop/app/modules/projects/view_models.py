"""ViewModel for project management functionality.

This module implements the ViewModel layer of the MVVM pattern for projects.
"""

from typing import Optional

from PySide6.QtCore import QObject, Signal, Property

from app.modules.projects.services import ProjectService
from app.core.undo_commands import CreateProjectCommand, EditProjectCommand, DeleteProjectCommand


class ProjectViewModel(QObject):
    """ViewModel for project management operations.
    
    Manages UI state and coordinates with the service layer.
    Follows MVVM pattern with Qt's property system and signals/slots.
    """
    
    # Signals (verbNoun naming convention as per architecture)
    projectCreated = Signal(int, str)  # project_id, name
    projectUpdated = Signal(int, str)  # project_id, name
    projectDeleted = Signal(int)  # project_id
    projectsListChanged = Signal()  # Emitted when project list changes
    validationError = Signal(str)  # Validation error message
    operationError = Signal(str)  # Database/operation error message
    
    def __init__(self, parent: Optional[QObject] = None, undo_manager=None):
        """Initialize ViewModel.
        
        Args:
            parent: Optional parent QObject
            undo_manager: Optional UndoManager instance for undo/redo support
        """
        super().__init__(parent)
        self._service = ProjectService()
        self._undo_manager = undo_manager
        self._current_project_id: Optional[int] = None
        self._project_name = ""
        self._project_description = ""
        self._projects_cache = []
        self._is_submitting = False
        self._validation_errors = {}
    
    # Properties for two-way data binding
    @Property(str)
    def projectName(self) -> str:
        """Get current project name."""
        return self._project_name
    
    @projectName.setter
    def projectName(self, value: str):
        """Set project name."""
        if self._project_name != value:
            self._project_name = value
            self._validate_name()
    
    @Property(str)
    def projectDescription(self) -> str:
        """Get current project description."""
        return self._project_description
    
    @projectDescription.setter
    def projectDescription(self, value: str):
        """Set project description."""
        if self._project_description != value:
            self._project_description = value
    
    @Property(bool)
    def isSubmitting(self) -> bool:
        """Get submission state."""
        return self._is_submitting
    
    @Property(int)
    def currentProjectId(self) -> int:
        """Get currently selected project ID."""
        return self._current_project_id or 0
    
    @currentProjectId.setter
    def currentProjectId(self, value: int):
        """Set currently selected project ID."""
        self._current_project_id = value if value > 0 else None
    
    # Public methods for business logic
    
    def create_project(self, name: str, description: Optional[str] = None) -> bool:
        """Create a new project.
        
        Args:
            name: Project name
            description: Optional project description
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self._is_submitting:
            return False  # Prevent double submission
        
        # Validate input
        if not name or not name.strip():
            self.validationError.emit("Project name cannot be empty")
            return False
        
        self._is_submitting = True
        
        try:
            # Create undo command if undo_manager is available
            if self._undo_manager:
                # Create command (will execute redo() to create project)
                command = CreateProjectCommand(
                    service=self._service,
                    name=name,
                    description=description if description else None
                )
                # Execute command through undo manager
                self._undo_manager.push(command)
                project_id = command.get_project_id()
                
                # Get created project for signal
                project = self._service.get_project(project_id)
            else:
                # Create directly without undo support
                project = self._service.create_project(
                    name=name,
                    description=description if description else None
                )
            
            # Refresh cache
            self._load_projects_cache()
            
            # Emit signal
            self.projectCreated.emit(project.id, project.name)
            self.projectsListChanged.emit()
            
            # Reset form
            self._project_name = ""
            self._project_description = ""
            self._validation_errors.clear()
            
            return True
            
        except ValueError as e:
            self.validationError.emit(str(e))
            return False
        except Exception as e:
            self.operationError.emit(f"Failed to create project: {str(e)}")
            return False
        finally:
            self._is_submitting = False
    
    def update_project(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """Update an existing project.
        
        Args:
            project_id: Project ID to update
            name: New project name (optional)
            description: New project description (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self._is_submitting:
            return False
        
        self._is_submitting = True
        
        try:
            # Update with undo command if undo_manager is available
            if self._undo_manager:
                # Create and execute edit command
                command = EditProjectCommand(
                    service=self._service,
                    project_id=project_id,
                    new_name=name,
                    new_description=description
                )
                self._undo_manager.push(command)
                
                # Get updated project for signal
                project = self._service.get_project(project_id)
            else:
                # Update directly without undo support
                project = self._service.update_project(
                    project_id=project_id,
                    name=name,
                    description=description
                )
            
            # Refresh cache
            self._load_projects_cache()
            
            # Emit signal
            self.projectUpdated.emit(project.id, project.name)
            self.projectsListChanged.emit()
            
            return True
            
        except ValueError as e:
            self.validationError.emit(str(e))
            return False
        except Exception as e:
            self.operationError.emit(f"Failed to update project: {str(e)}")
            return False
        finally:
            self._is_submitting = False
    
    def delete_project(self, project_id: int) -> bool:
        """Delete a project.
        
        Args:
            project_id: Project ID to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self._is_submitting:
            return False
        
        self._is_submitting = True
        
        try:
            # Delete with undo command if undo_manager is available
            if self._undo_manager:
                # Create and execute delete command
                command = DeleteProjectCommand(
                    service=self._service,
                    project_id=project_id
                )
                self._undo_manager.push(command)
                success = True
            else:
                # Delete directly without undo support
                success = self._service.delete_project(project_id)
            
            if success:
                # Refresh cache
                self._load_projects_cache()
                
                # Emit signal
                self.projectDeleted.emit(project_id)
                self.projectsListChanged.emit()
                
                # Clear selection if we deleted current project
                if self._current_project_id == project_id:
                    self._current_project_id = None
            else:
                self.validationError.emit(f"Project {project_id} not found")
            
            return success
            
        except Exception as e:
            self.operationError.emit(f"Failed to delete project: {str(e)}")
            return False
        finally:
            self._is_submitting = False
    
    def load_project(self, project_id: int) -> bool:
        """Load project details for viewing/editing.
        
        Args:
            project_id: Project ID to load
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = self._service.get_project(project_id)
            if project is None:
                self.validationError.emit(f"Project {project_id} not found")
                return False
            
            self._current_project_id = project.id
            self._project_name = project.name
            self._project_description = project.description or ""
            
            return True
            
        except Exception as e:
            self.operationError.emit(f"Failed to load project: {str(e)}")
            return False
    
    def get_projects_list(self):
        """Get cached list of projects.
        
        Returns:
            List of project dictionaries
        """
        return self._projects_cache
    
    def refresh_projects(self) -> bool:
        """Refresh projects list from database.
        
        Returns:
            bool: True if successful
        """
        try:
            self._load_projects_cache()
            self.projectsListChanged.emit()
            return True
        except Exception as e:
            self.operationError.emit(f"Failed to refresh projects: {str(e)}")
            return False
    
    # Private helper methods
    
    def _load_projects_cache(self):
        """Load projects from service and cache them."""
        try:
            projects = self._service.list_projects()
            self._projects_cache = [
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description or '',
                    'created_at': p.created_at,
                    'updated_at': p.updated_at
                }
                for p in projects
            ]
        except Exception as e:
            self.operationError.emit(f"Failed to load projects: {str(e)}")
            self._projects_cache = []
    
    def _validate_name(self):
        """Validate project name field."""
        if not self._project_name.strip():
            self._validation_errors['name'] = "Project name cannot be empty"
        else:
            self._validation_errors.pop('name', None)
    
    def close(self):
        """Clean up resources."""
        if self._service:
            self._service.close()
    
    def __del__(self):
        """Destructor - ensure resources are cleaned up."""
        self.close()

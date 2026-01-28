"""ViewModel for task management functionality.

This module implements the ViewModel layer of the MVVM pattern for tasks.
Follows the same pattern as ProjectViewModel from Story 2.1.
Includes task properties: priority and complexity.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union # Added Union import

from PySide6.QtCore import QObject, Signal, Property

from app.core.undo_manager import UndoManager
from app.modules.tasks.services import TaskService
# Import Task for type hints to avoid NameError at runtime
from app.modules.tasks.models import Task, TaskPriority, TaskComplexity, TaskStatus, VALID_STATUSES


class TaskViewModel(QObject):
    """ViewModel for task management operations.
    
    Manages UI state and coordinates with the service layer.
    Follows MVVM pattern with Qt's property system and signals/slots.
    Supports task properties: priority and complexity.
    """
    
    # Signals (verbNoun naming convention as per architecture)
    taskCreated = Signal(int, str)  # task_id, title
    taskUpdated = Signal(int, str)  # task_id, title
    taskDeleted = Signal(int)  # task_id
    tasksListChanged = Signal()  # Emitted when task list changes
    validationError = Signal(str)  # Validation error message
    operationError = Signal(str)  # Database/operation error message
    
    # Property changed signals
    taskPriorityChanged = Signal(str)  # Priority value
    taskComplexityChanged = Signal(str)  # Complexity value
    taskStatusChanged = Signal(str) # New: Status value
    
    def __init__(self, parent: Optional[QObject] = None, undo_manager=None):
        """Initialize ViewModel.
        
        Args:
            parent: Optional parent QObject
            undo_manager: Optional UndoManager instance for undo/redo support
        """
        super().__init__(parent)
        self._service = TaskService()
        self._undo_manager = undo_manager
        self._current_task_id: Optional[int] = None
        self._task_title = ""
        self._task_description = ""
        self._task_due_date: Optional[datetime] = None
        self._task_status = TaskStatus.TODO
        self._task_priority = 'medium'
        self._task_complexity = 'moderate'
        self._task_project_id: Optional[int] = None
        self._task_start_date: Optional[datetime] = None
        self._task_end_date: Optional[datetime] = None
        self._depends_on_task_id: Optional[int] = None
        self._dependency_type: Optional[str] = None
        self._tasks_cache: List[Dict[str, Any]] = []
        self._is_submitting = False
        self._is_loading = False  # Reentrancy guard to avoid recursive loads
        self._validation_errors: Dict[str, str] = {}
        self._current_filter_project_id: Optional[int] = None
        self._current_filter_status: Optional[TaskStatus] = None
    
    # Properties for two-way data binding
    @Property(str)
    def taskTitle(self) -> str:
        """Get current task title."""
        return self._task_title
    
    @taskTitle.setter
    def taskTitle(self, value: str):
        """Set task title."""
        if self._task_title != value:
            self._task_title = value
            self._validate_title()
    
    @Property(str)
    def taskDescription(self) -> str:
        """Get current task description."""
        return self._task_description
    
    @taskDescription.setter
    def taskDescription(self, value: str):
        """Set task description."""
        if self._task_description != value:
            self._task_description = value
    
    @Property(str)
    def taskStatus(self) -> str:
        """Get current task status."""
        return self._task_status.value if isinstance(self._task_status, TaskStatus) else str(self._task_status)
    
    @taskStatus.setter
    def taskStatus(self, value: str):
        """Set task status."""
        try:
            if isinstance(value, str):
                status = TaskStatus(value.lower())
            else:
                status = value
            
            if self._task_status != status:
                self._task_status = status
                self.taskStatusChanged.emit(status.value)
        except (ValueError, AttributeError) as e:
            self.validationError.emit(f"Invalid status: {value}")
    
    @Property(bool)
    def isSubmitting(self) -> bool:
        """Get submission state."""
        return self._is_submitting
    
    @Property(int)
    def currentTaskId(self) -> int:
        """Get currently selected task ID."""
        return self._current_task_id or 0
    
    @currentTaskId.setter
    def currentTaskId(self, value: int):
        """Set currently selected task ID."""
        self._current_task_id = value if value > 0 else None
    
    @Property(int)
    def taskProjectId(self) -> int:
        """Get task's project ID (0 if standalone)."""
        return self._task_project_id or 0
    
    @taskProjectId.setter
    def taskProjectId(self, value: int):
        """Set task's project ID."""
        self._task_project_id = value if value > 0 else None
    
    @Property(str)
    def taskPriority(self) -> str:
        """Get current task priority as string."""
        return self._task_priority
    
    @taskPriority.setter
    def taskPriority(self, value: str):
        """Set task priority.
        
        Args:
            value: Priority value as string or TaskPriority enum
        """
        try:
            # Extract string value if it's an enum, otherwise use directly
            if isinstance(value, TaskPriority):
                priority_str = value.value
            else:
                priority_str = str(value).lower() if value else 'medium'
            
            if self._task_priority != priority_str:
                self._task_priority = priority_str
                self.taskPriorityChanged.emit(priority_str)
        except (ValueError, AttributeError) as e:
            self.validationError.emit(f"Invalid priority: {value}")
    
    @Property(str)
    def taskComplexity(self) -> str:
        """Get current task complexity as string."""
        return self._task_complexity
    
    @taskComplexity.setter
    def taskComplexity(self, value: str):
        """Set task complexity.
        
        Args:
            value: Complexity value as string or TaskComplexity enum
        """
        try:
            # Extract string value if it's an enum, otherwise use directly
            if isinstance(value, TaskComplexity):
                complexity_str = value.value
            else:
                complexity_str = str(value).lower() if value else 'moderate'
            
            if self._task_complexity != complexity_str:
                self._task_complexity = complexity_str
                self.taskComplexityChanged.emit(complexity_str)
        except (ValueError, AttributeError) as e:
            self.validationError.emit(f"Invalid complexity: {value}")
    
    # Public methods for business logic
    
    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        status: Union[TaskStatus, str] = TaskStatus.TODO,
        priority: Optional[TaskPriority] = None,
        complexity: Optional[TaskComplexity] = None,
        project_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bool:
        """Create a new task.
        
        Args:
            title: Task title
            description: Optional task description
            due_date: Optional due date
            status: Task status (default: TODO)
            priority: Optional priority level (default: MEDIUM)
            complexity: Optional complexity level (default: MODERATE)
            project_id: Optional project association
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self._is_submitting:
            return False  # Prevent double submission
        
        # Validate input
        if not title or not title.strip():
            self.validationError.emit(self.tr("Task title cannot be empty"))
            return False
        
        # Use current values if not specified
        if priority is None:
            priority = self._task_priority
        if complexity is None:
            complexity = self._task_complexity
        
        self._is_submitting = True
        
        try:
            # Create with undo command if undo_manager is available
            if self._undo_manager:
                from app.core.undo_commands import CreateTaskCommand
                command = CreateTaskCommand(
                    service=self._service,
                    title=title,
                    description=description if description else None,
                    due_date=due_date,
                    status=status,
                    priority=priority,
                    complexity=complexity,
                    project_id=project_id
                )
                self._undo_manager.push(command)
                task_id = command.get_task_id()
                task = self._service.get_task(task_id)
                # Update timeline fields if provided (undo command doesn't handle these yet)
                if start_date or end_date:
                    self._service.update_task(task_id, start_date=start_date, end_date=end_date)
                    task = self._service.get_task(task_id)
            else:
                # Create directly without undo support
                task = self._service.create_task(
                    title=title,
                    description=description if description else None,
                    due_date=due_date,
                    status=status,
                    priority=priority,
                    complexity=complexity,
                    project_id=project_id,
                    start_date=start_date,
                    end_date=end_date
                )
            
            # Refresh cache
            self._load_tasks_cache()
            
            # Emit signal
            self.taskCreated.emit(task.id, task.title)
            self.tasksListChanged.emit()
            
            # Reset form
            self._reset_form()
            
            return True
            
        except ValueError as e:
            self.validationError.emit(str(e))
            return False
        except Exception as e:
            self.operationError.emit(self.tr("Failed to create task: {}").format(str(e)))
            return False
        finally:
            self._is_submitting = False
    
    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        status: Optional[Union[TaskStatus, str]] = None,
        priority: Optional[TaskPriority] = None,
        complexity: Optional[TaskComplexity] = None,
        project_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        depends_on_task_id: Optional[int] = None,
        dependency_type: Optional[str] = None,
    ) -> bool:
        """Update an existing task.
        
        Args:
            task_id: Task ID to update
            title: New task title (optional)
            description: New task description (optional)
            due_date: New due date (optional)
            status: New status (optional)
            priority: New priority level (optional)
            complexity: New complexity level (optional)
            project_id: New project association (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self._is_submitting:
            return False
        
        self._is_submitting = True
        
        try:
            # Update with undo command if undo_manager is available
            if self._undo_manager:
                from app.core.undo_commands import EditTaskCommand
                command = EditTaskCommand(
                    service=self._service,
                    task_id=task_id,
                    new_title=title,
                    new_description=description,
                    new_due_date=due_date,
                    new_status=status,
                    new_priority=priority,
                    new_complexity=complexity,
                    new_project_id=project_id
                )
                self._undo_manager.push(command)
                task = self._service.get_task(task_id)
            else:
                # Update directly without undo support
                task = self._service.update_task(
                    task_id=task_id,
                    title=title,
                    description=description,
                    due_date=due_date,
                    status=status,
                    priority=priority,
                    complexity=complexity,
                    project_id=project_id,
                    start_date=start_date,
                    end_date=end_date,
                    depends_on_task_id=depends_on_task_id,
                    dependency_type=dependency_type,
                )
            
            if task is None:
                self.validationError.emit(self.tr("Task {} not found").format(task_id))
                return False
            
            # Emit property change signals if properties were updated
            if priority is not None:
                priority_value = task.priority.value if hasattr(task.priority, "value") else task.priority
                self.taskPriorityChanged.emit(priority_value)
            if complexity is not None:
                complexity_value = task.complexity.value if hasattr(task.complexity, "value") else task.complexity
                self.taskComplexityChanged.emit(complexity_value)
            if status is not None: # New: emit status change signal
                status_value = task.status.value if hasattr(task.status, "value") else task.status
                self.taskStatusChanged.emit(status_value)
            
            # Refresh cache
            self._load_tasks_cache()
            
            # Emit signal
            self.taskUpdated.emit(task.id, task.title)
            self.tasksListChanged.emit()
            
            return True
            
        except ValueError as e:
            self.validationError.emit(str(e))
            return False
        except Exception as e:
            self.operationError.emit(self.tr("Failed to update task: {}").format(str(e)))
            return False
        finally:
            self._is_submitting = False
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task.
        
        Args:
            task_id: Task ID to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self._is_submitting:
            return False
        
        self._is_submitting = True
        
        try:
            # Delete with undo command if undo_manager is available
            if self._undo_manager:
                from app.core.undo_commands import DeleteTaskCommand
                command = DeleteTaskCommand(
                    service=self._service,
                    task_id=task_id
                )
                self._undo_manager.push(command)
                success = True
            else:
                # Delete directly without undo support
                success = self._service.delete_task(task_id)
            
            if success:
                # Refresh cache
                self._load_tasks_cache()
                
                # Emit signal
                self.taskDeleted.emit(task_id)
                self.tasksListChanged.emit()
                
                # Clear selection if we deleted current task
                if self._current_task_id == task_id:
                    self._current_task_id = None
            else:
                self.validationError.emit(self.tr("Task {} not found").format(task_id))
            
            return success
            
        except Exception as e:
            self.operationError.emit(self.tr("Failed to delete task: {}").format(str(e)))
            return False
        finally:
            self._is_submitting = False
    
    def load_task(self, task_id: int) -> bool:
        """Load task details for viewing/editing.
        
        Args:
            task_id: Task ID to load
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            task = self._service.get_task(task_id)
            if task is None:
                self.validationError.emit(self.tr("Task {} not found").format(task_id))
                return False
            
            self._current_task_id = task.id
            self._task_title = task.title
            self._task_description = task.description or ""
            self._task_due_date = task.due_date
            self._task_status = task.status
            self._task_project_id = task.project_id
            self._task_start_date = task.start_date
            self._task_end_date = task.end_date
            self._depends_on_task_id = task.depends_on_task_id
            self._dependency_type = task.dependency_type
            
            return True
            
        except Exception as e:
            self.operationError.emit(self.tr("Failed to load task: {}").format(str(e)))
            return False
    
    def get_tasks_list(self) -> List[Dict[str, Any]]:
        """Get cached list of tasks.
        
        Returns:
            List of task dictionaries
        """
        return self._tasks_cache

    def get_tasks_grouped_by_status(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group cached tasks by status for Kanban rendering.

        Returns:
            Mapping of status -> list of task dictionaries
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {status: [] for status in VALID_STATUSES}
        for task in self._tasks_cache:
            status = task.get("status", TaskStatus.TODO.value) # Use TaskStatus.TODO.value
            grouped.setdefault(status, []).append(task)
        return grouped
    
    def get_tasks_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get tasks for a specific project.
        
        Args:
            project_id: Project ID to filter by
            
        Returns:
            List of task dictionaries for the project
        """
        return [t for t in self._tasks_cache if t.get('project_id') == project_id]
    
    def get_tasks_for_project(self, project_id: int) -> List[Task]:
        """Get Task model instances for a specific project.
        
        Args:
            project_id: Project ID to filter by
            
        Returns:
            List of Task objects for the project
        """
        with self._service:
            return self._service.list_tasks(project_id=project_id)
    
    def get_standalone_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks not associated with any project.
        
        Returns:
            List of standalone task dictionaries
        """
        return [t for t in self._tasks_cache if t.get('project_id') is None]
    
    def set_filter(
        self,
        project_id: Optional[int] = None,
        status: Optional[Union[TaskStatus, str]] = None # Changed type
    ):
        """Set filter for task list.
        
        Args:
            project_id: Filter by project (None = all)
            status: Filter by status (None = all)
        """
        if isinstance(status, str): # New: convert string to TaskStatus
            status = TaskStatus(status.lower())
        self._current_filter_project_id = project_id
        self._current_filter_status = status
        self._load_tasks_cache()
        self.tasksListChanged.emit()
    
    def clear_filter(self):
        """Clear all filters."""
        self._current_filter_project_id = None
        self._current_filter_status = None
        self._load_tasks_cache()
        self.tasksListChanged.emit()
    
    def refresh_tasks(self) -> bool:
        """Refresh tasks list from database.
        
        Returns:
            bool: True if successful
        """
        try:
            self._load_tasks_cache()
            self.tasksListChanged.emit()
            return True
        except Exception as e:
            self.operationError.emit(self.tr("Failed to refresh tasks: {}").format(str(e)))
            return False

    def update_task_status(self, task_id: int, new_status: Union[TaskStatus, str]) -> bool: # Changed type
        """Update task status (used by Kanban drag-and-drop).

        Args:
            task_id: Task identifier
            new_status: Target status value

        Returns:
            bool: True if status was updated
        """
        if isinstance(new_status, str): # New: convert string to TaskStatus for validation
            new_status_enum = TaskStatus(new_status.lower())
        else:
            new_status_enum = new_status

        if new_status_enum.value not in VALID_STATUSES: # Validate enum value
            self.validationError.emit(self.tr(f"Invalid status: {new_status}"))
            return False

        return self.update_task(task_id, status=new_status_enum) # Pass enum to update
    
    def count_tasks_by_project(self, project_id: int) -> int:
        """Count tasks for a specific project.
        
        Args:
            project_id: Project ID to count tasks for
            
        Returns:
            Number of tasks in the project
        """
        try:
            return self._service.count_tasks_by_project(project_id)
        except Exception:
            return 0
    
    # Private helper methods
    
    def _load_tasks_cache(self):
        """Load tasks from service and cache them.
        Guards against re-entrant calls which can cause recursion loops.
        """
        if getattr(self, "_is_loading", False):
            return
        self._is_loading = True
        try:
            tasks = self._service.list_tasks(
                project_id=self._current_filter_project_id,
                status=self._current_filter_status # Status type is now TaskStatus
            )
            self._tasks_cache = [
                {
                    'id': t.id,
                    'title': t.title,
                    'description': t.description or '',
                    'due_date': t.due_date,
                    'status': t.status.value if isinstance(t.status, TaskStatus) else str(t.status), # Access .value
                    'project_id': t.project_id,
                    'priority': getattr(t.priority, "value", str(t.priority)),
                    'complexity': getattr(t.complexity, "value", str(t.complexity)),
                    'start_date': getattr(t, 'start_date', None),
                    'end_date': getattr(t, 'end_date', None),
                    'depends_on_task_id': getattr(t, 'depends_on_task_id', None),
                    'dependency_type': getattr(t, 'dependency_type', None),
                    'created_at': t.created_at,
                    'updated_at': t.updated_at
                }
                for t in tasks
            ]
        except Exception as e:
            # Avoid recursive dialog pops on deep recursion; log-friendly message
            msg = f"Failed to load tasks: {e}" if not isinstance(e, RecursionError) else "Failed to load tasks (retry later)"
            self.operationError.emit(self.tr(msg))
            self._tasks_cache = []
        finally:
            self._is_loading = False
    
    def _validate_title(self):
        """Validate task title field."""
        if not self._task_title.strip():
            self._validation_errors['title'] = "Task title cannot be empty"
        else:
            self._validation_errors.pop('title', None)
    
    def _reset_form(self):
        """Reset form fields after successful operation."""
        self._task_title = ""
        self._task_description = ""
        self._task_due_date = None
        self._task_status = TaskStatus.TODO
        self._task_project_id = None
        self._task_start_date = None
        self._task_end_date = None
        self._depends_on_task_id = None
        self._dependency_type = None
        self._validation_errors.clear()
    
    def get_task_due_date(self) -> Optional[datetime]:
        """Get current task due date."""
        return self._task_due_date
    
    def set_task_due_date(self, value: Optional[datetime]):
        """Set task due date."""
        self._task_due_date = value
    
    def close(self):
        """Clean up resources."""
        if self._service:
            self._service.close()
    
    def __del__(self):
        """Destructor - ensure resources are cleaned up."""
        self.close()

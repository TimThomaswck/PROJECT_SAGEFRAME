"""Service layer for task management.

This module provides the TaskService class for CRUD operations on tasks.
Follows the same pattern as ProjectService from Story 2.1.
Includes support for task properties: priority and complexity.
"""

from datetime import datetime, timezone
from typing import Optional, List, Union

from pydantic import ValidationError
from sqlalchemy.orm.exc import DetachedInstanceError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.modules.tasks.models import Task, TaskSchema, TaskUpdateSchema, TaskPriority, TaskComplexity, TaskStatus, TaskDependencyType


class TaskService:
    """Service class for task CRUD operations.
    
    Provides methods for creating, reading, updating, and deleting tasks.
    Supports context manager pattern for automatic session cleanup.
    """
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize TaskService.
        
        Args:
            session: Optional SQLAlchemy session. Creates new if not provided.
        """
        self._session = session
        self._owns_session = session is None
        if self._owns_session:
            self._session = SessionLocal()
    
    @staticmethod
    def _ensure_timezone(dt: Optional[datetime]) -> Optional[datetime]:
        """Force naive datetimes to UTC-aware for consistent storage."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def _normalize_task_timezone(task: Task) -> Task:
        """Ensure task datetime fields carry tzinfo when loaded from SQLite."""
        if getattr(task, "start_date", None) is not None and task.start_date.tzinfo is None:
            task.start_date = task.start_date.replace(tzinfo=timezone.utc)
        if getattr(task, "end_date", None) is not None and task.end_date.tzinfo is None:
            task.end_date = task.end_date.replace(tzinfo=timezone.utc)
        if getattr(task, "due_date", None) is not None and task.due_date.tzinfo is None:
            task.due_date = task.due_date.replace(tzinfo=timezone.utc)
        return task
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
    
    def close(self):
        """Close the database session if owned by this service."""
        if self._owns_session and self._session:
            self._session.close()
            self._session = None
    
    @property
    def session(self) -> Session:
        """Get the database session."""
        if self._session is None:
            raise RuntimeError("Service session is closed")
        return self._session
    
    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        status: Union[TaskStatus, str] = TaskStatus.TODO,
        priority: Union[TaskPriority, str] = TaskPriority.MEDIUM,
        complexity: Union[TaskComplexity, str] = TaskComplexity.MODERATE,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        depends_on_task_id: Optional[int] = None,
        dependency_type: Optional[Union[TaskDependencyType, str]] = None,
    ) -> Task:
        """Create a new task.
        
        Args:
            title: Task title (required, non-empty)
            description: Optional task description
            due_date: Optional due date
            status: Task status (default: TODO)
            priority: Task priority level (default: MEDIUM)
            complexity: Task complexity level (default: MODERATE)
            project_id: Optional project association
            user_id: Optional user ID for multi-tenancy
            id: Optional ID for restoring deleted tasks (undo operations)
            
        Returns:
            Created Task object
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate input with Pydantic
            validated = TaskSchema(
                title=title,
                description=description,
                due_date=self._ensure_timezone(due_date),
                status=status,
                priority=priority,
                complexity=complexity,
                project_id=project_id,
                start_date=self._ensure_timezone(start_date),
                end_date=self._ensure_timezone(end_date),
                depends_on_task_id=depends_on_task_id,
                dependency_type=dependency_type,
            )
            
            # Create task with validated data, ensuring enum values are stored as strings
            task = Task(
                title=validated.title,
                description=validated.description,
                due_date=validated.due_date,
                status=validated.status.value if isinstance(validated.status, TaskStatus) else validated.status,
                priority=validated.priority.value if isinstance(validated.priority, TaskPriority) else validated.priority,
                complexity=validated.complexity.value if isinstance(validated.complexity, TaskComplexity) else validated.complexity,
                project_id=validated.project_id,
                start_date=validated.start_date,
                end_date=validated.end_date,
                depends_on_task_id=validated.depends_on_task_id,
                dependency_type=validated.dependency_type.value if isinstance(validated.dependency_type, TaskDependencyType) else validated.dependency_type,
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Set ID if provided (for undo operations)
            if id is not None:
                task.id = id
            
            self.session.add(task)
            self.session.commit()
            try:
                self.session.refresh(task)
            except DetachedInstanceError:
                # If the instance was detached, re-merge to keep return value usable
                task = self.session.merge(task)
            return self._normalize_task_timezone(task)
            
        except ValidationError as e:
            self.session.rollback()
            raise ValueError(str(e)) from e
        except Exception as e:
            self.session.rollback()
            raise
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID.
        
        Args:
            task_id: Task ID to retrieve
            
        Returns:
            Task object if found, None otherwise
        """
        task = self.session.query(Task).filter(Task.id == task_id).first()
        return self._normalize_task_timezone(task) if task else None
    
    def list_tasks(
        self,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[Union[TaskStatus, str]] = None
    ) -> List[Task]:
        """List tasks with optional filtering.
        
        Args:
            project_id: Filter by project (None = all projects)
            user_id: Filter by user (None = all users)
            status: Filter by status (None = all statuses)
            
        Returns:
            List of Task objects ordered by creation date (newest first)
        """
        query = self.session.query(Task)
        
        if project_id is not None:
            query = query.filter(Task.project_id == project_id)
        
        if user_id is not None:
            query = query.filter(Task.user_id == user_id)
        
        if status is not None:
            # Convert enum to string value for database query if status is an Enum member
            if isinstance(status, TaskStatus):
                status = status.value
            query = query.filter(Task.status == status)
        
        tasks = query.order_by(Task.created_at.desc()).all()
        return [self._normalize_task_timezone(t) for t in tasks]
    
    def list_standalone_tasks(self, user_id: Optional[int] = None) -> List[Task]:
        """List tasks not associated with any project.
        
        Args:
            user_id: Filter by user (None = all users)
            
        Returns:
            List of standalone Task objects
        """
        query = self.session.query(Task).filter(Task.project_id.is_(None))
        
        if user_id is not None:
            query = query.filter(Task.user_id == user_id)
        
        return query.order_by(Task.created_at.desc()).all()
    
    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        status: Optional[Union[TaskStatus, str]] = None,
        priority: Optional[Union[TaskPriority, str]] = None,
        complexity: Optional[Union[TaskComplexity, str]] = None,
        project_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        depends_on_task_id: Optional[int] = None,
        dependency_type: Optional[Union[TaskDependencyType, str]] = None,
    ) -> Optional[Task]:
        """Update a task.
        
        Only provided fields are updated (selective update).
        
        Args:
            task_id: Task ID to update
            title: New title (optional)
            description: New description (optional)
            due_date: New due date (optional)
            status: New status (optional)
            priority: New priority level (optional)
            complexity: New complexity level (optional)
            project_id: New project association (optional)
            
        Returns:
            Updated Task object if found, None if not found
            
        Raises:
            ValueError: If validation fails
        """
        task = self.get_task(task_id)
        if not task:
            return None

        # Capture pre-update values for downstream effects (e.g., gamification)
        old_status = task.status
        
        try:
            # Normalize enum inputs to strings to match string columns
            if isinstance(status, TaskStatus):
                status = status.value
            if isinstance(priority, TaskPriority):
                priority = priority.value
            if isinstance(complexity, TaskComplexity):
                complexity = complexity.value
            if isinstance(dependency_type, TaskDependencyType):
                dependency_type = dependency_type.value

            # Build update dict with only provided fields
            update_data = {}
            if title is not None:
                update_data['title'] = title
            if description is not None:
                update_data['description'] = description
            if due_date is not None:
                update_data['due_date'] = due_date
            if status is not None:
                update_data['status'] = status
            if priority is not None:
                update_data['priority'] = priority
            if complexity is not None:
                update_data['complexity'] = complexity
            if project_id is not None:
                update_data['project_id'] = project_id
            if start_date is not None:
                update_data['start_date'] = start_date
            if end_date is not None:
                update_data['end_date'] = end_date
            if depends_on_task_id is not None:
                update_data['depends_on_task_id'] = depends_on_task_id
            if dependency_type is not None:
                update_data['dependency_type'] = dependency_type
            
            # Validate with Pydantic
            if update_data:
                validated = TaskUpdateSchema(**update_data)
                
                # Apply validated updates
                if validated.title is not None:
                    task.title = validated.title
                if validated.description is not None:
                    task.description = validated.description
                if validated.due_date is not None:
                    task.due_date = validated.due_date
                if validated.status is not None:
                    task.status = validated.status
                if validated.priority is not None:
                    task.priority = validated.priority
                if validated.complexity is not None:
                    task.complexity = validated.complexity
                if validated.project_id is not None:
                    task.project_id = validated.project_id
                if validated.start_date is not None:
                    task.start_date = validated.start_date
                if validated.end_date is not None:
                    task.end_date = validated.end_date
                if validated.depends_on_task_id is not None:
                    task.depends_on_task_id = validated.depends_on_task_id
                if validated.dependency_type is not None:
                    task.dependency_type = validated.dependency_type.value if hasattr(validated.dependency_type, "value") else validated.dependency_type
                
                task.updated_at = datetime.now(timezone.utc)
            
            self.session.commit()
            try:
                self.session.refresh(task)
            except DetachedInstanceError:
                # If the instance was detached after commit, re-attach so callers get a live entity
                task = self.session.merge(task)

            # Award XP if task just transitioned to done (use updated complexity)
            self._handle_completion_progress(old_status, task.status, task.complexity)
            return self._normalize_task_timezone(task)
            
        except ValidationError as e:
            self.session.rollback()
            raise ValueError(str(e)) from e
        except Exception as e:
            self.session.rollback()
            raise

    def _handle_completion_progress(self, old_status, new_status, complexity: Optional[Union[TaskComplexity, str]]):
        """Trigger gamification XP award when a task is completed.

        Args:
            old_status: Status prior to update
            new_status: Status after update
            complexity: Task complexity used for XP calculation
        """
        try:
            old = old_status.value if isinstance(old_status, TaskStatus) else str(old_status)
            new = new_status.value if isinstance(new_status, TaskStatus) else str(new_status)
        except Exception:
            return None

        if old == TaskStatus.DONE.value:
            return None
        if new != TaskStatus.DONE.value:
            return None

        # Award XP using gamification service; ignore failures to avoid blocking task updates
        try:
            from app.modules.gamification.services import GamificationService

            with GamificationService() as service:
                return service.award_xp_for_task(complexity=complexity)
        except Exception:
            return None
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task.
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        try:
            self.session.delete(task)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise
    
    def get_tasks_by_project(self, project_id: int) -> List[Task]:
        """Get all tasks for a specific project.
        
        Args:
            project_id: Project ID to filter by
            
        Returns:
            List of Task objects for the project
        """
        return self.list_tasks(project_id=project_id)
    
    def count_tasks_by_project(self, project_id: int) -> int:
        """Count tasks for a specific project.
        
        Useful for checking if a project has tasks before deletion.
        
        Args:
            project_id: Project ID to count tasks for
            
        Returns:
            Number of tasks in the project
        """
        return self.session.query(Task).filter(Task.project_id == project_id).count()
    
    def list_tasks_by_priority(
        self,
        priority: Union[TaskPriority, str],
        project_id: Optional[int] = None
    ) -> List[Task]:
        """List tasks filtered by priority level.
        
        Args:
            priority: Priority level to filter by (TaskPriority enum or string)
            project_id: Optional project filter
            
        Returns:
            List of Task objects with specified priority
        """
        # Convert enum to string if needed, since Task.priority is String column
        if isinstance(priority, TaskPriority):
            priority = priority.value
        
        query = self.session.query(Task).filter(Task.priority == priority)
        
        if project_id is not None:
            query = query.filter(Task.project_id == project_id)
        
        return query.order_by(Task.created_at.desc()).all()
    
    def list_tasks_by_complexity(
        self,
        complexity: Union[TaskComplexity, str],
        project_id: Optional[int] = None
    ) -> List[Task]:
        """List tasks filtered by complexity level.
        
        Args:
            complexity: Complexity level to filter by (TaskComplexity enum or string)
            project_id: Optional project filter
            
        Returns:
            List of Task objects with specified complexity
        """
        # Convert enum to string if needed, since Task.complexity is String column
        if isinstance(complexity, TaskComplexity):
            complexity = complexity.value
        
        query = self.session.query(Task).filter(Task.complexity == complexity)
        
        if project_id is not None:
            query = query.filter(Task.project_id == project_id)
        
        return query.order_by(Task.created_at.desc()).all()
    
    def list_high_priority_tasks(self, project_id: Optional[int] = None) -> List[Task]:
        """Convenience method: list all high-priority tasks.
        
        Args:
            project_id: Optional project filter
            
        Returns:
            List of Task objects with HIGH priority
        """
        return self.list_tasks_by_priority(TaskPriority.HIGH, project_id)
    
    def list_complex_tasks(self, project_id: Optional[int] = None) -> List[Task]:
        """Convenience method: list all complex tasks.
        
        Args:
            project_id: Optional project filter
            
        Returns:
            List of Task objects with COMPLEX complexity
        """
        return self.list_tasks_by_complexity(TaskComplexity.COMPLEX, project_id)

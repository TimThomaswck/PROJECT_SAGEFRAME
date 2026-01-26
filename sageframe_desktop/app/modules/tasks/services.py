"""Service layer for task management.

This module provides the TaskService class for CRUD operations on tasks.
Follows the same pattern as ProjectService from Story 2.1.
Includes support for task properties: priority and complexity.
"""

from datetime import datetime, timezone
from typing import Optional, List, Union

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.modules.tasks.models import Task, TaskSchema, TaskUpdateSchema, TaskPriority, TaskComplexity, TaskStatus


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
        status: Union[TaskStatus, str] = "todo",
        priority: Union[TaskPriority, str] = "medium",
        complexity: Union[TaskComplexity, str] = "moderate",
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        id: Optional[int] = None
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
                due_date=due_date,
                status=status,
                priority=priority,
                complexity=complexity,
                project_id=project_id
            )
            
            # Create task with validated data
            task = Task(
                title=validated.title,
                description=validated.description,
                due_date=validated.due_date,
                status=validated.status,
                priority=validated.priority,
                complexity=validated.complexity,
                project_id=validated.project_id,
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Set ID if provided (for undo operations)
            if id is not None:
                task.id = id
            
            self.session.add(task)
            self.session.commit()
            self.session.refresh(task)
            return task
            
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
        return self.session.query(Task).filter(Task.id == task_id).first()
    
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
            # Convert enum to string if needed, since Task.status is now String column
            if isinstance(status, TaskStatus):
                status = status.value
            query = query.filter(Task.status == status)
        
        return query.order_by(Task.created_at.desc()).all()
    
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
        project_id: Optional[int] = None
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
        
        try:
            # Normalize enum inputs to strings to match string columns
            if isinstance(status, TaskStatus):
                status = status.value
            if isinstance(priority, TaskPriority):
                priority = priority.value
            if isinstance(complexity, TaskComplexity):
                complexity = complexity.value

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
                
                task.updated_at = datetime.now(timezone.utc)
            
            self.session.commit()
            self.session.refresh(task)
            return task
            
        except ValidationError as e:
            self.session.rollback()
            raise ValueError(str(e)) from e
        except Exception as e:
            self.session.rollback()
            raise
    
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

"""Data models for task functionality.

This module defines the SQLAlchemy ORM model and Pydantic schemas for tasks.
Tasks can be standalone or associated with a project via foreign key.
Includes task properties: priority and complexity.
"""
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List # Added List import

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.modules.projects.models import Project 

# Constants
MAX_TITLE_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 5000


# Enum classes for task properties
class TaskStatus(str, Enum):
    """Task status levels.
    
    - todo: Task is planned but not started
    - in_progress: Task is currently being worked on
    - done: Task is completed
    - blocked: Task is blocked by some external factor
    """
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"

VALID_STATUSES: List[str] = [status.value for status in TaskStatus]


class TaskPriority(str, Enum):
    """Task priority levels.
    
    - low: Low priority task
    - medium: Medium priority task
    - high: High priority task
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskComplexity(str, Enum):
    """Task complexity levels.
    
    - simple: Simple task, low effort
    - moderate: Moderate complexity, moderate effort
    - complex: Complex task, high effort
    """
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class Task(Base):
    """SQLAlchemy model for tasks.
    
    Stores task metadata and can be associated with a project.
    Includes priority and complexity properties.
    Follows snake_case naming convention as per architecture.
    """
    
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(MAX_TITLE_LENGTH), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default='todo')
    priority = Column(String(10), nullable=False, default='medium')
    complexity = Column(String(10), nullable=False, default='moderate')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    user_id = Column(Integer, nullable=True)  # Prepared for future multi-tenancy
    
    # Relationship to Project
    project = relationship("Project", back_populates="tasks")
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title!r}, status={self.status}, priority={self.priority}, complexity={self.complexity}, project_id={self.project_id})>"


class TaskSchema(BaseModel):
    """Pydantic schema for task creation/full validation.
    
    Validates task input before persisting to database.
    Columns are stored as strings; validators ensure allowed values.
    """
    
    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH, description="Task title")
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH, description="Optional task description")
    due_date: Optional[datetime] = Field(None, description="Optional due date")
    status: str = Field(default="todo", description="Task status")
    priority: str = Field(default="medium", description="Task priority level")
    complexity: str = Field(default="moderate", description="Task complexity level")
    project_id: Optional[int] = Field(None, description="Optional project association")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate task title is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Task title cannot be empty")
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description if provided."""
        if v is not None and isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v) -> str:
        """Validate status and return normalized string."""
        if isinstance(v, TaskStatus):
            return v.value
        if isinstance(v, str):
            v = v.lower()
            if v in {s.value for s in TaskStatus}:
                return v
            raise ValueError(f"Status must be one of: {', '.join([s.value for s in TaskStatus])}")
        raise ValueError("Status must be a string or TaskStatus enum")
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate due_date if provided."""
        # Accept any valid datetime, None is also valid
        return v
    
    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority(cls, v) -> str:
        """Validate priority and return normalized string."""
        if isinstance(v, TaskPriority):
            return v.value
        if isinstance(v, str):
            v = v.lower()
            if v in {p.value for p in TaskPriority}:
                return v
            raise ValueError(f"Priority must be one of: {', '.join([p.value for p in TaskPriority])}")
        raise ValueError("Priority must be a string or TaskPriority enum")
    
    @field_validator('complexity', mode='before')
    @classmethod
    def validate_complexity(cls, v) -> str:
        """Validate complexity and return normalized string."""
        if isinstance(v, TaskComplexity):
            return v.value
        if isinstance(v, str):
            v = v.lower()
            if v in {c.value for c in TaskComplexity}:
                return v
            raise ValueError(f"Complexity must be one of: {', '.join([c.value for c in TaskComplexity])}")
        raise ValueError("Complexity must be a string or TaskComplexity enum")
    
    model_config = ConfigDict(from_attributes=True)


class TaskUpdateSchema(BaseModel):
    """Pydantic schema for partial task updates.
    
    All fields are optional to allow selective updates.
    Stored values are strings; validators keep them within allowed sets.
    """
    
    title: Optional[str] = Field(None, min_length=1, max_length=MAX_TITLE_LENGTH, description="Task title")
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH, description="Optional task description")
    due_date: Optional[datetime] = Field(None, description="Optional due date")
    status: Optional[str] = Field(None, description="Task status")
    priority: Optional[str] = Field(None, description="Task priority level")
    complexity: Optional[str] = Field(None, description="Task complexity level")
    project_id: Optional[int] = Field(None, description="Optional project association")

    @field_validator('status', mode='before')
    @classmethod
    def validate_status_update(cls, v) -> Optional[str]:
        """Validate optional status and return normalized string."""
        if v is None:
            return None
        if isinstance(v, TaskStatus):
            return v.value
        if isinstance(v, str):
            v = v.lower()
            if v in {s.value for s in TaskStatus}:
                return v
            raise ValueError(f"Status must be one of: {', '.join([s.value for s in TaskStatus])}")
        raise ValueError("Status must be a string or TaskStatus enum")

    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority_update(cls, v) -> Optional[str]:
        """Validate optional priority and return normalized string."""
        if v is None:
            return None
        if isinstance(v, TaskPriority):
            return v.value
        if isinstance(v, str):
            v = v.lower()
            if v in {p.value for p in TaskPriority}:
                return v
            raise ValueError(f"Priority must be one of: {', '.join([p.value for p in TaskPriority])}")
        raise ValueError("Priority must be a string or TaskPriority enum")

    @field_validator('complexity', mode='before')
    @classmethod
    def validate_complexity_update(cls, v) -> Optional[str]:
        """Validate optional complexity and return normalized string."""
        if v is None:
            return None
        if isinstance(v, TaskComplexity):
            return v.value
        if isinstance(v, str):
            v = v.lower()
            if v in {c.value for c in TaskComplexity}:
                return v
            raise ValueError(f"Complexity must be one of: {', '.join([c.value for c in TaskComplexity])}")
        raise ValueError("Complexity must be a string or TaskComplexity enum")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate task title if provided."""
        if v is not None:
            if not v.strip():
                raise ValueError("Task title cannot be empty")
            return v.strip()
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description if provided."""
        if v is not None and isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v) -> Optional[TaskStatus]:
        """Validate and convert status to TaskStatus enum if provided."""
        if v is None:
            return None
        if isinstance(v, TaskStatus):
            return v
        if isinstance(v, str):
            try:
                return TaskStatus(v.lower())
            except ValueError:
                raise ValueError(f"Status must be one of: {', '.join([s.value for s in TaskStatus])}")
        raise ValueError("Status must be a string or TaskStatus enum")
    
    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority(cls, v) -> Optional[TaskPriority]:
        """Validate and convert priority to TaskPriority enum if provided."""
        if v is None:
            return None
        if isinstance(v, TaskPriority):
            return v
        if isinstance(v, str):
            try:
                return TaskPriority(v.lower())
            except ValueError:
                raise ValueError(f"Priority must be one of: {', '.join([p.value for p in TaskPriority])}")
        raise ValueError("Priority must be a string or TaskPriority enum")
    
    @field_validator('complexity', mode='before')
    @classmethod
    def validate_complexity(cls, v) -> Optional[TaskComplexity]:
        """Validate and convert complexity to TaskComplexity enum if provided."""
        if v is None:
            return None
        if isinstance(v, TaskComplexity):
            return v
        if isinstance(v, str):
            try:
                return TaskComplexity(v.lower())
            except ValueError:
                raise ValueError(f"Complexity must be one of: {', '.join([c.value for c in TaskComplexity])}")
        raise ValueError("Complexity must be a string or TaskComplexity enum")
    
    model_config = ConfigDict(from_attributes=True)


# Ensure SQLAlchemy registry loads the related Project model for relationship resolution
from app.modules.projects.models import Project  # noqa: F401


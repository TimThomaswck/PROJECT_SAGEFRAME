"""Data models for project functionality.

This module defines the SQLAlchemy ORM model and Pydantic schema for projects.
Projects are the top-level organizational unit for tasks in Sageframe.
"""
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
if TYPE_CHECKING:
    from app.modules.tasks.models import Task

# Constants
MAX_DESCRIPTION_LENGTH = 5000


class Project(Base):
    """SQLAlchemy model for projects.
    
    Stores project metadata and serves as the top-level organizational unit.
    Follows snake_case naming convention as per architecture.
    """
    
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=False)  # Project name
    description = Column(Text, nullable=True)  # Optional project description
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    user_id = Column(Integer, nullable=True)  # Prepared for future multi-tenancy (no FK yet)
    
    # Relationship for associated tasks (Story 2.2)
    # Note: SET NULL on delete to keep tasks as standalone when project deleted
    tasks = relationship("Task", back_populates="project", cascade="save-update, merge", passive_deletes=True)
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name!r}, created_at={self.created_at})>"


class ProjectSchema(BaseModel):
    """Pydantic schema for project data validation.
    
    Validates project input before persisting to database.
    Hybrid approach: SQLAlchemy + Pydantic as per architecture.
    """
    
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH, description="Optional project description")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description if provided."""
        if v is not None and isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v
    
    model_config = ConfigDict(from_attributes=True)

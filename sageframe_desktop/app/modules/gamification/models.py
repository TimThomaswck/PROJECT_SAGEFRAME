"""SQLAlchemy models for gamification system (XP, levels, progress).

This module defines the UserProgress model for tracking user gamification metrics.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.orm import validates

from app.database import Base


class UserProgress(Base):
    """User progress tracking for gamification.
    
    Stores XP, current level, and progress metrics for a user.
    Currently supports single-user mode (user_id=1).
    """
    
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True, default=1)
    current_xp = Column(Integer, nullable=False, default=0)
    current_level = Column(Integer, nullable=False, default=1)
    total_tasks_completed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    @validates('current_xp')
    def validate_xp(self, key, value):
        """Ensure XP is non-negative."""
        if value < 0:
            raise ValueError("XP cannot be negative")
        return value
    
    @validates('current_level')
    def validate_level(self, key, value):
        """Ensure level is at least 1."""
        if value < 1:
            raise ValueError("Level must be at least 1")
        return value
    
    @validates('total_tasks_completed')
    def validate_tasks_completed(self, key, value):
        """Ensure task count is non-negative."""
        if value < 0:
            raise ValueError("Tasks completed cannot be negative")
        return value
    
    def __repr__(self):
        return f"<UserProgress(user_id={self.user_id}, level={self.current_level}, xp={self.current_xp})>"

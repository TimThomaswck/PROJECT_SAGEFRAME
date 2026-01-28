"""Habit tracking data models.

Story 7.1: Simple Habit Tracker

Data models for habit and habit completion tracking.
Provides foundation for daily habit tracking with weekly/monthly progress.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Habit(Base):
    """Habit model for tracking user habits.
    
    Represents a single habit that a user wants to track.
    Supports daily completion marking and progress tracking.
    
    Attributes:
        id: Primary key
        name: Habit name (required, max 255 chars)
        description: Optional habit description
        created_at: Creation timestamp (UTC)
        updated_at: Last update timestamp (UTC)
        completions: Relationship to HabitCompletion records
    
    Story 7.1 AC1: Support creating and naming new habits
    """
    __tablename__ = 'habits'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, 
                       default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                       default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship
    completions = relationship(
        'HabitCompletion',
        back_populates='habit',
        cascade='all, delete-orphan',
        lazy='joined'
    )
    
    def __repr__(self):
        return f"<Habit(id={self.id}, name='{self.name}')>"
    
    def __str__(self):
        return self.name
    
    def get_completion_for_date(self, completion_date):
        """Get completion record for a specific date.
        
        Args:
            completion_date: datetime.date object
            
        Returns:
            HabitCompletion or None
        """
        date_str = completion_date.isoformat() if hasattr(completion_date, 'isoformat') else str(completion_date)
        return next(
            (c for c in self.completions if c.completion_date == date_str),
            None
        )
    
    def is_completed_on(self, completion_date):
        """Check if habit is completed on a specific date.
        
        Args:
            completion_date: datetime.date object
            
        Returns:
            bool: True if completed, False otherwise
        """
        return self.get_completion_for_date(completion_date) is not None


class HabitCompletion(Base):
    """Habit completion tracking model.
    
    Represents a single completion of a habit on a specific date.
    Uses unique constraint to prevent duplicate completions for same day.
    
    Attributes:
        id: Primary key
        habit_id: Foreign key to habits table
        completion_date: ISO 8601 date string (YYYY-MM-DD)
        created_at: Creation timestamp (UTC)
        habit: Relationship to Habit model
    
    Story 7.1 AC2: Support marking habit as complete with single click
    """
    __tablename__ = 'habit_completions'
    
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey('habits.id'), nullable=False)
    completion_date = Column(String(10), nullable=False)  # ISO 8601 format: YYYY-MM-DD
    created_at = Column(DateTime(timezone=True), nullable=False,
                       default=lambda: datetime.now(timezone.utc))
    
    # Relationship
    habit = relationship('Habit', back_populates='completions')
    
    # Unique constraint: prevent duplicate completions for same habit on same day
    __table_args__ = (
        UniqueConstraint('habit_id', 'completion_date', name='unique_habit_completion'),
    )
    
    def __repr__(self):
        return f"<HabitCompletion(habit_id={self.habit_id}, date={self.completion_date})>"
    
    def __str__(self):
        return f"Completed on {self.completion_date}"

"""Habit tracking service.

Story 7.1: Simple Habit Tracker

Service for managing habits and daily completions.
Provides CRUD operations and completion tracking functionality.
"""

from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.modules.habits.models import Habit, HabitCompletion


class HabitService:
    """Service for habit tracking operations.
    
    Manages habit creation, deletion, and daily completion marking.
    Handles progress calculation and completion history.
    
    Story 7.1 AC1: Create and name new habits
    Story 7.1 AC2: Mark habits as complete with single click
    Story 7.1 AC3: View progress for current week/month
    """
    
    def __init__(self, session: Session):
        """Initialize habit service.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    # ==================== HABIT CRUD ====================
    
    def create_habit(self, name: str, description: str = None) -> Habit:
        """Create a new habit.
        
        Story 7.1 AC1: Create and name new habits
        
        Args:
            name: Habit name (required, validated)
            description: Optional habit description
            
        Returns:
            Habit: Created habit object
            
        Raises:
            ValueError: If name is empty or exceeds max length
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Habit name cannot be empty")
        
        if len(name) > 255:
            raise ValueError("Habit name must be 255 characters or less")
        
        # Create habit
        habit = Habit(
            name=name.strip(),
            description=description.strip() if description else None
        )
        
        self.session.add(habit)
        self.session.commit()
        
        return habit
    
    def get_habit(self, habit_id: int) -> Optional[Habit]:
        """Get a habit by ID.
        
        Args:
            habit_id: ID of the habit
            
        Returns:
            Habit or None if not found
        """
        return self.session.query(Habit).filter_by(id=habit_id).first()
    
    def get_all_habits(self) -> List[Habit]:
        """Get all habits.
        
        Story 7.1 AC3: View habits
        
        Returns:
            List of all habits
        """
        return self.session.query(Habit).order_by(Habit.created_at).all()
    
    def update_habit(self, habit_id: int, name: str = None, description: str = None) -> Optional[Habit]:
        """Update a habit.
        
        Args:
            habit_id: ID of habit to update
            name: New habit name (optional)
            description: New description (optional)
            
        Returns:
            Updated habit or None if not found
            
        Raises:
            ValueError: If validation fails
        """
        habit = self.get_habit(habit_id)
        if not habit:
            return None
        
        if name is not None:
            if not name or not name.strip():
                raise ValueError("Habit name cannot be empty")
            if len(name) > 255:
                raise ValueError("Habit name must be 255 characters or less")
            habit.name = name.strip()
        
        if description is not None:
            habit.description = description.strip() if description else None
        
        self.session.commit()
        return habit
    
    def delete_habit(self, habit_id: int) -> bool:
        """Delete a habit and all its completions.
        
        Args:
            habit_id: ID of habit to delete
            
        Returns:
            True if deleted, False if not found
        """
        habit = self.get_habit(habit_id)
        if not habit:
            return False
        
        self.session.delete(habit)
        self.session.commit()
        return True
    
    # ==================== COMPLETION TRACKING ====================
    
    def mark_complete(self, habit_id: int, completion_date: date = None) -> bool:
        """Mark a habit as complete for a specific date.
        
        Story 7.1 AC2: Mark habit as complete with single click
        
        Args:
            habit_id: ID of the habit
            completion_date: Date to mark complete (defaults to today)
            
        Returns:
            True if marked, False if already marked or habit not found
            
        Raises:
            ValueError: If habit not found
        """
        # Validate habit exists
        habit = self.get_habit(habit_id)
        if not habit:
            raise ValueError(f"Habit with ID {habit_id} not found")
        
        # Default to today
        if completion_date is None:
            completion_date = date.today()
        
        # Convert to ISO string format
        date_str = completion_date.isoformat() if hasattr(completion_date, 'isoformat') else str(completion_date)
        
        # Check if already completed
        existing = self.session.query(HabitCompletion).filter_by(
            habit_id=habit_id,
            completion_date=date_str
        ).first()
        
        if existing:
            return False  # Already marked
        
        # Create completion record
        try:
            completion = HabitCompletion(
                habit_id=habit_id,
                completion_date=date_str
            )
            self.session.add(completion)
            self.session.commit()
            return True
        except IntegrityError:
            self.session.rollback()
            return False  # Duplicate constraint
    
    def unmark_complete(self, habit_id: int, completion_date: date = None) -> bool:
        """Unmark a habit completion for a specific date.
        
        Args:
            habit_id: ID of the habit
            completion_date: Date to unmark (defaults to today)
            
        Returns:
            True if unmarked, False if not found
        """
        # Default to today
        if completion_date is None:
            completion_date = date.today()
        
        # Convert to ISO string format
        date_str = completion_date.isoformat() if hasattr(completion_date, 'isoformat') else str(completion_date)
        
        # Find and delete completion
        completion = self.session.query(HabitCompletion).filter_by(
            habit_id=habit_id,
            completion_date=date_str
        ).first()
        
        if not completion:
            return False
        
        self.session.delete(completion)
        self.session.commit()
        return True
    
    def is_completed(self, habit_id: int, completion_date: date = None) -> bool:
        """Check if habit is completed on a specific date.
        
        Args:
            habit_id: ID of the habit
            completion_date: Date to check (defaults to today)
            
        Returns:
            True if completed, False otherwise
        """
        # Default to today
        if completion_date is None:
            completion_date = date.today()
        
        # Convert to ISO string format
        date_str = completion_date.isoformat() if hasattr(completion_date, 'isoformat') else str(completion_date)
        
        return self.session.query(HabitCompletion).filter_by(
            habit_id=habit_id,
            completion_date=date_str
        ).first() is not None
    
    # ==================== PROGRESS TRACKING ====================
    
    def get_week_completions(self, habit_id: int, target_date: date = None) -> Tuple[List[date], List[bool]]:
        """Get week's completions for a habit.
        
        Story 7.1 AC3: View progress for current week
        
        Returns week starting on Monday.
        
        Args:
            habit_id: ID of the habit
            target_date: Date within the target week (defaults to today)
            
        Returns:
            Tuple of (dates_list, completion_list)
            - dates_list: List of 7 dates for the week (Monday-Sunday)
            - completion_list: List of booleans for each date
        """
        if target_date is None:
            target_date = date.today()
        
        # Get Monday of the week
        monday = target_date - timedelta(days=target_date.weekday())
        
        # Get all dates for the week
        week_dates = [monday + timedelta(days=i) for i in range(7)]
        
        # Get completions for this week
        completions = self.session.query(HabitCompletion).filter(
            HabitCompletion.habit_id == habit_id,
            HabitCompletion.completion_date >= monday.isoformat(),
            HabitCompletion.completion_date <= (monday + timedelta(days=6)).isoformat()
        ).all()
        
        # Build completion lookup
        completion_dates = {c.completion_date for c in completions}
        
        # Map dates to boolean status
        completion_status = [date_obj.isoformat() in completion_dates for date_obj in week_dates]
        
        return week_dates, completion_status
    
    def get_month_completions(self, habit_id: int, target_date: date = None) -> Tuple[List[date], List[bool]]:
        """Get month's completions for a habit.
        
        Story 7.1 AC3: View progress for current month
        
        Args:
            habit_id: ID of the habit
            target_date: Date within the target month (defaults to today)
            
        Returns:
            Tuple of (dates_list, completion_list)
            - dates_list: List of dates for the month
            - completion_list: List of booleans for each date
        """
        if target_date is None:
            target_date = date.today()
        
        # Get first day of month
        first_day = date(target_date.year, target_date.month, 1)
        
        # Get last day of month
        if target_date.month == 12:
            last_day = date(target_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(target_date.year, target_date.month + 1, 1) - timedelta(days=1)
        
        # Get all dates for the month
        month_dates = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
        
        # Get completions for this month
        completions = self.session.query(HabitCompletion).filter(
            HabitCompletion.habit_id == habit_id,
            HabitCompletion.completion_date >= first_day.isoformat(),
            HabitCompletion.completion_date <= last_day.isoformat()
        ).all()
        
        # Build completion lookup
        completion_dates = {c.completion_date for c in completions}
        
        # Map dates to boolean status
        completion_status = [date_obj.isoformat() in completion_dates for date_obj in month_dates]
        
        return month_dates, completion_status
    
    def get_completion_count(self, habit_id: int, start_date: date = None, end_date: date = None) -> int:
        """Get count of completions within date range.
        
        Args:
            habit_id: ID of the habit
            start_date: Start of range (defaults to start of month)
            end_date: End of range (defaults to today)
            
        Returns:
            Number of completions
        """
        if end_date is None:
            end_date = date.today()
        
        if start_date is None:
            start_date = date(end_date.year, end_date.month, 1)
        
        return self.session.query(HabitCompletion).filter(
            HabitCompletion.habit_id == habit_id,
            HabitCompletion.completion_date >= start_date.isoformat(),
            HabitCompletion.completion_date <= end_date.isoformat()
        ).count()
    
    def get_all_completions(self, habit_id: int, start_date: date = None, end_date: date = None) -> List[HabitCompletion]:
        """Get all completions for a habit within date range.
        
        Args:
            habit_id: ID of the habit
            start_date: Start of range
            end_date: End of range
            
        Returns:
            List of HabitCompletion objects
        """
        query = self.session.query(HabitCompletion).filter_by(habit_id=habit_id)
        
        if start_date:
            query = query.filter(HabitCompletion.completion_date >= start_date.isoformat())
        
        if end_date:
            query = query.filter(HabitCompletion.completion_date <= end_date.isoformat())
        
        return query.order_by(HabitCompletion.completion_date).all()

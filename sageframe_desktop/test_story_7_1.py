"""Test suite for Story 7.1: Simple Habit Tracker

Tests all acceptance criteria:
- AC1: Create and name new habits
- AC2: Mark habits as complete with single click
- AC3: View progress for current week/month
"""

import pytest
from datetime import date, timedelta, datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.database import Base
from app.modules.habits.models import Habit, HabitCompletion
from app.modules.habits.service import HabitService


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def habit_service(db_session):
    """Create habit service with in-memory database."""
    return HabitService(db_session)


class TestAC1HabitCreation:
    """Test AC1: Create and name new habits."""
    
    def test_create_habit_basic(self, habit_service):
        """AC1: Can create a new habit with name."""
        habit = habit_service.create_habit("Morning Exercise")
        
        assert habit is not None
        assert habit.id is not None
        assert habit.name == "Morning Exercise"
        assert habit.description is None
        assert habit.created_at is not None
    
    def test_create_habit_with_description(self, habit_service):
        """AC1: Can create habit with name and description."""
        habit = habit_service.create_habit(
            "Morning Exercise",
            "30 minutes of cardio"
        )
        
        assert habit.name == "Morning Exercise"
        assert habit.description == "30 minutes of cardio"
    
    def test_create_habit_empty_name_fails(self, habit_service):
        """AC1: Cannot create habit with empty name."""
        with pytest.raises(ValueError, match="empty"):
            habit_service.create_habit("")
    
    def test_create_habit_whitespace_name_fails(self, habit_service):
        """AC1: Cannot create habit with only whitespace."""
        with pytest.raises(ValueError, match="empty"):
            habit_service.create_habit("   ")
    
    def test_create_habit_name_too_long_fails(self, habit_service):
        """AC1: Cannot create habit with name > 255 chars."""
        long_name = "x" * 256
        with pytest.raises(ValueError, match="255"):
            habit_service.create_habit(long_name)
    
    def test_create_habit_name_max_length(self, habit_service):
        """AC1: Can create habit with name = 255 chars."""
        max_name = "x" * 255
        habit = habit_service.create_habit(max_name)
        
        assert habit.name == max_name
        assert len(habit.name) == 255
    
    def test_create_multiple_habits(self, habit_service):
        """AC1: Can create multiple different habits."""
        habit1 = habit_service.create_habit("Exercise")
        habit2 = habit_service.create_habit("Read")
        habit3 = habit_service.create_habit("Meditate")
        
        assert habit1.id != habit2.id
        assert habit2.id != habit3.id
        
        all_habits = habit_service.get_all_habits()
        assert len(all_habits) == 3
    
    def test_habit_name_whitespace_stripped(self, habit_service):
        """AC1: Habit name whitespace is trimmed."""
        habit = habit_service.create_habit("  Morning Exercise  ")
        
        assert habit.name == "Morning Exercise"
    
    def test_get_habit_by_id(self, habit_service):
        """AC1: Can retrieve habit by ID."""
        created = habit_service.create_habit("Test Habit")
        retrieved = habit_service.get_habit(created.id)
        
        assert retrieved.id == created.id
        assert retrieved.name == "Test Habit"
    
    def test_get_nonexistent_habit_returns_none(self, habit_service):
        """AC1: Getting non-existent habit returns None."""
        result = habit_service.get_habit(999)
        assert result is None
    
    def test_get_all_habits_empty(self, habit_service):
        """AC1: Can retrieve empty habit list."""
        habits = habit_service.get_all_habits()
        assert habits == []
    
    def test_update_habit_name(self, habit_service):
        """AC1: Can update habit name."""
        habit = habit_service.create_habit("Old Name")
        updated = habit_service.update_habit(habit.id, name="New Name")
        
        assert updated.name == "New Name"
        assert updated.id == habit.id
    
    def test_update_habit_description(self, habit_service):
        """AC1: Can update habit description."""
        habit = habit_service.create_habit("Exercise")
        updated = habit_service.update_habit(
            habit.id,
            description="30 min daily"
        )
        
        assert updated.description == "30 min daily"
    
    def test_delete_habit(self, habit_service):
        """AC1: Can delete a habit."""
        habit = habit_service.create_habit("Test")
        result = habit_service.delete_habit(habit.id)
        
        assert result is True
        assert habit_service.get_habit(habit.id) is None
    
    def test_delete_nonexistent_habit_returns_false(self, habit_service):
        """AC1: Deleting non-existent habit returns False."""
        result = habit_service.delete_habit(999)
        assert result is False


class TestAC2HabitCompletion:
    """Test AC2: Mark habits as complete with single click."""
    
    def test_mark_habit_complete_today(self, habit_service):
        """AC2: Can mark habit complete for today."""
        habit = habit_service.create_habit("Exercise")
        result = habit_service.mark_complete(habit.id)
        
        assert result is True
        assert habit_service.is_completed(habit.id) is True
    
    def test_mark_habit_complete_specific_date(self, habit_service):
        """AC2: Can mark habit complete for specific date."""
        habit = habit_service.create_habit("Exercise")
        target_date = date(2026, 1, 15)
        
        result = habit_service.mark_complete(habit.id, target_date)
        
        assert result is True
        assert habit_service.is_completed(habit.id, target_date) is True
    
    def test_mark_same_habit_twice_fails(self, habit_service):
        """AC2: Cannot mark same habit twice for same day."""
        habit = habit_service.create_habit("Exercise")
        first = habit_service.mark_complete(habit.id)
        second = habit_service.mark_complete(habit.id)
        
        assert first is True
        assert second is False  # Already marked
    
    def test_mark_different_dates_succeeds(self, habit_service):
        """AC2: Can mark habit complete on different dates."""
        habit = habit_service.create_habit("Exercise")
        date1 = date(2026, 1, 15)
        date2 = date(2026, 1, 16)
        
        result1 = habit_service.mark_complete(habit.id, date1)
        result2 = habit_service.mark_complete(habit.id, date2)
        
        assert result1 is True
        assert result2 is True
    
    def test_mark_complete_nonexistent_habit_raises(self, habit_service):
        """AC2: Marking non-existent habit raises ValueError."""
        with pytest.raises(ValueError):
            habit_service.mark_complete(999)
    
    def test_unmark_complete(self, habit_service):
        """AC2: Can unmark habit completion."""
        habit = habit_service.create_habit("Exercise")
        habit_service.mark_complete(habit.id)
        
        result = habit_service.unmark_complete(habit.id)
        
        assert result is True
        assert habit_service.is_completed(habit.id) is False
    
    def test_unmark_incomplete_returns_false(self, habit_service):
        """AC2: Unmarking incomplete habit returns False."""
        habit = habit_service.create_habit("Exercise")
        result = habit_service.unmark_complete(habit.id)
        
        assert result is False
    
    def test_toggle_completion(self, habit_service):
        """AC2: Can toggle habit completion."""
        habit = habit_service.create_habit("Exercise")
        
        # Initially not complete
        assert habit_service.is_completed(habit.id) is False
        
        # Mark complete
        habit_service.mark_complete(habit.id)
        assert habit_service.is_completed(habit.id) is True
        
        # Unmark
        habit_service.unmark_complete(habit.id)
        assert habit_service.is_completed(habit.id) is False
    
    def test_mark_multiple_habits_same_day(self, habit_service):
        """AC2: Can mark different habits complete on same day."""
        habit1 = habit_service.create_habit("Exercise")
        habit2 = habit_service.create_habit("Read")
        
        result1 = habit_service.mark_complete(habit1.id)
        result2 = habit_service.mark_complete(habit2.id)
        
        assert result1 is True
        assert result2 is True
        assert habit_service.is_completed(habit1.id) is True
        assert habit_service.is_completed(habit2.id) is True


class TestAC3ProgressTracking:
    """Test AC3: View progress for current week/month."""
    
    def test_get_week_completions(self, habit_service):
        """AC3: Can get week's completions for habit."""
        habit = habit_service.create_habit("Exercise")
        
        # Mark some days complete this week
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        
        habit_service.mark_complete(habit.id, monday)
        habit_service.mark_complete(habit.id, monday + timedelta(days=1))
        
        week_dates, completions = habit_service.get_week_completions(habit.id, today)
        
        assert len(week_dates) == 7
        assert len(completions) == 7
        assert completions[0] is True  # Monday
        assert completions[1] is True  # Tuesday
        assert completions[2] is False  # Wednesday
    
    def test_get_week_completions_empty(self, habit_service):
        """AC3: Get week with no completions."""
        habit = habit_service.create_habit("Exercise")
        
        week_dates, completions = habit_service.get_week_completions(habit.id)
        
        assert len(week_dates) == 7
        assert all(c is False for c in completions)
    
    def test_get_month_completions(self, habit_service):
        """AC3: Can get month's completions for habit."""
        habit = habit_service.create_habit("Exercise")
        
        # Mark some days complete this month
        habit_service.mark_complete(habit.id, date(2026, 1, 15))
        habit_service.mark_complete(habit.id, date(2026, 1, 16))
        habit_service.mark_complete(habit.id, date(2026, 1, 20))
        
        month_dates, completions = habit_service.get_month_completions(
            habit.id,
            date(2026, 1, 15)
        )
        
        # January 2026 has 31 days
        assert len(month_dates) == 31
        assert len(completions) == 31
        
        # Check specific days (0-indexed)
        assert completions[14] is True  # Day 15
        assert completions[15] is True  # Day 16
        assert completions[19] is True  # Day 20
        assert completions[0] is False  # Day 1
    
    def test_get_month_completions_short_month(self, habit_service):
        """AC3: Get month with less than 31 days."""
        habit = habit_service.create_habit("Exercise")
        
        # February 2026 has 28 days
        month_dates, completions = habit_service.get_month_completions(
            habit.id,
            date(2026, 2, 15)
        )
        
        assert len(month_dates) == 28
        assert len(completions) == 28
    
    def test_get_completion_count(self, habit_service):
        """AC3: Can count completions in date range."""
        habit = habit_service.create_habit("Exercise")
        
        # Mark several days
        habit_service.mark_complete(habit.id, date(2026, 1, 5))
        habit_service.mark_complete(habit.id, date(2026, 1, 10))
        habit_service.mark_complete(habit.id, date(2026, 1, 15))
        
        count = habit_service.get_completion_count(
            habit.id,
            date(2026, 1, 1),
            date(2026, 1, 31)
        )
        
        assert count == 3
    
    def test_get_completion_count_empty_range(self, habit_service):
        """AC3: Count completions in empty range."""
        habit = habit_service.create_habit("Exercise")
        
        count = habit_service.get_completion_count(
            habit.id,
            date(2026, 1, 1),
            date(2026, 1, 5)
        )
        
        assert count == 0
    
    def test_get_all_completions(self, habit_service):
        """AC3: Can get all completions for habit."""
        habit = habit_service.create_habit("Exercise")
        
        dates = [date(2026, 1, 5), date(2026, 1, 10), date(2026, 1, 15)]
        for d in dates:
            habit_service.mark_complete(habit.id, d)
        
        completions = habit_service.get_all_completions(habit.id)
        
        assert len(completions) == 3
        assert all(c.habit_id == habit.id for c in completions)


class TestHabitModel:
    """Test Habit model functionality."""
    
    def test_habit_creation_timestamps(self, db_session):
        """Habit model has proper timestamps."""
        habit = Habit(name="Test")
        db_session.add(habit)
        db_session.commit()
        
        assert habit.created_at is not None
        assert habit.updated_at is not None
        # SQLite returns naive datetime, but we store as timezone-aware in code
    
    def test_habit_repr(self, habit_service):
        """Habit model string representation."""
        habit = habit_service.create_habit("Test Habit")
        
        repr_str = repr(habit)
        assert "Habit" in repr_str
        assert "Test Habit" in repr_str
    
    def test_habit_relationship_to_completions(self, habit_service, db_session):
        """Habit has relationship to completions."""
        habit = habit_service.create_habit("Exercise")
        habit_service.mark_complete(habit.id)
        habit_service.mark_complete(habit.id, date.today() - timedelta(days=1))
        
        # Refresh to ensure relationship
        db_session.refresh(habit)
        
        assert len(habit.completions) == 2
        assert all(c.habit_id == habit.id for c in habit.completions)


class TestHabitCompletionModel:
    """Test HabitCompletion model functionality."""
    
    def test_completion_unique_constraint(self, db_session):
        """Unique constraint on habit_id + completion_date."""
        from app.database import Base
        Base.metadata.create_all(bind=db_session.bind)
        
        habit = Habit(name="Test")
        db_session.add(habit)
        db_session.commit()
        
        # Create first completion
        completion1 = HabitCompletion(
            habit_id=habit.id,
            completion_date="2026-01-15"
        )
        db_session.add(completion1)
        db_session.commit()
        
        # Try to create duplicate
        completion2 = HabitCompletion(
            habit_id=habit.id,
            completion_date="2026-01-15"
        )
        db_session.add(completion2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_completion_cascade_delete(self, habit_service, db_session):
        """Deleting habit cascades to completions."""
        habit = habit_service.create_habit("Exercise")
        habit_service.mark_complete(habit.id)
        habit_service.mark_complete(habit.id, date.today() - timedelta(days=1))
        
        habit_id = habit.id
        habit_service.delete_habit(habit_id)
        
        completions = db_session.query(HabitCompletion).filter_by(
            habit_id=habit_id
        ).all()
        
        assert len(completions) == 0


class TestIntegration:
    """Integration tests for habit tracking workflow."""
    
    def test_full_habit_workflow(self, habit_service):
        """Complete workflow: create, mark, track progress."""
        # Create habit
        habit = habit_service.create_habit("Morning Exercise", "30 minutes")
        assert habit.id is not None
        
        # Mark complete for several days
        for i in range(5):
            target_date = date.today() - timedelta(days=i)
            habit_service.mark_complete(habit.id, target_date)
        
        # View progress - using month view to ensure all dates are captured
        month_dates, month_completions = habit_service.get_month_completions(habit.id)
        
        # Should have exactly 5 completions
        completed_count = sum(1 for c in month_completions if c)
        assert completed_count == 5
        
        # Get completion count
        count = habit_service.get_completion_count(habit.id)
        assert count == 5
    
    def test_multiple_habits_independent(self, habit_service):
        """Multiple habits are independent."""
        habit1 = habit_service.create_habit("Exercise")
        habit2 = habit_service.create_habit("Read")
        
        # Mark first habit complete
        habit_service.mark_complete(habit1.id)
        
        # Second habit should not be marked
        assert habit_service.is_completed(habit1.id) is True
        assert habit_service.is_completed(habit2.id) is False
    
    def test_habit_persistence(self, habit_service):
        """Habits persist across retrievals."""
        # Create and mark
        habit = habit_service.create_habit("Test")
        original_id = habit.id
        habit_service.mark_complete(habit.id)
        
        # Retrieve again
        retrieved = habit_service.get_habit(original_id)
        assert retrieved.id == original_id
        assert habit_service.is_completed(retrieved.id) is True

# Story 7.1: Simple Habit Tracker

Status: ready-for-dev

## Epic Context

**Epic 7: Focus and Well-being**

Users can improve their focus and build positive routines through integrated tools that support focused work sessions and simple habit tracking.

This story implements basic habit tracking with daily checkmarks.

## Story

As a user,
I want to track simple habits with daily checkmarks,
so that I can build positive routines.

## Acceptance Criteria

1. **Given** I am in the habit tracking section, **When** I create a new habit, **Then** I can create and name a new habit.

2. **Given** a habit exists, **When** I complete the habit for the day, **Then** I can mark it as complete with a single click.

3. **Given** a habit exists, **When** I view my habits, **Then** I can see my progress for the current week/month.

4. (Note: No complex streak math or analytics are included in this story).

## Business Value & Context

**Primary User Need:** Users want a simple way to build positive daily routines without complex tracking or analysis.

**Why This Matters:**
- Supports well-being and personal growth
- Simple daily rituals improve consistency
- Visual progress (checkmarks) provides motivation
- Aligns with "empathetic co-pilot" philosophy (supportive, not judgmental)

**Related FRs:**
- FR37: Simple habit tracker with daily checkmarks

## Tasks / Subtasks

- [ ] Design habit data model (AC: #1, #2)
  - [ ] Create `habits` table (id, name, created_at)
  - [ ] Create `habit_completions` table (id, habit_id, completion_date)
  - [ ] Add Alembic migration
  
- [ ] Implement habit CRUD service (AC: #1)
  - [ ] Create `HabitService` class
  - [ ] Implement create, read, update, delete methods
  - [ ] Validate habit names (not empty, max length)
  
- [ ] Implement habit completion service (AC: #2)
  - [ ] Implement `mark_complete(habit_id, date)` method
  - [ ] Implement `unmark_complete(habit_id, date)` method
  - [ ] Prevent duplicate completions for same day
  
- [ ] Build habit tracking UI (AC: #1, #2, #3)
  - [ ] Create habit list view
  - [ ] Add "New Habit" button and creation dialog
  - [ ] Create daily checkmark UI (simple checkbox or toggle)
  - [ ] Build week/month progress view (calendar grid with checkmarks)
  
- [ ] Testing (AC: all)
  - [ ] Unit tests for habit service
  - [ ] Integration tests for habit completion
  - [ ] UI tests for habit creation and completion

## Dev Notes

### Architecture Compliance

**Data Architecture:** SQLAlchemy ORM, SQLite local storage, Alembic migrations

**Frontend:** MVVM with PySide6, Atomic Design principles

**Naming:** `snake_case` database, PEP 8 Python, `verbNoun` signals

### Data Model

**`habits` table:**
```sql
CREATE TABLE habits (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**`habit_completions` table:**
```sql
CREATE TABLE habit_completions (
    id INTEGER PRIMARY KEY,
    habit_id INTEGER NOT NULL,          -- FK to habits.id
    completion_date TEXT NOT NULL,      -- ISO 8601 date (YYYY-MM-DD)
    created_at TEXT NOT NULL,
    UNIQUE(habit_id, completion_date)   -- Prevent duplicate completions
);
```

### Habit Service Implementation

```python
from datetime import date
from sqlalchemy.orm import Session

class HabitService:
    def __init__(self, session: Session):
        self.session = session
    
    def create_habit(self, name: str, description: str = None):
        """Create new habit."""
        habit = Habit(name=name, description=description)
        self.session.add(habit)
        self.session.commit()
        return habit
    
    def get_all_habits(self):
        """Get all habits."""
        return self.session.query(Habit).all()
    
    def mark_complete(self, habit_id: int, completion_date: date = None):
        """Mark habit as complete for a date."""
        if completion_date is None:
            completion_date = date.today()
        
        # Check if already completed
        existing = self.session.query(HabitCompletion).filter_by(
            habit_id=habit_id,
            completion_date=completion_date.isoformat()
        ).first()
        
        if not existing:
            completion = HabitCompletion(
                habit_id=habit_id,
                completion_date=completion_date.isoformat()
            )
            self.session.add(completion)
            self.session.commit()
        
        return True
    
    def unmark_complete(self, habit_id: int, completion_date: date = None):
        """Unmark habit completion."""
        if completion_date is None:
            completion_date = date.today()
        
        self.session.query(HabitCompletion).filter_by(
            habit_id=habit_id,
            completion_date=completion_date.isoformat()
        ).delete()
        self.session.commit()
    
    def get_completions(self, habit_id: int, start_date: date, end_date: date):
        """Get completions for a habit within date range."""
        return self.session.query(HabitCompletion).filter(
            HabitCompletion.habit_id == habit_id,
            HabitCompletion.completion_date >= start_date.isoformat(),
            HabitCompletion.completion_date <= end_date.isoformat()
        ).all()
```

### UI Implementation

**Weekly Progress View:**
```
┌─────────────────────────────────────────┐
│ 🎯 Habits                               │
├─────────────────────────────────────────┤
│ Morning Exercise                        │
│ M  T  W  T  F  S  S                     │
│ ✓  ✓  ✓  ○  ○  ○  ○                     │
│                                          │
│ Read 30 Minutes                          │
│ M  T  W  T  F  S  S                     │
│ ✓  ○  ✓  ✓  ○  ○  ○                     │
│                                          │
│ [+ New Habit]                            │
└─────────────────────────────────────────┘
```

**Today's Habits (Quick Access):**
```
┌──────────────────┐
│ Today's Habits   │
├──────────────────┤
│ ☐ Morning Exercise
│ ☑ Read 30 Minutes
│ ☐ Drink Water
└──────────────────┘
```

### Common LLM Mistakes to AVOID

- ❌ Don't implement streak calculations (out of scope for this story)
- ❌ Don't add analytics or charts (keep it simple)
- ❌ Don't forget UNIQUE constraint on (habit_id, completion_date)
- ❌ Don't use timestamps - use dates only (ISO 8601 YYYY-MM-DD)
- ❌ Don't overcomplicate UI - simple checkmarks are sufficient

### References

- [Source: architecture.md#Data Architecture] - SQLAlchemy, SQLite
- [Source: epics.md#Story 7.1 Acceptance Criteria]
- [Source: epics.md#Epic 7] - Focus and Well-being

## Dev Agent Record

### Agent Model Used
_To be filled by dev agent_

### Completion Notes List
_To be filled by dev agent_

### File List
_To be filled by dev agent_

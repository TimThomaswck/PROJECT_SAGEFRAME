# Story 4.2: Read Calendar to Identify Free/Busy Times

Status: ready-for-dev

## Epic Context

**Epic 4: Intelligent Calendar & Proactive Scheduling**

This epic covers calendar integration and intelligent scheduling. Story 4.2 builds on Story

 4.1 (calendar connection) to analyze availability.

**Dependencies:** Requires Story 4.1 (calendar connection) to be complete.

## Story

As a user,
I want Sageframe to read my connected calendar and identify my free and busy times,
so that the system can understand my availability and make informed suggestions for scheduling.

## Acceptance Criteria

1. **Given** an external calendar is successfully connected (from Story 4.1),  
   **When** Sageframe accesses the calendar data,  
   **Then** it accurately distinguishes between time slots marked as "free" and "busy" based on event entries.

2. **Given** Sageframe has identified free/busy times,  
   **Then** this availability information is stored internally in a format that can be easily queried by other Sageframe features (e.g., proactive scheduling).

3. **Given** my calendar contains recurring events or all-day events,  
   **Then** Sageframe correctly interprets these to mark the corresponding time as busy or free as appropriate.

4. **Given** I am performing any operation related to calendar reading,  
   **Then** the interaction is responsive and fluid (NFR1, NFR2), and data privacy is respected as per NFR3.

## Business Value & Context

**Primary User Need:** Enable AI Co-Pilot to make intelligent time-based suggestions without manual availability input.

**Why This Matters:**
- Foundation for Stories 4.4 (proactive scheduling) and 4.6 (intelligent scheduling)
- Enables time blocking (Story 4.5) by identifying available slots
- Reduces manual effort in finding free time
- Prevents double-booking and scheduling conflicts

**Related FRs:**
- FR21: System can read calendar to identify free/busy times

## Tasks / Subtasks

- [ ] Extend calendar data model for availability (AC: #2)
  - [ ] Create `availability_slots` table to store computed free/busy periods
  - [ ] Add indexes for time-range queries
  - [ ] Implement Alembic migration
  
- [ ] Implement availability analysis service (AC: #1, #3)
  - [ ] Create `AvailabilityService` class
  - [ ] Parse calendar events to identify busy periods
  - [ ] Calculate free periods (gaps between busy periods)
  - [ ] Handle recurring events (expand to individual occurrences)
  - [ ] Handle all-day events correctly
  
- [ ] Build availability query API (AC: #2)
  - [ ] Implement `find_free_slots(start_time, end_time, duration)` method
  - [ ] Implement `is_time_available(start_time, end_time)` method
  - [ ] Optimize queries with SQLite indexes
  
- [ ] Implement background availability refresh (AC: #4)
  - [ ] Trigger availability recalculation on calendar sync completion
  - [ ] Async processing (don't block UI)
  - [ ] Cache availability results for performance
  
- [ ] Testing (AC: all)
  - [ ] Test recurring event expansion
  - [ ] Test all-day event handling
  - [ ] Test free slot finding with various constraints
  - [ ] Test performance with large calendar (1000+ events)

## Dev Notes

### Architecture Compliance

**Data Architecture:** SQLAlchemy + Pydantic, Alembic migrations, SQLite local storage

**Performance:** Non-blocking async processing, indexed queries, caching for frequent lookups

**Naming:** `snake_case` database, PEP 8 Python, `verbNoun` signals

### Data Model

**`availability_slots` table:**
```sql
id              INTEGER PRIMARY KEY
connection_id   INTEGER NOT NULL -- FK to calendar_connections.id
start_time      TEXT NOT NULL    -- ISO 8601 UTC
end_time        TEXT NOT NULL    -- ISO 8601 UTC
status          TEXT NOT NULL    -- 'free' or 'busy'
event_id        TEXT             -- FK to calendar_events.id (if busy)
computed_at     TEXT NOT NULL    -- ISO 8601 UTC
```

**Indexes:**
```sql
CREATE INDEX idx_availability_time_range ON availability_slots(connection_id, start_time, end_time);
CREATE INDEX idx_availability_status ON availability_slots(connection_id, status);
```

### Recurring Event Handling

Use Python `dateutil.rrule` to expand recurring events:

```python
from dateutil.rrule import rrulestr
from datetime import datetime

def expand_recurring_event(event, start_date, end_date):
    """Expand recurring event into individual occurrences."""
    if not event.recurrence_rule:
        return [event]
    
    rrule = rrulestr(event.recurrence_rule, dtstart=event.start_time)
    occurrences = []
    for dt in rrule.between(start_date, end_date):
        occurrence = Event(
            start_time=dt,
            end_time=dt + (event.end_time - event.start_time),
            summary=event.summary
        )
        occurrences.append(occurrence)
    return occurrences
```

### Free Slot Finding Algorithm

```python
def find_free_slots(start_range, end_range, min_duration_minutes=30):
    """Find free time slots within a date range."""
    # Get all busy periods sorted by start time
    busy_periods = get_busy_periods(start_range, end_range)
    
    free_slots = []
    current_time = start_range
    
    for busy in busy_periods:
        # Gap before this busy period
        if busy.start_time > current_time:
            gap_duration = (busy.start_time - current_time).total_seconds() / 60
            if gap_duration >= min_duration_minutes:
                free_slots.append({
                    'start': current_time,
                    'end': busy.start_time,
                    'duration_minutes': gap_duration
                })
        current_time = max(current_time, busy.end_time)
    
    # Final gap after last busy period
    if end_range > current_time:
        gap_duration = (end_range - current_time).total_seconds() / 60
        if gap_duration >= min_duration_minutes:
            free_slots.append({
                'start': current_time,
                'end': end_range,
                'duration_minutes': gap_duration
            })
    
    return free_slots
```

### Common LLM Mistakes to AVOID

- ❌ Don't forget to expand recurring events before calculating availability
- ❌ Don't block UI thread during availability calculation - use async
- ❌ Don't recalculate availability on every query - cache results
- ❌ Don't forget to handle all-day events (they span entire day)
- ❌ Don't ignore time zones - always use UTC internally

### References

- [Source: architecture.md#Data Architecture]
- [Source: epics.md#Story 4.2 Acceptance Criteria]
- [Source: epics.md#NFR1, NFR2, NFR3]

## Dev Agent Record

### Agent Model Used
_To be filled by dev agent_

### Completion Notes List
_To be filled by dev agent_

### File List
_To be filled by dev agent_

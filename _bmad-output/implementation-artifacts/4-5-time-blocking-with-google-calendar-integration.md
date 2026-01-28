# Story 4.5: Time Blocking with Google Calendar Integration

Status: ready-for-dev

## Story

As a user,
I want to create a time block for a task and push it to my Google Calendar,
so that I can dedicate specific time for my tasks.

## Acceptance Criteria

1. **Given** I am viewing a task, **When** I choose to create a time block, **Then** I can create a time block with a start and end time.

2. **Given** I have created a time block, **When** I choose to push it to my calendar, **Then** it is sent to my connected Google Calendar as an event (relying on functionality from Story 4.3).

## Dev Notes

**Dependencies:**
- Epic 2 (task management system)
- Story 4.1 (calendar connection)
- Story 4.3 (event creation)

**Implementation:**
- Add "Time Block" action to task detail view
- Create time block picker UI (date + time range)
- Use Story 4.2 (availability analysis) to suggest available time slots
- Use Story 4.3 (event creation) to push to Google Calendar

**Time Block Format:**
```
Event Title: "[Focus] Task Name"
Description: "Dedicated time block for: [Task Description]"
Color: Use distinct calendar color for focus blocks
```

**UI Flow:**
1. User clicks "Create Time Block" on task
2. Show time picker with suggested free slots (from Story 4.2)
3. User selects time slot
4. Confirm and push to Google Calendar
5. Show confirmation: "Time block created: Tuesday 2-4pm"

**Common Mistakes to AVOID:**
- ❌ Don't forget to link time block event back to task (FK relationship)
- ❌ Don't allow overlapping time blocks (validate against availability)
- ❌ Don't create time blocks for completed tasks

## Dev Agent Record
_To be filled by dev agent_

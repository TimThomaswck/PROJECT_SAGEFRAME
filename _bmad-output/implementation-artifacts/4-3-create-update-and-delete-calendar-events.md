# Story 4.3: Create, Update, and Delete Calendar Events

Status: ready-for-dev

## Story

As a user,
I want Sageframe to be able to create, update, and delete events directly in my connected external calendar,
so that I can manage my schedule through Sageframe and ensure my calendar is always accurate without switching applications.

## Acceptance Criteria

1. **Given** an external calendar is connected (from Story 4.1), **When** I create a new event within Sageframe, **Then** this event is successfully created in my external calendar.

2. **Given** an event exists in my external calendar and is displayed in Sageframe, **When** I modify that event's details (e.g., time, title, description) within Sageframe, **Then** the changes are successfully updated in my external calendar.

3. **Given** an event exists in my external calendar and is displayed in Sageframe, **When** I delete that event within Sageframe, **Then** the event is successfully deleted from my external calendar.

4. **Given** any operation to create, update, or delete an event fails (as per NFR8), **Then** the system handles the error gracefully, attempts to retry, and provides a clear prompt for manual intervention if necessary (NFR9).

5. **Given** I am performing any calendar event management operation, **Then** the interaction is responsive and fluid (NFR1, NFR2).

## Dev Notes

**Dependencies:** Requires Story 4.1 (calendar connection and sync service).

**Implementation:** Extend `CalendarSyncService` from Story 4.1 with CRUD methods for events. Use Google Calendar API methods: `events().insert()`, `events().update()`, `events().delete()`.

**Error Handling:** Implement retry logic with exponential backoff (NFR8). Show user-friendly error prompts for persistent failures (NFR9).

**Data Model:** Use existing `calendar_events` table from Story 4.1. Mark events created in Sageframe with `source='sageframe'`.

**UI Integration:** Add event creation/edit/delete buttons to calendar view. Integrate with existing task/project system (optional: create calendar events from tasks).

**Common Mistakes to AVOID:**
- ❌ Don't forget to sync locally after pushing to Google Calendar
- ❌ Don't block UI during API calls - always async
- ❌ Don't forget to handle partial failures (some events fail, others succeed)

## Dev Agent Record
_To be filled by dev agent_

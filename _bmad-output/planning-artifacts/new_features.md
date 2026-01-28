## New Functional Requirements

*   **FR31:** A user can break down a task into a checklist of subtasks.
*   **FR32:** The system can remind the user of overdue or untouched tasks.
*   **FR33:** A user can manually estimate the energy/effort required for a task (e.g., small, medium, large).
*   **FR34:** A user can create a time block for a task and push it to their Google Calendar.
*   **FR35:** The system can sync events from SageFrame to Google Calendar (one-way).
*   **FR36:** The system can provide basic intelligent scheduling suggestions.
*   **FR37:** A user can track simple habits with daily checkmarks.
*   **FR38:** A user can use a Pomodoro timer to help them focus.
*   **FR39:** A user can use tags and smart filters with AND/OR logic to organize and find information.

---

## New User Stories

### Epic 2: Comprehensive Task & Project Management

**Story 2.7: Hierarchical Tasks (1-level subtasks)**

*   **As a user, I want to break down my tasks into a simple checklist of subtasks, so that I can manage more complex tasks without being overwhelmed.**
*   **Acceptance Criteria:**
    *   Given I am viewing a task, I can add, edit, and delete subtasks in a checklist format.
    *   Given a task has subtasks, I can mark each subtask as complete.
    *   Given a task has subtasks, the main task's progress is visually updated as I complete subtasks.

**Story 2.8: Basic Task Suggestions (Overdue/Untouched Reminders)**

*   **As a user, I want to be reminded of overdue or untouched tasks, so that nothing falls through the cracks.**
*   **Acceptance Criteria:**
    *   Given a task is overdue, the system will highlight it in my task list.
    *   Given a task has not been updated for a configurable period (e.g., 7 days), the system will suggest I review it.

**Story 2.9: Manual Energy/Effort Estimation**

*   **As a user, I want to manually estimate the energy/effort required for a task (e.g., small, medium, large), so that I can better plan my day based on my energy levels.**
*   **Acceptance Criteria:**
    *   Given I am creating or editing a task, I can select an energy/effort level from a predefined list (e.g., Small, Medium, Large).
    *   Given a task has an energy/effort level, it is clearly displayed in my task list.

---

### Epic 4: Intelligent Calendar & Proactive Scheduling

**Story 4.5: Time Blocking with Google Calendar Integration**

*   **As a user, I want to create a time block for a task and push it to my Google Calendar, so that I can dedicate specific time for my tasks.**
*   **Acceptance Criteria:**
    *   Given I am viewing a task, I can create a time block with a start and end time.
    *   Given I have created a time block, I can push it to my connected Google Calendar as an event.

**Story 4.6: One-Way Calendar Sync (SageFrame to Google Calendar)**

*   **As a user, I want to sync my SageFrame events to my Google Calendar, so that I can see my schedule in one place.**
*   **Acceptance Criteria:**
    *   Given I have connected my Google Calendar, any new event created in SageFrame is automatically pushed to my Google Calendar.
    *   (Note: This is a one-way sync. Changes in Google Calendar will not be reflected in SageFrame).

**Story 4.7: Intelligent Scheduling (Lite)**

*   **As a user, I want the system to provide basic intelligent scheduling suggestions, so that I can get help with planning my day.**
*   **Acceptance Criteria:**
    *   Given my connected calendar, the system can identify my free slots.
    *   Given my task list, the system can suggest which tasks to work on based on their due date and my free slots.

---

### Epic 7: Focus and Well-being

**Story 7.1: Simple Habit Tracker**

*   **As a user, I want to track simple habits with daily checkmarks, so that I can build positive routines.**
*   **Acceptance Criteria:**
    *   Given I am in the habit tracking section, I can create and name a new habit.
    *   Given a habit exists, I can mark it as complete for the current day with a single click.
    *   Given a habit exists, I can see my progress for the current week/month.
    *   (Note: No complex streak math or analytics are included in this story).

**Story 7.2: Pomodoro & Focus Mode**

*   **As a user, I want to use a Pomodoro timer to help me focus, so that I can work in focused bursts.**
*   **Acceptance Criteria:**
    *   Given I want to focus on a task, I can start a Pomodoro timer (e.g., 25 minutes).
    *   Given the timer is running, the application enters a "focus mode" with minimal UI distractions.
    *   Given the timer completes, the system notifies me to take a short break.
    *   (Note: No analytics or tracking of Pomodoro sessions is included in this story).

---

### Epic 3: Effortless Information Capture & Curation

**Story 3.4: Tags & Smart Filters**

*   **As a user, I want to use tags and smart filters with AND/OR logic, so that I can organize and find my information more effectively.**
*   **Acceptance Criteria:**
    *   Given I am creating or editing a note or task, I can add one or more tags.
    *   Given I am viewing my notes or tasks, I can filter them by one or more tags.
    *   Given I am filtering, I can use AND/OR logic to combine multiple filters.
    *   (Note: This does not include a full rule engine, just simple filtering logic).

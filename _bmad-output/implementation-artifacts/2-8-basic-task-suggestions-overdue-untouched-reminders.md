# Story 2.8: basic-task-suggestions-overdue-untouched-reminders

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to be reminded of overdue or untouched tasks,
So that nothing falls through the cracks.

## Acceptance Criteria

*   **Given** a task is overdue,
    **When** I view my task list,
    **Then** the system will highlight it.
*   **Given** a task has not been updated for a configurable period (e.g., 7 days),
    **When** I view my task list,
    **Then** the system will suggest I review it.

## Tasks / Subtasks

- [ ] Design and implement modifications to `Task` SQLAlchemy model to ensure `due_date` and `last_updated` fields are present and properly managed. Consider adding `last_review_date`.
- [ ] Implement a dedicated `SuggestionService` responsible for querying and identifying:
  - [ ] Overdue tasks (e.g., `due_date < current_date` for tasks with a `due_date`)
  - [ ] Untouched tasks (e.g., `last_updated < (current_date - configurable_period)`)
- [ ] Implement logic for `configurable_period` for "untouched" tasks (e.g., user setting in preferences, system default).
- [ ] Define and implement how overdue/untouched logic applies to subtasks within hierarchical tasks (Story 2.7).
- [ ] Design UI components within the task list to visually highlight overdue tasks (e.g., color change, icon).
- [ ] Design UI components to suggest review for untouched tasks (e.g., a small banner, an icon with a tooltip).
- [ ] Implement mechanisms for triggering suggestions (e.g., on task list load, periodic background check).
- [ ] Implement user interactions with suggestions (e.g., dismiss suggestion, mark as reviewed).
- [ ] Ensure efficient database queries for task identification (NFR2).
- [ ] Add unit tests for suggestion logic (overdue/untouched identification).
- [ ] Add integration tests for suggestion service with task model.
- [ ] Add UI tests for visual highlighting and suggestion display.

## Dev Notes

- **Architectural Context & Technical Stack:**
  - Strictly Python-only development.
  - UI to be implemented using PySide6 following the MVVM (Model-View-ViewModel) pattern and Atomic Design principles.
  - Data persistence for tasks uses SQLite, managed via SQLAlchemy (ORM) and Alembic for migrations.
  - Data validation should utilize SQLAlchemy models and Pydantic.
- **Implementation Details:**
  - **"Overdue" Definition (Critical):** A task is considered "overdue" if its `due_date` is in the past relative to the current date and the task is not completed. Tasks without a `due_date` should not be considered overdue.
  - **Configurable Period for "Untouched" (Critical):** The "configurable period" (e.g., 7 days) for untouched tasks must be implemented as a user-configurable setting within the application preferences. This setting should be persisted and retrieved for task identification.
  - **Subtask Handling (Critical):**
    - If a parent task is overdue, all its subtasks (regardless of their individual `due_date`) are also implicitly highlighted as part of the overdue parent.
    - If a parent task is untouched, its subtasks are also implicitly considered untouched. Conversely, if a subtask is updated, its parent's `last_updated` (or `last_review_date`) should also be updated.
  - **Suggestion Trigger & UI (Critical):**
    - The suggestion mechanism should run efficiently on task list load and potentially as a periodic background check (configurable by user).
    - **Overdue Tasks:** Visually highlight overdue tasks directly within the task list (e.g., a distinct background color, a prominent icon, or bold text).
    - **Untouched Tasks:** For untouched tasks, display a subtle visual cue (e.g., a small icon with a tooltip, a gentle border) or a dedicated suggestion panel within the task list view, prompting the user to review.
  - **User Interaction with Suggestions (Critical):**
    - Users must be able to dismiss individual suggestions for untouched tasks (e.g., "Dismiss for 1 week").
    - Implement a "Mark as Reviewed" action that updates a `last_review_date` field on the task, resetting its "untouched" status.
  - **Task Model Enhancements (Enhancement):** Modify the `Task` SQLAlchemy model to ensure `due_date` and `last_updated` fields are properly managed. Add a `last_review_date` field (type: DateTime) to enable accurate tracking of when a task was last explicitly reviewed by the user.
  - **Dedicated Suggestion Service (Enhancement):** Create a dedicated `app/services/suggestion_service.py` responsible for encapsulating the logic to identify overdue and untouched tasks by querying the database. This service should expose methods callable by ViewModels.
  - **Performance Considerations (Enhancement):** Implement efficient database queries with appropriate indexing on `due_date`, `last_updated`, and `is_completed` fields to ensure task identification does not impact UI responsiveness (NFR2) for large task lists.
  - **Prioritization of Suggestions (Optimization):** Consider implementing a mechanism to prioritize suggestions (e.g., overdue tasks with 'High' priority are highlighted more aggressively).
  - **Customizable Untouched Period (Optimization):** In the future, allow users to define different "untouched" periods per project or task category.
- **Previous Story Learnings:**
  - Stories 2.1-2.3 provide the core `Task` model, including fields like `due_date` and potentially `last_updated` (to be confirmed/added).
  - Stories 2.4-2.7 establish patterns for task display, interaction, and data persistence, which are directly applicable to highlighting and suggesting tasks in the UI.
  - Story 2.7 (Hierarchical Tasks) is crucial for understanding how overdue/untouched logic should cascade or be aggregated for parent tasks.
  - UI state management and data synchronization patterns learned from previous UI stories will be vital.
- **Testing Standards:**
  - Implement robust unit tests for the `SuggestionService` logic (overdue/untouched identification, `last_review_date` updates).
  - Develop integration tests to verify the `SuggestionService` correctly interacts with the `Task` model and database.
  - Create UI tests to ensure overdue tasks are correctly highlighted, untouched task suggestions appear as designed, and user interactions (dismiss, mark reviewed) function as expected.

### Project Structure Notes

- Adhere to PEP 8 for Python and use `snake_case` for all database fields, JSON payloads, and API parameters.
- PySide6 Signals & Slots should follow `verbNoun` naming conventions and integrate with Pydantic for data handling.
- **Component Placement (Enhancement):**
  - The `SuggestionService` (containing identification logic) should be located at `app/services/suggestion_service.py`.
  - Any new configuration models for the "untouched period" would be in `app/models/settings_model.py`.
  - UI components for highlighting and displaying suggestions should be integrated into existing task list views (`app/ui/tasks/task_list_view.py`) or dedicated widgets within `app/ui/tasks`.
- Ensure consistent use of existing project conventions for module imports and class definitions.

### References

- Project Epics and Architectural Details: [Source: _bmad-output/planning-artifacts/epics.md]

## Dev Agent Record

### Agent Model Used

Gemini (sm.agent.yaml)

### Debug Log References

(No specific debug logs generated for this review process)

### Completion Notes List

- Comprehensive review and update based on user feedback.
- All identified critical issues, enhancements, and optimizations applied to story context.
- Detailed architectural guidance, implementation specifics (overdue/untouched definition, configuration, subtask handling, UI/UX, user interaction), and project structure notes integrated.
- References section verified as correct.

### File List

- _bmad-output/implementation-artifacts/2-8-basic-task-suggestions-overdue-untouched-reminders.md (updated)
- _bmad-output/planning-artifacts/epics.md (referenced)
- _bmad-output/implementation-artifacts/sprint-status.yaml (referenced)

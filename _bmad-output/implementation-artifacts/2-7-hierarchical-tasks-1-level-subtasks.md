# Story 2.7: Hierarchical Tasks (1-level subtasks)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to break down my tasks into a simple checklist of subtasks,
So that I can manage more complex tasks without being overwhelmed.

## Acceptance Criteria

*   **Given** I am viewing a task,
    **When** I choose to add a subtask,
    **Then** I can add, edit, and delete subtasks in a checklist format.
*   **Given** a task has subtasks,
    **When** I mark a subtask as complete,
    **Then** the subtask is visually marked as done.
*   **Given** a task has subtasks,
    **Then** the main task's progress is visually updated as I complete subtasks.

## Tasks / Subtasks

- [ ] Design and implement SQLAlchemy model for subtasks (e.g., extend existing `Task` model or create new `Subtask` model with `parent_task_id` foreign key)
  - [ ] Define fields for subtask title, completion status, and order
- [ ] Implement logic to calculate and update parent task progress based on subtask completion
  - [ ] Store/derive parent task progress (e.g., `completed_subtasks / total_subtasks`)
- [ ] Implement UI for adding, editing, and deleting subtasks within a parent task's detail view
  - [ ] Use a checklist format for subtask display
  - [ ] Implement visual representation of subtask completion (e.g., checkbox, strike-through)
- [ ] Define and implement cascading actions for parent task completion/deletion
  - [ ] Automatically complete subtasks when parent task is completed
  - [ ] Handle subtask deletion when parent task is deleted (e.g., cascade delete)
- [ ] Ensure actions on subtasks update parent task properties (e.g., `last_updated`)
- [ ] Ensure UI fluidity and responsiveness for subtask interactions
- [ ] Add unit tests for subtask model, progress calculation, and cascading logic
- [ ] Add integration tests for subtask CRUD operations and parent task progress updates
- [ ] Add UI tests for subtask display, editing, and deletion

## Dev Notes

- **Architectural Context & Technical Stack:**
  - Strictly Python-only development.
  - UI to be implemented using PySide6 following the MVVM (Model-View-ViewModel) pattern and Atomic Design principles.
  - Data persistence for tasks and subtasks uses SQLite, managed via SQLAlchemy (ORM) and Alembic for migrations.
  - Data validation (both for input and output) should utilize SQLAlchemy models and Pydantic.
- **Implementation Details:**
  - **Subtask Data Model (Critical):** Implement subtasks by either extending the existing `Task` SQLAlchemy model with a `parent_task_id` (self-referencing foreign key) or creating a new lightweight `Subtask` model with a foreign key to `Task`. Each subtask should have at least a `title` and `is_completed` field. Consider an `order` field for display.
  - **Parent Task Progress Calculation (Critical):** The "main task's progress visually updated" requires logic to calculate progress based on its subtasks. This typically means `(count_completed_subtasks / count_total_subtasks) * 100%`. This progress metric should be stored or derived in the parent `Task` model.
  - **Subtask UI/UX (Critical):** Design the user interface for adding, editing, and deleting subtasks within a parent task's detail view. Subtasks should be displayed in a clear "checklist format" (e.g., indented list) with checkboxes for completion status and visual cues (e.g., strike-through) for completed subtasks.
  - **Cascading Actions (Critical):** Define the behavior for cascading actions. If a parent task is marked complete, all its subtasks should automatically be marked complete. If a parent task is deleted, its subtasks should also be deleted (cascade delete). Consider prompting the user for confirmation.
  - **Impact on Parent Task (Critical):** Actions on subtasks (e.g., completion, title change) should update the parent task's `last_updated` timestamp to reflect changes within its hierarchy.
  - **Reusing Task Model (Enhancement):** Prioritize reusing existing `Task` model fields and functionalities for subtasks where applicable to minimize code duplication and maintain consistency.
  - **Display Location (Enhancement):** Subtasks should be prominently displayed within the parent task's detail view, possibly in an expandable section, allowing users to focus or hide subtask details.
  - **UI Feedback (Enhancement):** Provide clear visual feedback for all subtask actions (add, edit, delete, complete) to ensure a responsive and intuitive user experience.
  - **Ordering of Subtasks (Enhancement):** Implement functionality to allow users to reorder subtasks within their parent task, and ensure this order is persisted.
  - **Keyboard Shortcuts (Optimization):** Consider adding keyboard shortcuts for quickly adding new subtasks or toggling their completion status.
- **Previous Story Learnings:**
  - Stories 2.1-2.3 provide the core Task model and CRUD operations, which this story will extend.
  - Stories 2.4 (Kanban), 2.5 (Gantt), and 2.6 (Gamification) provide patterns for task visualization and how task status/completion impacts other system features. Ensure subtask completion correctly triggers updates to gamification (if subtasks contribute XP) and other views.
  - Recent work on UI interactions and state management (e.g., Story 1.7 Undo/Redo) is relevant for managing subtask changes.
- **Testing Standards:**
  - Implement unit tests for the subtask data model, parent task progress calculation logic, and cascading actions.
  - Develop integration tests to verify the CRUD operations for subtasks and how they interact with parent tasks and other related system components.
  - Create UI tests to confirm correct display and interaction with subtasks (add, edit, delete, complete) and visual updates to parent task progress.

### Project Structure Notes

- Adhere to PEP 8 for Python and use `snake_case` for all database fields, JSON payloads, and API parameters.
- PySide6 Signals & Slots should follow `verbNoun` naming conventions and integrate with Pydantic for data models.
- **Component Placement (Enhancement):** Subtask-specific logic (e.g., `subtask_service.py`), data model extensions (e.g., modifications to `task_model.py` or new `subtask_model.py`), and UI components (`subtask_widget.py`) should be placed logically within the existing `app/services`, `app/models`, and `app/ui/tasks` (or a new `app/ui/subtasks`) directories respectively.
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
- Detailed architectural guidance, implementation specifics (subtask data model, progress calculation, UI/UX, cascading actions), and project structure notes integrated.
- References section verified as correct.

### File List

- _bmad-output/implementation-artifacts/2-7-hierarchical-tasks-1-level-subtasks.md (updated)
- _bmad-output/planning-artifacts/epics.md (referenced)
- _bmad-output/implementation-artifacts/sprint-status.yaml (referenced)


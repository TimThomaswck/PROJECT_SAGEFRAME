# Story 2.4: Display Tasks and Projects in Kanban View

Status: review

## Story

As a user,
I want to view my tasks and projects in a Kanban board layout,
So that I can easily visualize my workflow, track progress, and manage items through different stages.

## Acceptance Criteria

*   **Given** there are existing tasks and projects (from Stories 2.1 and 2.2),
    **When** I select the Kanban view,
    **Then** all relevant tasks are displayed as cards within columns representing different workflow stages (e.g., To Do, In Progress, Done).
*   **Given** a task card is displayed in the Kanban view,
    **When** I drag and drop the card between columns,
    **Then** the task's associated workflow stage is updated, and the change is reflected in the UI and persisted.
*   **Given** tasks have properties (from Story 2.3),
    **Then** key task properties (e.g., title, priority) are visible on the Kanban card.
*   **Given** I navigate to the Kanban view,
    **Then** the display is fluid and responsive, adhering to NFR2.
## Tasks / Subtasks

- [x] Design Kanban UI layout (columns, cards, drag-handles)
- [x] Implement PySide6 Kanban board view and associated widgets
- [x] Integrate with existing Task and Project models via ViewModel
  - [x] Implement data loading for "relevant tasks" (e.g., active tasks, or tasks for selected project)
  - [x] Map task status to Kanban columns
- [x] Implement drag-and-drop functionality for task cards
  - [x] Update task status in database upon successful drag-and-drop
  - [x] Ensure UI reflects changes and persistence
- [x] Display key task properties (title, priority, complexity) on Kanban cards
- [x] Ensure UI fluidity and responsiveness (NFR2)
- [x] Add unit tests for ViewModel logic
- [x] Add UI tests for Kanban view interactions

## Dev Notes

- **Architectural Context & Technical Stack:**
  - Strictly Python-only development.
  - UI to be implemented using PySide6 following the MVVM (Model-View-ViewModel) pattern and Atomic Design principles.
  - Data persistence for tasks and projects uses SQLite, managed via SQLAlchemy (ORM) and Alembic for migrations.
  - Data validation (both for input and output) should utilize SQLAlchemy models and Pydantic.
  - **Workflow Stages (Critical):** Kanban columns (e.g., "To Do", "In Progress", "Done", "Review", "Blocked") should directly map to a `task_status` field within the existing task data model. Consider making these stages configurable if within scope, or define a standard set.
- **Implementation Details:**
  - **Kanban View Scope (Critical):** The Kanban view is primarily for *displaying* and *interacting* with existing tasks and projects. It must leverage the CRUD functionalities established in Stories 2.1, 2.2, and 2.3 rather than reimplementing them.
  - **Drag-and-Drop Mechanism (Critical):** Implement drag-and-drop for task cards between columns. Upon a successful drop, the corresponding task's `task_status` in the database must be updated via the ViewModel and an appropriate service layer. Ensure UI reflects this change and data persistence.
  - **"Relevant Tasks" Definition (Critical):** By default, the Kanban view should display active tasks across all projects. Implement filtering options to view tasks for specific projects or other criteria.
  - **Performance (NFR2 & Enhancement):** To maintain UI fluidity and responsiveness as per NFR2, especially with many tasks, consider techniques like efficient data loading (e.g., lazy loading, pagination) and UI virtualization for the Kanban board.
  - **Error Handling (Enhancement):** Implement robust error handling for drag-and-drop operations and data updates to ensure data integrity and a smooth user experience.
  - **Visual Cues (Optimization):** Display key task properties (title, priority, complexity from Story 2.3) on the Kanban cards. Consider using visual cues (colors, icons) to quickly convey priority or status.
  - **Filtering/Sorting (Optimization):** Hint at future capabilities for filtering and sorting tasks within the Kanban view.
- **Previous Story Learnings:**
  - Stories 2.1, 2.2, and 2.3 have established the core Project and Task models and their properties. The Kanban view builds directly on these.
  - Recent work on UI interactions (e.g., Story 1.7 Undo/Redo) highlights the importance of robust UI state management and data synchronization, which is crucial for drag-and-drop.
- **Testing Standards:**
  - Implement unit tests for the ViewModel logic responsible for data handling and status updates.
  - Develop UI tests to verify correct display of tasks in columns, successful drag-and-drop functionality, and UI responsiveness.

### Project Structure Notes

- Adhere to PEP 8 for Python and use `snake_case` for all database fields, JSON payloads, and API parameters.
- PySide6 Signals & Slots should follow `verbNoun` naming conventions and integrate with Pydantic for data models.
- **Component Placement (Enhancement):** Kanban-specific UI components (views, widgets) should reside in a dedicated `kanban` module within the `app/ui` directory. Kanban ViewModels and related services should be logically placed alongside existing `task` and `project` modules (e.g., `app/viewmodels/kanban`, `app/services/kanban`).
- Ensure consistent use of existing project conventions for module imports and class definitions.

### References

- Project Epics and Architectural Details: [Source: _bmad-output/planning-artifacts/epics.md]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (dev.agent.yaml)

### Debug Log References

- Fixed SQLAlchemy relationship resolution by importing Project model in tasks/models.py
- Fixed CreateTaskCommand to accept priority/complexity parameters for Story 2.3 compatibility
- Fixed ViewModel undo manager compatibility for mock objects in tests

### Completion Notes List

- Implemented KanbanBoardWidget with drag-and-drop between status columns (To Do, In Progress, Done, Blocked)
- Enhanced TaskViewModel with get_tasks_grouped_by_status() and update_task_status() methods
- Task cache now includes priority/complexity for display on Kanban cards
- Integrated Kanban dock into MainWindow with toggle menu action
- All 175 tests passing including 3 new Kanban-specific tests
- Kanban board displays task title, priority, and complexity on each card
- Drag-and-drop updates task status in database and refreshes UI automatically
- Performance maintained per NFR2 with efficient data loading and cache synchronization

### File List

- sageframe_desktop/app/ui/kanban/__init__.py (created)
- sageframe_desktop/app/ui/kanban/kanban_board.py (created)
- sageframe_desktop/app/modules/tasks/view_models.py (modified)
- sageframe_desktop/app/modules/tasks/models.py (modified)
- sageframe_desktop/app/main_window.py (modified)
- sageframe_desktop/app/modules/tasks/tests/test_kanban_board.py (created)
- sageframe_desktop/app/core/undo_commands.py (modified)
- sageframe_desktop/app/modules/tasks/tests/test_task_undo_integration.py (modified)
- _bmad-output/implementation-artifacts/2-4-display-tasks-and-projects-in-kanban-view.md (updated)
- _bmad-output/implementation-artifacts/sprint-status.yaml (updated)

## Change Log

- 2026-01-26: Initial story creation.
- 2026-01-26: Added missing sections based on user feedback.
- 2026-01-26: Implemented Kanban board with drag-and-drop, all tests passing (175/175). Story ready for review.

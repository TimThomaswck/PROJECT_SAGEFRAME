# Story 2.5: Display Tasks and Projects in Gantt Chart View

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to view my tasks and projects in a Gantt chart layout,
So that I can visualize timelines, dependencies, and overall project progress more effectively.

## Acceptance Criteria

*   **Given** there are existing tasks and projects (from Stories 2.1 and 2.2) with defined start/end dates (implicitly covered by task creation),
    **When** I select the Gantt chart view,
    **Then** all relevant tasks and projects are displayed on a timeline, showing their duration and sequence.
*   **Given** a task is displayed in the Gantt chart,
    **When** I modify its start or end date directly on the chart (e.g., by dragging its bar),
    **Then** the task's dates are updated, and the change is reflected in the UI and persisted.
*   **Given** I navigate to the Gantt chart view,
    **Then** the display is fluid and responsive, adhering to NFR2.
*   **Given** tasks have properties such as dependencies (implicitly part of Gantt functionality, though not a specific FR),
    **Then** these dependencies are visually represented on the Gantt chart.

## Tasks / Subtasks

- [ ] Design Gantt chart UI layout (timeline, task bars, dependency lines)
- [ ] Implement PySide6 Gantt chart view and associated widgets
- [ ] Research/Integrate a PySide6-compatible interactive Gantt chart component or develop custom widget
- [ ] Extend Task model (SQLAlchemy) to include fields for dependencies (e.g., `depends_on_task_id`, `dependency_type`) and `start_date`, `end_date` if not already present
- [ ] Implement data loading for relevant tasks and projects, including their dates and dependencies
- [ ] Implement interactive date modification (drag task bars, resize)
  - [ ] Update task `start_date` and `end_date` in database upon UI interaction
  - [ ] Ensure UI reflects changes and persistence
- [ ] Implement visual representation of task dependencies (lines, arrows)
- [ ] Implement time scale switching (daily, weekly, monthly views)
- [ ] Ensure UI fluidity and responsiveness (NFR2) for complex charts
- [ ] Add unit tests for ViewModel logic and dependency management
- [ ] Add UI tests for Gantt chart interactions and date modifications

## Dev Notes

- **Architectural Context & Technical Stack:**
  - Strictly Python-only development.
  - UI to be implemented using PySide6 following the MVVM (Model-View-ViewModel) pattern and Atomic Design principles.
  - Data persistence for tasks and projects uses SQLite, managed via SQLAlchemy (ORM) and Alembic for migrations.
  - Data validation (both for input and output) should utilize SQLAlchemy models and Pydantic.
- **Implementation Details:**
  - **Task Dependencies (Critical):** Explicitly model task dependencies within the SQLAlchemy Task model. This will likely involve a self-referencing relationship (e.g., `Task.depends_on_task_id`) and a `dependency_type` field (e.g., 'finish-to-start', 'start-to-start').
  - **Date Modification & Persistence (Critical):** Implement interactive date modification directly on the Gantt chart (e.g., dragging task bars or resizing them). These UI interactions must trigger updates to the `start_date` and `end_date` fields in the SQLAlchemy Task model, which are then persisted to the SQLite database.
  - **Time Scale (Critical):** The Gantt chart should support different time scales (e.g., daily, weekly, monthly, quarterly views). Provide UI elements for users to switch between these granularities.
  - **UI/UX for Dependencies (Critical):** Visually represent task dependencies clearly on the Gantt chart, typically using connector lines or arrows between task bars.
  - **Integration with Existing Data (Critical):** The Gantt chart must leverage the existing task and project data models and the CRUD operations established in Stories 2.1, 2.2, and 2.3. It should not create duplicate data management logic.
  - **PySide6 Gantt Component (Enhancement):** Research and either integrate a suitable PySide6-compatible interactive Gantt chart library/widget or develop a custom QWidget for this functionality. Consider libraries that can handle complex drawing efficiently.
  - **Performance (NFR2 & Enhancement):** To ensure UI fluidity and responsiveness (NFR2) for potentially dense Gantt charts, optimize data loading (e.g., only load visible data range), drawing performance (e.g., custom painting, caching rendering), and potentially leverage hardware acceleration.
  - **Conflict Resolution (Enhancement):** Implement basic logic to highlight or warn users about scheduling conflicts or overlaps that occur when modifying task dates, especially for dependent tasks.
  - **Task Progress Representation (Enhancement):** Visually integrate task progress (e.g., a progress bar within the task bar, or percentage text) if the Task model includes a `progress` field.
  - **Gantt Scope:** The Gantt chart should display tasks and projects with defined timelines.
- **Previous Story Learnings:**
  - Stories 2.1, 2.2, and 2.3 provide the foundational Project and Task models.
  - Story 2.4 (Kanban View) provides patterns for displaying, interacting, and persisting changes to task data in a visual layout. This interaction model (e.g., drag-and-drop affecting backend data) is highly relevant.
  - Recent work on UI interactions (e.g., Story 1.7 Undo/Redo) reinforces the need for robust UI state management and data synchronization.
- **Testing Standards:**
  - Implement unit tests for ViewModel logic, particularly for date manipulation, dependency management, and data synchronization with the database.
  - Develop UI tests to verify correct display of tasks and dependencies, successful interactive date modification, and overall UI responsiveness and fluidity.

### Project Structure Notes

- Adhere to PEP 8 for Python and use `snake_case` for all database fields, JSON payloads, and API parameters.
- PySide6 Signals & Slots should follow `verbNoun` naming conventions and integrate with Pydantic for data models.
- **Component Placement (Enhancement):** Gantt-specific UI components (views, widgets) should reside in a dedicated `gantt` module within the `app/ui` directory. Gantt ViewModels and related services should be logically placed alongside existing `task` and `project` modules (e.g., `app/viewmodels/gantt`, `app/services/gantt`).
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
- Missing technical details for Gantt chart implementation added, including dependency modeling, date modification, and time scales.
- Detailed architectural guidance, implementation specifics, and project structure notes integrated.
- References updated.

### File List

- _bmad-output/implementation-artifacts/2-5-display-tasks-and-projects-in-gantt-chart-view.md (updated)
- _bmad-output/planning-artifacts/epics.md (referenced)
- _bmad-output/implementation-artifacts/sprint-status.yaml (referenced)

## Change Log

- 2026-01-26: Initial story creation.
- 2026-01-26: Added missing sections based on user feedback.


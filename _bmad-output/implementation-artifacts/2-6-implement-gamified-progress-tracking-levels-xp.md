# Story 2.6: Implement Gamified Progress Tracking (Levels & XP)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to see my progress visualized through a gamified system of levels and experience points (XP) based on task completion,
So that I feel motivated, encouraged, and rewarded for my productivity efforts.

## Acceptance Criteria

*   **Given** a task is marked as complete,
    **When** the system registers the completion,
    **Then** the user's XP counter is updated based on the task's properties (e.g., higher complexity tasks yield more XP).
*   **Given** a user accumulates enough XP,
    **When** their XP crosses a level threshold,
    **Then** the user's level is automatically increased, and a visual notification of the level-up is displayed.
*   **Given** the user views their profile or a dedicated progress dashboard,
    **Then** their current level, XP total, and progress towards the next level are clearly displayed.
*   **Given** task properties (from Story 2.3) include complexity,
    **Then** the XP awarded for task completion is proportional to the task's complexity.
*   **Given** I am viewing my gamified progress,
    **Then** the display is fluid and responsive, adhering to NFR2.

## Tasks / Subtasks

- [ ] Design and implement SQLAlchemy models for `UserProgress` (XP, Level, etc.)
- [ ] Define and implement XP calculation logic based on task properties (e.g., complexity from Story 2.3)
- [ ] Define and implement leveling system logic (XP thresholds for each level)
- [ ] Integrate XP gain with task completion events
- [ ] Implement UI for level-up visual notifications (e.g., toast, banner)
- [ ] Design and implement a dedicated UI (profile/dashboard) to display gamified progress
  - [ ] Display current level, XP total, and progress towards next level
- [ ] Ensure data persistence of XP and level in SQLite
- [ ] Ensure UI fluidity and responsiveness (NFR2)
- [ ] Add unit tests for XP calculation and leveling logic
- [ ] Add integration tests for task completion affecting XP/level
- [ ] Add UI tests for level-up notifications and progress display

## Dev Notes

- **Architectural Context & Technical Stack:**
  - Strictly Python-only development.
  - UI to be implemented using PySide6 following the MVVM (Model-View-ViewModel) pattern and Atomic Design principles.
  - Data persistence for user gamification progress (XP, level) uses SQLite, managed via SQLAlchemy (ORM) and Alembic for migrations.
  - Data validation (both for input and output) should utilize SQLAlchemy models and Pydantic.
- **Implementation Details:**
  - **XP Calculation Formula (Critical):** Define a clear formula or logic for calculating XP based on a completed task's properties. For instance, `XP = base_xp_per_task + (task_complexity_multiplier * complexity_value)`. Leverage `complexity` from Story 2.3.
  - **Leveling System Logic (Critical):** Implement a leveling system that defines how accumulated XP translates into user levels. This involves defining XP thresholds for each level (e.g., Level 1: 0-100 XP, Level 2: 101-250 XP). The progression curve (linear vs. exponential) should be considered.
  - **Data Model for Gamification (Critical):** Create a dedicated SQLAlchemy model (e.g., `UserProgress`) to store `user_id`, `current_xp`, `current_level`, and potentially `xp_to_next_level`. This data needs to be persistent in the SQLite database.
  - **Visual Notification Details (Critical):** Design the UI/UX for the "level-up" visual notification. This could be a transient toast message, an animated banner, or a simple modal dialog. Ensure it's engaging but non-intrusive.
  - **Progress Dashboard Content (Critical):** Detail the specific information to be displayed on the gamified progress dashboard. This should include: current level, total XP, XP needed for the next level (or a progress bar), and potentially recent achievements or milestones.
  - **Configurability (Enhancement):** Initially, XP values and level thresholds can be hardcoded. Consider future requirements for making these parameters configurable by the user or an administrator.
  - **Additional XP Earning Events (Enhancement):** While task completion is primary, briefly consider if other user actions (e.g., creating a new project, completing a full sprint, consistent mood check-ins) could contribute to XP gain in future iterations.
  - **Gamification UI Integration Points (Enhancement):** Specify where the gamified progress will be displayed (e.g., a dedicated "Progress" tab, a persistent sidebar widget, integrated into existing task/project dashboards).
  - **Badges/Achievements (Enhancement):** Hint at future expansion possibilities for a system of badges or achievements that users can earn for specific accomplishments.
  - **Sound Effects/Progress Visualizations (Optimization):** Suggest incorporating optional sound effects for level-ups/XP gains and more dynamic visual representations of progress.
- **Previous Story Learnings:**
  - Stories 2.1-2.3 provide the core Task and Project models, especially `complexity` from Story 2.3, which is central to XP calculation.
  - Stories 2.4 (Kanban) and 2.5 (Gantt) provide patterns for updating UI based on backend data changes and maintaining NFR2 (fluidity).
  - Recent work on UI interactions (e.g., Story 1.7 Undo/Redo) reinforces the need for robust UI state management.
- **Testing Standards:**
  - Implement unit tests for the XP calculation logic and the leveling system logic to ensure correctness.
  - Develop integration tests to verify that task completion events correctly trigger XP updates and level changes, and that these changes are persisted.
  - Create UI tests to confirm that level-up notifications display as expected and that the gamified progress dashboard accurately reflects the user's progress and adheres to NFR2.

### Project Structure Notes

- Adhere to PEP 8 for Python and use `snake_case` for all database fields, JSON payloads, and API parameters.
- PySide6 Signals & Slots should follow `verbNoun` naming conventions and integrate with Pydantic for data models.
- **Component Placement (Enhancement):** Gamification logic (e.g., `xp_service.py`, `level_system.py`) should reside in a new `gamification` module within `app/services`. Gamification models (e.g., `user_progress_model.py`) should be in `app/models`. UI components (views, widgets for dashboard, notifications) should be in `app/ui/gamification`.
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
- Detailed architectural guidance, implementation specifics (XP calculation, leveling system, data model, notifications), and project structure notes integrated.
- References section verified as correct.

### File List

- _bmad-output/implementation-artifacts/2-6-implement-gamified-progress-tracking-levels-xp.md (updated)
- _bmad-output/planning-artifacts/epics.md (referenced)
- _bmad-output/implementation-artifacts/sprint-status.yaml (referenced)


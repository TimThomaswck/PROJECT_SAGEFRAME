---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments:
  - C:\Users\LEGION\Documents\PROJECT_SAGEFRAME\_bmad-output\planning-artifacts\prd.md
  - C:\Users\LEGION\Documents\PROJECT_SAGEFRAME\_bmad-output\planning-artifacts\architecture.md
---

# PROJECT_SAGEFRAME - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for PROJECT_SAGEFRAME, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: A User can receive proactive, context-aware suggestions and guidance from the AI Co-Pilot.
FR2: A User can check-in with their current mood or energy level.
FR3: The System can suggest tasks to the User based on their logged mood and energy level.
FR4: The System's AI persona (The Co-Pilot) must communicate in a calm, supportive, and non-intrusive tone.
FR5: A User can navigate the application and execute primary actions using keyboard shortcuts.
FR6: A User can view a reference menu for all available keyboard shortcuts.
FR7: A User can customize the application's appearance (e.g., light/dark theme).
FR8: A User can undo their last action.
FR9: A User can create, view, edit, and delete a Project.
FR10: A User can create, view, edit, and delete a Task within a Project or as a standalone item.
FR11: A User can assign properties to a task, such as priority and complexity.
FR12: A User can view their tasks and projects in a Kanban board layout.
FR13: A User can view their tasks and projects in a Gantt chart layout.
FR14: A User can see their progress through a gamified system (levels, XP) based on task completion.
FR15: A User can capture unstructured information (e.g., thoughts, ideas, notes) into a quick-capture inbox.
FR16: A User can capture information using smart tags (e.g., `@movie`, `@book`) for automatic categorization and enrichment.
FR17: The System can automatically enrich tagged content with relevant metadata from external sources.
FR18: A user can import a bill or note (image/PDF) into the application.
FR19: The system can extract key information (raw text, entities, suggested tasks) from the imported file.
FR20: A User can connect their external calendar (e.g., Google Calendar) for bi-directional synchronization.
FR21: The System can read the user's calendar to identify free/busy times.
FR22: The System can create, update, and delete events in the user's external calendar.
FR23: The System can proactively suggest scheduling social or professional engagements based on calendar availability and user tasks.
FR24: A User's data must be stored on their local device by default.
FR27: The System must operate on the Windows desktop platform.
FR30: The user can perform one-click actions on the extracted information (e.g., create a task).
FR31: A user can break down a task into a checklist of subtasks.
FR32: The system can remind the user of overdue or untouched tasks.
FR33: A user can manually estimate the energy/effort required for a task (e.g., small, medium, large).
FR34: A user can create a time block for a task and push it to their Google Calendar.
FR35: The system can sync events from SageFrame to Google Calendar (one-way).
FR36: The system can provide basic intelligent scheduling suggestions.
FR37: A user can track simple habits with daily checkmarks.
FR38: A user can use a Pomodoro timer to help them focus.
FR39: A user can use tags and smart filters with AND/OR logic to organize and find information.

### NonFunctional Requirements

NFR1: Core Action Responsiveness: User interactions for core actions (e.g., creating a task, logging mood, marking task complete) shall have an immediate visual response, perceived as instantaneous (<100ms visual feedback).
NFR2: UI Fluidity: Transitions between different application tabs, sections, and views shall be fluid and smooth, with no noticeable lag or stutter (<200ms for full content load and display).
NFR3: Data Isolation (Local-First): All user data stored locally on the device shall be isolated from other applications and protected by standard operating system security measures.
NFR4: Cloud Sync Security: Data synchronized to user-controlled cloud storage (e.g., Google Drive) shall utilize secure authentication protocols (e.g., OAuth 2.0) and data encryption during transit. For the initial MVP, encryption at rest for cloud data relies on the cloud provider's capabilities.
NFR5: Modular Feature Scalability: The system architecture shall be designed to allow for the addition of new modular features and API integrations without requiring significant re-architecting of the core platform.
NFR6: Single User Focus: The system shall prioritize optimal performance and stability for a single, individual user. High concurrent user load is not a primary scalability concern for the MVP.
NFR7: Basic Accessibility Standards: The application shall adhere to basic accessibility guidelines (e.g., keyboard navigability, clear focus indicators, readable font sizes and contrast) to ensure usability for a broad audience. (Based on our target audience and general best practices).
NFR8: Integration Failure Handling: In the event of an integration failure (e.g., calendar sync error), the system shall automatically attempt to retry the operation a configurable number of times.
NFR9: Manual Reconnection/Intervention: If automatic retries fail, the system shall provide clear user prompts for manual reconnection or intervention to resolve integration issues.
NFR10: System Availability: Sageframe shall aim for 99.9% availability during active use, minimizing unexpected crashes or unresponsiveness.
NFR11: Data Recovery: In the event of an application crash or unexpected shutdown, the system shall automatically recover to the last known consistent state of user data and application settings. User data loss should be prevented as much as technically feasible.

### Additional Requirements

-   **Starter Template:** The project will be initialized using **PySide6** via `pyside-cli`.
    -   `pip install pyside-cli`
    -   `pyside-cli create sageframe_desktop`
    -   *This project initialization should be the first implementation story.*
-   **Technology Stack:** Strictly **Python-only**.
-   **Platform Priority:** **Windows desktop first**, Android mobile to follow.
-   **Dependencies:** External calendar APIs and automation service APIs (IFTTT/Zapier).
-   **Local Database:** SQLite, managed with SQLAlchemy (ORM) and Alembic for migrations.
-   **Data Validation:** Hybrid approach using SQLAlchemy and Pydantic.
-   **Caching:** Hybrid of in-memory (`functools.lru_cache`) and SQLite optimizations.
-   **Cloud Sync Authentication:** OAuth 2.0 with user-controlled cloud providers.
-   **Data Encryption:** OS-level encryption for local data, HTTPS/TLS for data in transit.
-   **User-Accessible API:** RESTful API with OpenAPI (Swagger) documentation, standard HTTP status codes, JSON payloads, and Token Bucket rate limiting.
-   **Frontend Architecture:** MVVM pattern with Atomic Design principles for PySide6 UI.
-   **Hosting Strategy:** Primarily client-side with direct cloud provider API integration.
-   **CI/CD Pipeline:** GitHub Actions for builds, tests, and releases.
-   **Monitoring & Logging:** Local-first logging with opt-in telemetry/crash reporting.
-   **Development Standards (for all AI Agents):**
    -   Adhere to PEP 8 for Python.
    -   Use `snake_case` for database and JSON fields.
    -   PySide6 Signals & Slots with `verbNoun` naming and Pydantic.
    -   `snake_case` for API parameters, `kebab-case` for HTTP headers.
    -   JSON Envelope for API responses.
    -   Integrate with global error handling and loading states.

### FR Coverage Map

FR1: Epic 1 - Initial System Setup & Core Experience
FR2: Epic 1 - Initial System Setup & Core Experience
FR3: Epic 1 - Initial System Setup & Core Experience
FR4: Epic 1 - Initial System Setup & Core Experience
FR5: Epic 1 - Initial System Setup & Core Experience
FR6: Epic 1 - Initial System Setup & Core Experience
FR7: Epic 1 - Initial System Setup & Core Experience
FR8: Epic 1 - Initial System Setup & Core Experience
FR9: Epic 2 - Comprehensive Task & Project Management
FR10: Epic 2 - Comprehensive Task & Project Management
FR11: Epic 2 - Comprehensive Task & Project Management
FR12: Epic 2 - Comprehensive Task & Project Management
FR13: Epic 2 - Comprehensive Task & Project Management
FR14: Epic 2 - Comprehensive Task & Project Management
FR15: Epic 3 - Effortless Information Capture & Curation
FR16: Epic 3 - Effortless Information Capture & Curation
FR17: Epic 3 - Effortless Information Capture & Curation
FR18: Epic 3 - Effortless Information Capture & Curation
FR19: Epic 3 - Effortless Information Capture & Curation
FR20: Epic 4 - Intelligent Calendar & Proactive Scheduling
FR21: Epic 4 - Intelligent Calendar & Proactive Scheduling
FR22: Epic 4 - Intelligent Calendar & Proactive Scheduling
FR23: Epic 4 - Intelligent Calendar & Proactive Scheduling
FR24: Epic 5 - Secure Data Management & Portability
FR27: Epic 6 - Extensibility & Platform Integration
FR30: Epic 3 - Effortless Information Capture & Curation
FR31: Epic 2 - Comprehensive Task & Project Management
FR32: Epic 2 - Comprehensive Task & Project Management
FR33: Epic 2 - Comprehensive Task & Project Management
FR34: Epic 4 - Intelligent Calendar & Proactive Scheduling
FR35: Epic 4 - Intelligent Calendar & Proactive Scheduling
FR36: Epic 4 - Intelligent Calendar & Proactive Scheduling
FR36: Epic 4 - Intelligent Calendar & Proactive Scheduling
FR37: Epic 7 - Focus and Well-being
FR38: Epic 7 - Focus and Well-being
FR39: Epic 3 - Effortless Information Capture & Curation

## Epic List

### Epic 1: Initial System Setup & Core Experience
Users can install Sageframe, get familiar with its basic interface, and interact with the empathetic AI co-pilot for initial guidance and mood check-ins. This epic establishes the foundational user experience and sets the stage for all other features.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8

### Story 1.1: Initialize the PySide6 Desktop Application

As a new user,
I want to run the application for the first time,
So that I can see the basic window and verify the system is set up correctly.

**Acceptance Criteria:**

*   **Given** a developer has the required Python environment setup,
    **When** they run the `pyside-cli create sageframe_desktop` command,
    **Then** a new project directory named `sageframe_desktop` is created with the standard PySide6 structure.
*   **Given** the project has been created,
    **When** the developer runs the main application entry point (e.g., `python src/main.py`),
    **Then** a basic, empty application window appears on the screen without errors.
*   **Given** the project is created,
    **Then** the project's dependencies and structure must strictly adhere to the Python-only technology stack constraint.

### Story 1.2: Implement Basic Application Window and Theming

As a user,
I want the application to display a main window with a defined default theme,
So that the interface is visually consistent and I can perceive it as part of the Sageframe experience.

**Acceptance Criteria:**

*   **Given** the application is launched,
    **When** the main application window appears,
    **Then** it displays a clean, minimalist design consistent with the Sageframe aesthetic.
*   **Given** the application is launched,
    **Then** the default theme (e.g., light or dark mode) is applied, with appropriate color schemes and typography based on the defined UI/UX.
*   **Given** the application is launched,
    **Then** the UI elements respond smoothly, without noticeable lag or stutter, adhering to NFR2.

### Story 1.3: Implement Mood Check-in

As a user,
I want to easily check-in with my current mood or energy level,
So that the system can understand my state and offer relevant support.

**Acceptance Criteria:**

*   **Given** the application is running,
    **When** the user initiates a mood check-in (e.g., via a dedicated button or prompt),
    **Then** a clear and intuitive interface is presented for the user to select or input their current mood/energy level.
*   **Given** the user has selected their mood/energy level,
    **When** they confirm their selection,
    **Then** the system records this information without errors.
*   **Given** a mood check-in is initiated,
    **Then** the interaction should be responsive (<100ms visual feedback) and fluid (NFR1, NFR2).

### Story 1.4: Implement Empathetic AI Co-Pilot Communication

As a user,
I want the AI Co-Pilot to communicate with me in a calm, supportive, and non-intrusive tone,
So that I feel understood and encouraged, enhancing my well-being and productivity.

**Acceptance Criteria:**

*   **Given** the AI Co-Pilot provides any form of textual communication (e.g., suggestions, feedback, prompts),
    **When** the user reads the communication,
    **Then** the tone and language used are consistently calm, supportive, and non-intrusive.
*   **Given** the AI Co-Pilot communicates,
    **Then** the communication is delivered in a manner that respects user context and does not interrupt critical tasks or flow states.
*   **Given** the AI Co-Pilot generates communication,
    **Then** the system ensures the communication avoids jargon, overly technical language, or anything that might cause user anxiety or confusion.

### Story 1.5: Implement Proactive Suggestions based on Mood

As a user,
I want the AI Co-Pilot to offer proactive suggestions based on my current mood and energy level,
So that I can receive timely guidance that aligns with my well-being and helps me make appropriate progress.

**Acceptance Criteria:**

*   **Given** the user has logged their mood/energy level (via Story 1.3),
    **When** the AI Co-Pilot presents suggestions,
    **Then** these suggestions are contextually relevant to the logged mood/energy level (e.g., if low energy, suggest lighter tasks or breaks).
*   **Given** the AI Co-Pilot provides proactive suggestions,
    **Then** the suggestions are delivered non-intrusively, adhering to the communication style defined in Story 1.4.
*   **Given** a suggestion is provided,
    **Then** the user can easily dismiss or act upon the suggestion.
*   **Given** the system suggests tasks,
    **Then** the tasks presented are from the user's available task list.

### Story 1.6: Implement Keyboard Shortcut Navigation & Help Menu

As a power user,
I want to efficiently navigate the application and execute primary actions using keyboard shortcuts, and view a reference menu for them,
So that I can maximize my productivity and avoid relying solely on mouse interaction.

**Acceptance Criteria:**

*   **Given** the application is running,
    **When** the user attempts to perform primary actions (e.g., open a specific view, save, create new item) using designated keyboard shortcuts,
    **Then** the application responds correctly and immediately to the shortcut, executing the action.
*   **Given** the application is running,
    **When** the user triggers the shortcut help functionality (e.g., by pressing `?` or a dedicated hotkey),
    **Then** a comprehensive and easily accessible reference menu of all available keyboard shortcuts is displayed.
*   **Given** the shortcut help menu is displayed,
    **Then** it is clearly organized and easy to read, with shortcuts categorized logically.
*   **Given** the application focuses on keyboard-first navigation (as per architecture),
    **Then** a significant portion of core interactions are accessible via keyboard shortcuts.

### Story 1.7: Implement Undo Functionality

As a user,
I want to be able to undo my last action in the application,
So that I can correct mistakes or revert unintended changes without losing work.

**Acceptance Criteria:**

*   **Given** the user performs an action that modifies application state (e.g., enters text, changes a setting, performs a drag-and-drop),
    **When** the user invokes the "undo" command (e.g., Ctrl+Z or a dedicated button),
    **Then** the application successfully reverts to the state before the last action.
*   **Given** multiple actions have been performed,
    **When** the user repeatedly invokes the "undo" command,
    **Then** the application reverts actions in reverse chronological order, step by step, for a reasonable history depth (e.g., last 10 actions).
*   **Given** there are no actions to undo,
    **When** the user attempts to invoke the "undo" command,
    **Then** the undo action is gracefully disabled or provides feedback that there's nothing to undo.
*   **Given** the user performs an action that cannot be undone (e.g., closing the application, permanently deleting data, if applicable),
    **Then** the system provides a warning or prevents the undo action for such critical operations.

### Epic 2: Comprehensive Task & Project Management
Users can effectively organize their work and personal life by creating, managing, and tracking projects and tasks, visualizing their progress and gamified achievements.
**FRs covered:** FR9, FR10, FR11, FR12, FR13, FR14

### Story 2.1: Create, View, Edit, and Delete a Project

As a user,
I want to create, view, edit, and delete projects,
So that I can organize my work and personal life into distinct initiatives.

**Acceptance Criteria:**

*   **Given** I am using the application,
    **When** I initiate project creation,
    **Then** I am presented with an interface to define a new project (e.g., name, description).
*   **Given** a project exists,
    **When** I select to view it,
    **Then** its details (e.g., name, description, associated tasks) are clearly displayed.
*   **Given** a project exists,
    **When** I select to edit its details,
    **Then** I am able to modify its attributes and save the changes.
*   **Given** a project exists,
    **When** I select to delete it,
    **Then** the project is removed from my list, and I am prompted for confirmation if it contains active tasks.
*   **Given** I am performing any project management operation,
    **Then** the interaction is responsive and fluid (NFR1, NFR2).

### Story 2.2: Create, View, Edit, and Delete a Task

As a user,
I want to create, view, edit, and delete tasks, both as standalone items and within projects,
So that I can manage my to-do list and break down larger initiatives.

**Acceptance Criteria:**

*   **Given** I am using the application,
    **When** I initiate task creation (e.g., from a project view or a general task list),
    **Then** I am presented with an interface to define a new task (e.g., title, description, due date).
*   **Given** a task exists,
    **When** I select to view it,
    **Then** its details (e.g., title, description, due date, associated project) are clearly displayed.
*   **Given** a task exists,
    **When** I select to edit its details,
    **Then** I am able to modify its attributes and save the changes.
*   **Given** a task exists,
    **When** I select to delete it,
    **Then** the task is removed from my list, and I am prompted for confirmation.
*   **Given** a project exists (from Story 2.1),
    **When** I create a new task,
    **Then** I can associate it with an existing project.
*   **Given** I am performing any task management operation,
    **Then** the interaction is responsive and fluid (NFR1, NFR2).

### Story 2.3: Assign Properties to a Task

As a user,
I want to assign properties like priority and complexity to my tasks,
So that I can better organize and understand the relative importance and effort required for each task.

**Acceptance Criteria:**

*   **Given** an existing task (from Story 2.2),
    **When** I access its edit interface,
    **Then** I am presented with options to assign its priority (e.g., High, Medium, Low) and complexity (e.g., Simple, Moderate, Complex).
*   **Given** I assign new properties to a task,
    **When** I save the changes,
    **Then** the task's properties are updated and persistently stored.
*   **Given** a task has assigned properties,
    **When** I view the task,
    **Then** its priority and complexity are clearly displayed.
*   **Given** I am assigning properties to a task,
    **Then** the interaction is responsive and fluid (NFR1, NFR2).

### Story 2.4: Display Tasks and Projects in Kanban View

As a user,
I want to view my tasks and projects in a Kanban board layout,
So that I can easily visualize my workflow, track progress, and manage items through different stages.

**Acceptance Criteria:**

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

### Story 2.5: Display Tasks and Projects in Gantt Chart View

As a user,
I want to view my tasks and projects in a Gantt chart layout,
So that I can visualize timelines, dependencies, and overall project progress more effectively.

**Acceptance Criteria:**

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

### Story 2.6: Implement Gamified Progress Tracking (Levels & XP)

As a user,
I want to see my progress visualized through a gamified system of levels and experience points (XP) based on task completion,
So that I feel motivated, encouraged, and rewarded for my productivity efforts.

**Acceptance Criteria:**

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

### Story 2.7: Hierarchical Tasks (1-level subtasks)

As a user,
I want to break down my tasks into a simple checklist of subtasks,
So that I can manage more complex tasks without being overwhelmed.

**Acceptance Criteria:**

*   **Given** I am viewing a task,
    **When** I choose to add a subtask,
    **Then** I can add, edit, and delete subtasks in a checklist format.
*   **Given** a task has subtasks,
    **When** I mark a subtask as complete,
    **Then** the subtask is visually marked as done.
*   **Given** a task has subtasks,
    **Then** the main task's progress is visually updated as I complete subtasks.

### Story 2.8: Basic Task Suggestions (Overdue/Untouched Reminders)

As a user,
I want to be reminded of overdue or untouched tasks,
So that nothing falls through the cracks.

**Acceptance Criteria:**

*   **Given** a task is overdue,
    **When** I view my task list,
    **Then** the system will highlight it.
*   **Given** a task has not been updated for a configurable period (e.g., 7 days),
    **When** I view my task list,
    **Then** the system will suggest I review it.

### Story 2.9: Manual Energy/Effort Estimation

As a user,
I want to manually estimate the energy/effort required for a task (e.g., small, medium, large),
So that I can better plan my day based on my energy levels.

**Acceptance Criteria:**

*   **Given** I am creating or editing a task,
    **When** I choose to estimate the effort,
    **Then** I can select an energy/effort level from a predefined list (e.g., Small, Medium, Large).
*   **Given** a task has an energy/effort level,
    **When** I view my task list,
    **Then** the energy/effort level is clearly displayed.

### Epic 3: Effortless Information Capture & Curation
Users can quickly and easily capture various forms of information—from unstructured thoughts to structured data in bills and notes—and have it intelligently organized, enriched, and made actionable for future retrieval and task management.
**FRs covered:** FR15, FR16, FR17, FR18, FR19, FR30

### Story 3.1: Implement Smart Tagging for Automatic Categorization

As a user,
I want to use smart tags (e.g., `@movie`, `@book`) when capturing information,
So that my content is automatically categorized and easily retrievable.

**Acceptance Criteria:**

*   **Given** I am capturing information (e.g., in the quick-capture inbox from Story 3.1),
    **When** I type a predefined smart tag format (e.g., `@tag: content` or just `@tag`),
    **Then** the system recognizes and highlights the smart tag.
*   **Given** information containing smart tags is saved,
    **When** I later view or search my captured information,
    **Then** the smart tags facilitate filtering, categorization, or searching for content associated with that tag.
*   **Given** a smart tag is recognized,
    **Then** the system stores the tag and its associated content in a structured way that supports later enrichment (Story 3.2).
*   **Given** I am entering smart tags,
    **Then** the input experience is responsive and fluid (NFR1, NFR2).

### Story 3.2: Automatically Enrich Tagged Content from External Sources

As a user,
I want content tagged with smart tags (e.g., `@movie`, `@book`) to be automatically enriched with relevant metadata from external sources,
So that I have more complete and useful information without manual effort.

**Acceptance Criteria:**

*   **Given** information containing a recognized smart tag (e.g., `@movie: Inception`) is saved (from Story 3.1),
    **When** the system processes this tagged content,
    **Then** it automatically queries an appropriate external source (e.g., a movie database API for `@movie` tags).
*   **Given** an external source is successfully queried,
    **Then** relevant metadata (e.g., director, cast, release year for a movie) is retrieved and associated with the captured information.
*   **Given** the enriched metadata is available,
    **Then** it is displayed alongside the original captured information when viewed (e.g., in a details panel or popup).
*   **Given** an external source query fails or returns no data,
    **Then** the system gracefully handles the failure, possibly logging the error without disrupting the user experience, and does not display incomplete or incorrect enrichment.

### Story 3.3: Import and Extract Information from Bills and Notes

As a user,
I can import a bill or note (image/PDF) and have SageFrame extract key info and store it, with one-click actions to create tasks.

**Acceptance Criteria:**

*   **Given** the user is in the application,
    **When** they initiate file import via drag/drop or a file picker,
    **Then** the import works for supported file types (.png, .jpg, .pdf).
*   **Given** a file is imported,
    **When** the import is complete,
    **Then** the original file is stored locally (e.g., under `data/ingest/<uuid>/original.ext`) and is viewable later.
*   **Given** a file is imported,
    **When** the extraction process runs,
    **Then** it does not freeze the UI (runs in a separate thread/asynchronously).
*   **Given** a PDF with selectable text is imported,
    **When** the extraction runs,
    **Then** the text is extracted locally without an API call.
*   **Given** an image-based file or PDF without selectable text is imported,
    **When** the extraction runs,
    **Then** an external API is used for OCR and data extraction, returning structured JSON.
*   **Given** the extraction is complete,
    **When** the results are displayed,
    **Then** the extracted information is shown to the user and is editable.
*   **Given** the extracted information is displayed,
    **When** the user clicks the "Create task" action,
    **Then** a new task is created using the extracted information.
*   **Given** the user re-runs extraction on the same file,
    **When** the extraction completes,
    **Then** it overwrites or versions the previous results, avoiding duplication.

### Story 3.4: Tags & Smart Filters

As a user,
I want to use tags and smart filters with AND/OR logic,
So that I can organize and find my information more effectively.

**Acceptance Criteria:**

*   **Given** I am creating or editing a note or task,
    **When** I choose to add tags,
    **Then** I can add one or more tags.
*   **Given** I am viewing my notes or tasks,
    **When** I choose to filter,
    **Then** I can filter them by one or more tags.
*   **Given** I am filtering,
    **When** I apply multiple filters,
    **Then** I can use AND/OR logic to combine them.
*   (Note: This does not include a full rule engine, just simple filtering logic).

### Epic 4: Intelligent Calendar & Proactive Scheduling
Users can connect their existing calendars, have Sageframe intelligently identify free time, and proactively suggest social and professional engagements, reducing scheduling friction.
**FRs covered:** FR20, FR21, FR22, FR23

### Story 4.1: Connect External Calendar for Bi-Directional Synchronization

As a user,
I want to connect my external calendar (e.g., Google Calendar) for bi-directional synchronization, including the ability to push SageFrame events one-way to the external calendar,
So that Sageframe can have an accurate, up-to-date view of my schedule and help manage my time, and I can see all my SageFrame events in my external calendar.

**Acceptance Criteria:**

*   **Given** I am in the application's settings,
    **When** I select the option to connect a new calendar,
    **Then** I am guided through a secure OAuth 2.0 flow to authenticate with my chosen calendar provider (e.g., Google).
*   **Given** I have successfully authenticated my external calendar,
    **When** the connection is established,
    **Then** Sageframe performs an initial synchronization of my calendar events.
*   **Given** the calendar is connected,
    **When** a new event is created or updated in Sageframe,
    **Then** the change is reflected in my external calendar (this includes one-way sync functionality from Sageframe to external calendar, fulfilling FR35).
*   **Given** the calendar is connected,
    **When** a new event is created or updated in my external calendar,
    **Then** the change is reflected in Sageframe.
*   **Given** any synchronization issue occurs (as per NFR8),
    **Then** the system handles the error gracefully, attempts to retry, and provides a clear prompt for manual intervention if necessary (NFR9).

### Story 4.2: Read Calendar to Identify Free/Busy Times

As a user,
I want Sageframe to read my connected calendar and identify my free and busy times,
So that the system can understand my availability and make informed suggestions for scheduling.

**Acceptance Criteria:**

*   **Given** an external calendar is successfully connected (from Story 4.1),
    **When** Sageframe accesses the calendar data,
    **Then** it accurately distinguishes between time slots marked as "free" and "busy" based on event entries.
*   **Given** Sageframe has identified free/busy times,
    **Then** this availability information is stored internally in a format that can be easily queried by other Sageframe features (e.g., proactive scheduling).
*   **Given** my calendar contains recurring events or all-day events,
    **Then** Sageframe correctly interprets these to mark the corresponding time as busy or free as appropriate.
*   **Given** I am performing any operation related to calendar reading,
    **Then** the interaction is responsive and fluid (NFR1, NFR2), and data privacy is respected as per NFR3.

### Story 4.3: Create, Update, and Delete Calendar Events

As a user,
I want Sageframe to be able to create, update, and delete events directly in my connected external calendar,
So that I can manage my schedule through Sageframe and ensure my calendar is always accurate without switching applications.

**Acceptance Criteria:**

*   **Given** an external calendar is connected (from Story 4.1),
    **When** I create a new event within Sageframe,
    **Then** this event is successfully created in my external calendar.
*   **Given** an event exists in my external calendar and is displayed in Sageframe,
    **When** I modify that event's details (e.g., time, title, description) within Sageframe,
    **Then** the changes are successfully updated in my external calendar.
*   **Given** an event exists in my external calendar and is displayed in Sageframe,
    **When** I delete that event within Sageframe,
    **Then** the event is successfully deleted from my external calendar.
*   **Given** any operation to create, update, or delete an event fails (as per NFR8),
    **Then** the system handles the error gracefully, attempts to retry, and provides a clear prompt for manual intervention if necessary (NFR9).
*   **Given** I am performing any calendar event management operation,
    **Then** the interaction is responsive and fluid (NFR1, NFR2).

### Story 4.4: Proactively Suggest Engagements Based on Availability

As a user,
I want Sageframe to proactively suggest social or professional engagements based on my calendar availability and user tasks,
So that I can maintain a balanced life, nurture relationships, and optimize my schedule without manual effort.

**Acceptance Criteria:**

*   **Given** an external calendar is connected (from Story 4.1) and free/busy times are identified (from Story 4.2),
    **When** the AI Co-Pilot (from Epic 1) recognizes opportunities for scheduling (e.g., a long free block, a pending task related to social outreach),
    **Then** it proactively suggests a social or professional engagement (e.g., "You have a 2-hour free slot on Tuesday afternoon, would you like to schedule a coffee chat with [Contact Name]?").
*   **Given** a suggestion is made,
    **When** I accept the suggestion,
    **Then** Sageframe uses its event creation capabilities (from Story 4.3) to schedule the engagement in my external calendar.
*   **Given** a suggestion is made,
    **When** I decline or dismiss the suggestion,
    **Then** Sageframe learns from my preferences and adjusts future proactive suggestions.
*   **Given** Sageframe suggests an engagement,
    **Then** the suggestion is non-intrusive and aligned with the empathetic communication style (from Story 1.4).
*   **Given** I am receiving proactive suggestions,
    **Then** the process is responsive and fluid (NFR1, NFR2).

### Story 4.5: Time Blocking with Google Calendar Integration

As a user,
I want to create a time block for a task and push it to my Google Calendar,
So that I can dedicate specific time for my tasks.

**Acceptance Criteria:**

*   **Given** I am viewing a task,
    **When** I choose to create a time block,
    **Then** I can create a time block with a start and end time.
*   **Given** I have created a time block,
    **When** I choose to push it to my calendar,
    **Then** it is sent to my connected Google Calendar as an event (relying on functionality from Story 4.3).

### Story 4.6: Intelligent Scheduling (Lite)

As a user,
I want the system to provide basic intelligent scheduling suggestions,
So that I can get help with planning my day.

**Acceptance Criteria:**

*   **Given** my connected calendar,
    **When** I ask for scheduling suggestions,
    **Then** the system can identify my free slots (relying on functionality from Story 4.2).
*   **Given** my task list,
    **When** I ask for scheduling suggestions,
    **Then** the system can suggest which tasks to work on based on their due date and my free slots.

### Epic 5: Secure Data Management & Portability
Users have control over their personal data, knowing it's stored locally by default, ensuring privacy.
**FRs covered:** FR24

### Story 5.1: Implement Local-First Data Storage as Default

As a user,
I want my data to be stored on my local device by default,
So that I have complete control over my information and can ensure my privacy.

**Acceptance Criteria:**

*   **Given** I am using the application,
    **When** any data is created or modified (e.g., tasks, notes, projects),
    **Then** this data is written to a local database (SQLite as per Architecture) on my device.
*   **Given** the application is running without an internet connection,
    **Then** all core functionalities that rely on my data (e.g., viewing tasks, creating notes) remain fully operational.
*   **Given** my data is stored locally,
    **Then** the application adheres to standard operating system security measures to protect the data from unauthorized access (as per NFR3).
*   **Given** I am using the application,
    **Then** the local data storage is efficient and does not negatively impact application performance (NFR1, NFR2).
### Epic 6: Extensibility & Platform Integration
Users can trust that the system operates reliably within its defined technical boundaries by running Sageframe on the Windows desktop platform.
**FRs covered:** FR27

### Story 6.1: Implement Windows Desktop Platform Support

As a user,
I want to run Sageframe on the Windows desktop platform,
So that I can use the application on my primary operating system.

**Acceptance Criteria:**

*   **Given** the application is built,
    **When** I run the installer or executable on a Windows desktop,
    **Then** the application installs and launches correctly without platform-specific errors.
*   **Given** the application is running on Windows,
    **Then** it integrates as expected with the operating system (e.g., appears in the taskbar, can be pinned to the start menu, and can be properly uninstalled).
*   **Given** the application is running on Windows,
    **Then** all features defined in previous stories function as expected within the Windows environment.
*   **Given** the application is built for Windows,
    **Then** the CI/CD pipeline (as per Architecture) produces a valid Windows installer or executable.

### Epic 7: Focus and Well-being
Users can improve their focus and build positive routines through integrated tools that support focused work sessions and simple habit tracking.
**FRs covered:** FR37, FR38

### Story 7.1: Simple Habit Tracker

As a user,
I want to track simple habits with daily checkmarks,
So that I can build positive routines.

**Acceptance Criteria:**

*   **Given** I am in the habit tracking section,
    **When** I create a new habit,
    **Then** I can create and name a new habit.
*   **Given** a habit exists,
    **When** I complete the habit for the day,
    **Then** I can mark it as complete with a single click.
*   **Given** a habit exists,
    **When** I view my habits,
    **Then** I can see my progress for the current week/month.
*   (Note: No complex streak math or analytics are included in this story).

### Story 7.2: Pomodoro & Focus Mode

As a user,
I want to use a Pomodoro timer to help me focus,
So that I can work in focused bursts.

**Acceptance Criteria:**

*   **Given** I want to focus on a task,
    **When** I start a timer,
    **Then** I can start a Pomodoro timer (e.g., 25 minutes).
*   **Given** the timer is running,
    **When** I am in the application,
    **Then** the application enters a "focus mode" with minimal UI distractions.
*   **Given** the timer completes,
    **When** the time is up,
    **Then** the system notifies me to take a short break.
*   (Note: No analytics or tracking of Pomodoro sessions is included in this story).

<!-- Repeat for each epic in epics_list (N = 1, 2, 3...) -->

## Epic {{N}}: {{epic_title_N}}

{{epic_goal_N}}

<!-- Repeat for each story (M = 1, 2, 3...) within epic N -->

### Story {{N}}.{{M}}: {{story_title_N_M}}

As a {{user_type}},
I want {{capability}},
So that {{value_benefit}}.

**Acceptance Criteria:**

<!-- for each AC on this story -->

**Given** {{precondition}}
**When** {{action}}
**Then** {{expected_outcome}}
**And** {{additional_criteria}}

<!-- End story repeat -->

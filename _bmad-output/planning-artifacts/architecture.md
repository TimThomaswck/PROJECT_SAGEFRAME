---
stepsCompleted: ['step-01-init', 'step-02-context', 'step-03-starter', 'step-04-decisions', 'step-05-patterns', 'step-06-structure']
inputDocuments:
  - C:\Users\LEGION\Documents\PROJECT_SAGEFRAME\_bmad-output\planning-artifacts\prd.md
  - C:\Users\LEGION\Documents\PROJECT_SAGEFRAME\_bmad-output\planning-artifacts\prd-validation-report.md
  - C:\Users\LEGION\Documents\PROJECT_SAGEFRAME\_bmad-output\implementation-artifacts\Project_Sageframe_Product_Brief_2026-01-22_v1.0.md
  - C:\Users\LEGION\Documents\PROJECT_SAGEFRAME\_bmad-output\analysis\brainstorming-session-2026-01-19.md
workflowType: 'architecture'
project_name: 'PROJECT_SAGEFRAME'
user_name: 'Timothy'
date: '2026-01-24'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
The system is defined by 29 functional requirements across 6 capability areas, including Core User Experience, Task Management, Information Capture, Scheduling, Data Platform, and Integrations. Architecturally, this translates to a system that must support a rich, interactive, and intelligent user experience, with a clear separation of concerns between local data management and cloud-based services.

**Non-Functional Requirements:**
The architecture will be heavily influenced by the following critical NFRs:
*   **Performance:** A core requirement is "instant" responsiveness (<100ms) for all primary user actions and fluid UI transitions (<200ms), which will drive decisions around the local data stack and rendering technology.
*   **Security:** The "local-first" data model is a primary security and privacy feature. The architecture must ensure robust data isolation on the user's device and secure synchronization with user-controlled cloud storage.
*   **Reliability:** The system must be highly reliable, with a 99.9% availability target, necessitating a robust error handling and data recovery strategy.

**Scale & Complexity:**
*   **Primary domain:** Full-Stack (Desktop, Cloud Services, Integrations)
*   **Complexity level:** Medium
*   **Estimated architectural components:** Initial estimates suggest a modular architecture with at least 5-7 major components (e.g., UI, Local Data Store, AI Engine, Sync Service, API Gateway).

### Technical Constraints & Dependencies

*   **Technology Stack:** The project is strictly constrained to a **Python-only** technology stack.
*   **Platform Priority:** The initial release must target the **Windows desktop platform**, with Android development to follow. This requires an architectural approach that facilitates future cross-platform expansion.
*   **Dependencies:** The system will depend on external calendar APIs and automation service APIs (IFTTT/Zapier), requiring a resilient integration layer.

### Cross-Cutting Concerns Identified

The following concerns will influence multiple parts of the architecture:
*   **AI/ML:** The empathetic co-pilot is a core feature that will require a dedicated AI engine and a clear interface with the rest of the system.
*   **Security & Privacy:** The "local-first" data model is a fundamental principle that must be woven into every component.
*   **Multi-tenancy:** The cloud backend must be designed to securely and efficiently serve multiple users.
*   **Cross-Platform:** Architectural decisions for the Windows application should consider future reuse and adaptation for the Android platform.

## Starter Template Evaluation

### Primary Technology Domain

Based on the project requirements, the primary technology domain is **Desktop Application Development** using the **Python** ecosystem.

### Starter Options Considered

*   **PyQt/PySide:** A powerful and mature framework for building native desktop applications. Offers extensive styling capabilities suitable for the desired RPG-style UI and strong cross-platform support for future Android development.
*   **NiceGUI:** A modern, Pythonic framework for building web-based UIs that can be wrapped as desktop applications. Offers simplicity and rapid development but may have limitations for deep native OS integration.

### Selected Starter: PySide6 (via `pyside-cli`)

**Rationale for Selection:**
We have selected **PySide6** as our foundational framework. Its power, maturity, and extensive styling capabilities (via Qt Style Sheets) make it the ideal choice for creating the rich, performant, and custom "empathetic co-pilot" experience we envision. Its strong native desktop performance and clear path for future cross-platform expansion align perfectly with our Platform MVP strategy and long-term goals. The `pyside-cli` tool provides a standardized, best-practice project structure, which will accelerate initial setup.

**Initialization Command:**
The project will be initialized using the `pyside-cli` tool. The following commands should be executed to set up the starter project:
```bash
# 1. Install the CLI tool
pip install pyside-cli

# 2. Create the project (replace 'sageframe_desktop' with the desired project name)
pyside-cli create sageframe_desktop
```

**Architectural Decisions Provided by Starter:**

*   **Language & Runtime:** Python with PySide6 bindings for the Qt6 framework.
*   **Styling Solution:** Qt Style Sheets (QSS) will be used for custom styling to achieve the minimalist, RPG-style aesthetic.
*   **Build Tooling:** Standard Python build systems (e.g., `setuptools` or `poetry`) integrated with Qt's resource system.
*   **Testing Framework:** The starter provides a basic structure for `pytest`.
*   **Code Organization:** A standard project structure separating UI components, application logic, and resources.
*   **Development Experience:** Provides a clear entry point for running the application in a development environment.

**Note:** Project initialization using this command should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
All decisions made in this section are considered critical for proceeding with implementation, establishing a clear technical foundation that aligns with our PRD.

**Important Decisions (Shape Architecture):**
Each decision directly influences how components are designed and interact, addressing key functional and non-functional requirements.

**Deferred Decisions (Post-MVP):**
Complex user permission models, additional subscription tiers, and a dedicated backend for advanced AI processing have been consciously deferred to post-MVP phases to maintain a lean initial release.

### Data Architecture

*   **Local Database Choice:** **SQLite**
    *   **Rationale:** Chosen for its ubiquity, lightweight nature, and cross-platform compatibility, supporting our "local-first" principle and future Android expansion.
*   **Data Modeling Approach:** **SQLAlchemy (ORM)**
    *   **Rationale:** Provides a robust, Pythonic, and maintainable way to interact with the SQLite database, enhancing developer productivity and code quality.
*   **Data Validation Strategy:** **Hybrid Approach (SQLAlchemy + Pydantic)**
    *   **Rationale:** Combines database-level integrity with application-level business rule validation, ensuring data correctness and user-friendly error feedback.
*   **Migration Approach:** **Alembic**
    *   **Rationale:** Essential for managing database schema changes reliably, enabling safe upgrades and rollbacks without data loss, crucial for persistent user data.
*   **Caching Strategy:** **Hybrid (In-Memory + SQLite Optimizations)**
    *   **Rationale:** Leverages Python's `functools.lru_cache` for fast access to short-lived data and relies on SQLite's internal optimizations for general database performance, addressing performance NFRs.

### Authentication & Security

*   **Authentication Method (Cloud Sync):** **OAuth 2.0 with User-Controlled Cloud Providers**
    *   **Rationale:** Secure, privacy-respecting, and standard approach for third-party cloud integrations, directly supporting "local-first" and "user-controlled cloud sync" principles.
*   **Authorization Patterns (MVP):** **Implicit Authorization (User as Owner)**
    *   **Rationale:** Simplest approach for a single-user desktop application, aligning with the MVP scope and deferring complex RBAC for potential future multi-user features.
*   **Data Encryption Approach:** **OS Encryption (local) + HTTPS/TLS (in transit)**
    *   **Rationale:** Relies on robust OS-level full-disk encryption for data at rest on the user's device and industry-standard HTTPS/TLS for secure data transfer during cloud synchronization, balancing security with MVP complexity.

### API & Communication Patterns

*   **API Design Patterns (User-Accessible API):** **RESTful API**
    *   **Rationale:** The most pragmatic choice for a user-accessible API, offering broad compatibility with automation services like IFTTT/Zapier and ease of implementation for the MVP.
*   **API Documentation Approach:** **OpenAPI Specification (Swagger)**
    *   **Rationale:** Provides machine-readable, interactive documentation, crucial for a positive developer experience and seamless integration with third-party automation tools.
*   **Error Handling Standards:** **Standard HTTP Status Codes with JSON Payloads**
    *   **Rationale:** Ensures clear, consistent, and machine-readable error responses, adhering to industry best practices for external-facing APIs.
*   **Rate Limiting Strategy:** **Token Bucket Algorithm**
    *   **Rationale:** Offers a balanced approach to fairness, flexibility, and protection, preventing API abuse while accommodating legitimate bursty usage by automation tools.

### Frontend Architecture

*   **State Management Approach:** **MVVM (Model-View-ViewModel) Pattern**
    *   **Rationale:** Promotes clear separation of concerns, testability, and maintainability for the PySide6 application, leveraging Qt's property system and signals/slots for a responsive UI.
*   **Component Architecture:** **Atomic Design (Adapted for Desktop)**
    *   **Rationale:** Establishes a scalable design system for UI components, ensuring consistency and reusability for the minimalist RPG-style aesthetic.

### Infrastructure & Deployment

*   **Hosting Strategy:** **Primarily Client-Side with Direct Cloud Provider API Integration**
    *   **Rationale:** Reduces operational overhead and aligns with "local-first" principles for the MVP, with architectural hooks for future cloud-based backend expansion.
*   **CI/CD Pipeline Approach:** **GitHub Actions**
    *   **Rationale:** Automates builds, tests, and releases for the Windows desktop application, ensuring code quality and rapid iteration cycles.
*   **Monitoring and Logging Strategy:** **Local-First Logging with Opt-in Telemetry/Crash Reporting**
    *   **Rationale:** Balances user privacy with the need for actionable insights into application health and usage, enabling proactive maintenance and improvement.

### Decision Impact Analysis

**Implementation Sequence:** Architectural decisions have been made from foundational data layers through to the UI and deployment, providing a clear sequence for development. The initial focus will be on setting up the PySide6 framework, SQLAlchemy models, and core local storage.

**Cross-Component Dependencies:** The local-first data model, Python-only stack, and Windows-first platform choice are pervasive. The AI Co-Pilot will have interfaces with both UI and local data. Security and privacy considerations are woven throughout all components.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
We identified key areas where inconsistent choices could lead to conflicts between different development efforts, including naming, project structure, data formats, communication, and process handling. These patterns are designed to provide clear guidance.

### Naming Patterns

*   **Database Naming Conventions:**
    *   **Rule:** All database table and column names shall use `snake_case` (e.g., `user_accounts`, `first_name`). Primary keys will be `id`, and foreign keys `related_table_id`.
    *   **Rationale:** Ensures consistency with Pythonic conventions and improves readability for SQLAlchemy users.
*   **API Naming Conventions:**
    *   **Endpoints:** **Plural Nouns** (e.g., `/tasks`, `/users/{id}`).
    *   **Route and Query Parameters:** **`snake_case`** (e.g., `{task_id}`, `?start_date=...`).
    *   **Headers:** **`kebab-case`** (e.g., `Content-Type`, `X-RateLimit-Remaining`).
    *   **Rationale:** Adheres to RESTful best practices, HTTP standards, and maintains consistency with our Pythonic internal conventions where appropriate.
*   **Code Naming Conventions:**
    *   **Rule:** Strict adherence to **Pythonic (PEP 8)** style guide for all Python code.
    *   **Rationale:** Ensures readability, maintainability, and consistency across the codebase, integrating seamlessly with standard Python tooling.

### Structure Patterns

*   **Project Organization:**
    *   **Rule:** Project shall be **Organized by Feature**, with all related files for a given feature grouped within a dedicated directory (e.g., `src/modules/task_management/`).
    *   **Rationale:** Promotes high cohesion, modularity, and scalability, making features easier to develop and maintain independently.
*   **File Structure Patterns:**
    *   **Rule:** Within each feature module, a consistent sub-directory structure for `models.py`, `views.py`, `services.py`, `api.py`, `tests/`, and `assets/` shall be used. Top-level directories like `src/core/`, `config/`, `docs/`, `scripts/`, `resources/`, and root `tests/` will house project-wide elements.
    *   **Rationale:** Provides predictability, eases navigation, and supports both modular development and overall project coherence.

### Format Patterns

*   **API Response Formats:**
    *   **Rule:** All API responses (success and error) shall use a consistent **JSON Envelope (Wrapper)** (e.g., `{"status": "success", "data": {...}}` or `{"status": "error", "error": {...}}`).
    *   **Rationale:** Ensures predictable and robust parsing for API consumers, simplifying client-side logic and future extensibility.
*   **Data Exchange Formats:**
    *   **JSON Field Naming:** **`snake_case`**.
    *   **Date/Time Formats:** **ISO 8601 Strings (UTC)**.
    *   **Boolean Representations:** Standard **`true`/`false`**.
    *   **Null Handling:** Explicitly use **`null`**.
    *   **Rationale:** Ensures clarity, unambiguous interpretation, and alignment with Pythonic conventions and industry best practices.

### Communication Patterns

*   **Event System Patterns (PySide6 Signals & Slots):**
    *   **Event Naming Convention:** **`verbNoun` (`camelCase`)** (e.g., `taskCreated`, `userLoggedIn`).
    *   **Event Payload Structure:** **Simple Types for Simple Events, Pydantic Models for Complex Events**.
    *   **Rationale:** Promotes consistent, clear, and type-safe internal event communication, leveraging Qt's idiomatic patterns and Pydantic for data validation.

### Process Patterns

*   **Error Handling Patterns:**
    *   **Rule:** Implementation of a **Global Error Handler with User-Friendly Dialogs** that logs technical details locally but presents professional, non-crashing messages to the user.
    *   **Rationale:** Enhances application reliability, user trust, and provides a graceful user experience during unexpected issues.
*   **Loading State Patterns:**
    *   **Rule:** A **Hybrid Approach (Global for major, Contextual for minor)** shall be used for loading indicators. Global indicators for application-blocking operations, contextual indicators for localized updates.
    *   **Rationale:** Optimizes user experience by providing appropriate and non-intrusive feedback, supporting perceived performance and UI fluidity.

### Enforcement Guidelines

**All AI Agents MUST:**
*   Adhere strictly to PEP 8 for Python code styling and naming.
*   Utilize `snake_case` for database entities and JSON field names in APIs.
*   Employ PySide6's Signals & Slots with `verbNoun` naming and Pydantic models for complex payloads.
*   Implement `snake_case` for API parameters and `kebab-case` for HTTP headers.
*   Ensure all API responses follow the defined JSON Envelope and data exchange formats.
*   Integrate with the global error handling and loading state patterns.

**Pattern Enforcement:**
These patterns will be verified through code reviews, automated linting, and where applicable, automated tests. Any deviations will require justification and approval or refactoring. This document serves as the primary reference for all development efforts.

## AI/ML Integration Architecture

### LLM Service Integration

*   **Primary LLM Provider:** **Google Gemini 2.5 Flash**
    *   **Rationale:** Fast inference (\<500ms), cost-effective ($0.00001875/1K tokens), strong reasoning capabilities for task scheduling and prioritization, actively maintained by Google with improving models.
*   **Integration Pattern:** **User-Provided API Key**
    *   **Rationale:** Privacy-preserving (user controls their own API usage), no backend infrastructure needed for MVP, scales cost with user engagement, aligns with local-first philosophy.
*   **Architecture Pattern:** **Hybrid Template + LLM**
    *   **Rationale:** Templates provide instant feedback (\<100ms, meets NFR1) and offline capability, LLM provides intelligent reasoning for complex scenarios (scheduling, prioritization), graceful degradation when API unavailable.

### Agent Prompt System (Jarvis Persona)

*   **Design Pattern:** **BMAD-Style Agent Definition**
    *   **Rationale:** Reuses proven persona pattern from BMAD agents, ensures tone consistency through structured prompts, enables versioning and refinement of AI personality.
*   **Implementation Approach:**
    *   Agent definition files stored in `app/modules/ai_copilot/prompts/`
    *   Separation of concerns: communication prompts, scheduling prompts, task prioritization prompts
    *   System prompt + dynamic context injection for personalized responses
*   **Tone Enforcement:**
    *   Pre-processing: Template system ensures baseline quality
    *   LLM processing: System prompts define "Jarvis" calm, supportive, non-intrusive persona
    *   Post-processing: Tone validation filter rejects inappropriate responses, falls back to templates

### API Key Security Architecture

*   **Storage Strategy:** **Multi-Tier Secure Storage**
    *   **Primary:** System keychain (Windows Credential Manager, macOS Keychain) via `keyring` library
    *   **Fallback:** Encrypted .env file with restrictive permissions
    *   **Never:** Hardcoded in source code or committed to version control
*   **Key Management Service:**
    *   `app/modules/settings/services/api_key_manager.py`
    *   Handles secure storage, retrieval, validation, and removal
    *   No plaintext persistence anywhere in the application

### LLM Response Processing Pipeline

**Processing Stages:**
1. **Context Enrichment:** Gather user mood, task list, calendar data, preferences
2. **Prompt Construction:** Build agent-appropriate system prompt + user context
3. **LLM Generation:** Async Gemini API call (target \<500ms)
4. **Response Validation:** Check tone compliance, content safety, format correctness
5. **Fallback Handling:** If validation fails or API unavailable → template response
6. **Caching:** Frequently requested responses cached locally for instant delivery

### Performance Optimization Strategies

*   **Async Processing:** All LLM calls are asynchronous to avoid blocking UI thread (NFR1/NFR2)
*   **Aggressive Caching:** Common responses (greetings, standard acknowledgments) pre-generated and cached
*   **Strategic LLM Usage:** 
    *   Simple interactions (greetings): 10% LLM, 90% templates
    *   Complex scenarios (scheduling): 90% LLM, 10% fallback
*   **Latency Budgets:**
    *   Simple communication: \<100ms (templates only)
    *   Nuanced responses: \<500ms (LLM acceptable)
    *   Scheduling analysis: \<1000ms (user expects AI "thinking")
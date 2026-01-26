# Story 1.4: Implement Empathetic AI Co-Pilot Communication

Status: completed

<!-- Note: This story is automatically generated with comprehensive context analysis to prevent LLM developer mistakes and ensure flawless implementation. -->

## Story

As a user,
I want the AI Co-Pilot to communicate with me in a calm, supportive, and non-intrusive tone,
So that I feel understood and encouraged, enhancing my well-being and productivity.

## Acceptance Criteria

1. **Given** the AI Co-Pilot provides any form of textual communication (e.g., suggestions, feedback, prompts),
   **When** the user reads the communication,
   **Then** the tone and language used are consistently calm, supportive, and non-intrusive.

2. **Given** the AI Co-Pilot communicates,
   **Then** the communication is delivered in a manner that respects user context and does not interrupt critical tasks or flow states.

3. **Given** the AI Co-Pilot generates communication,
   **Then** the system ensures the communication avoids jargon, overly technical language, or anything that might cause user anxiety or confusion.

## Tasks / Subtasks

- [ ] **Task 1: Design the AI Co-Pilot Communication Engine** (AC: #1, #2, #3)
  - [ ] Subtask 1.1: Create new feature module `app/modules/ai_copilot/` following feature-based organization
  - [ ] Subtask 1.2: Define empathetic communication persona model with tone guidelines
  - [ ] Subtask 1.3: Create message template system for consistent calm, supportive communication
  - [ ] Subtask 1.4: Design context-awareness mechanism to avoid interrupting flow states
  - [ ] Subtask 1.5: Create language filter to eliminate jargon and anxiety-inducing phrases
  - [ ] Subtask 1.6: Document the "Jarvis" persona characteristics and communication principles

- [ ] **Task 2: Implement Core Communication Service** (AC: #1, #3)
  - [ ] Subtask 2.1: Create `services.py` with `CopilotCommunicationService` class
  - [ ] Subtask 2.2: Implement message generation methods with tone enforcement (initially template-based)
  - [ ] Subtask 2.3: Add message templates for common scenarios (greetings, encouragement, suggestions, check-ins)
  - [ ] Subtask 2.4: Implement prompt engineering wrapper to ensure LLM follows empathetic persona (design only, mock LLM for MVP)
  - [ ] Subtask 2.5: Add message validation to ensure tone compliance before delivery
  - [ ] Subtask 2.6: Create configurable message delivery preferences (frequency, intrusiveness level)
  - [ ] Subtask 2.7: **Design for future LLM integration points within `CopilotCommunicationService` (e.g., interface for LLM provider, API key management)**

- [ ] **Task 3: Create Communication UI Components** (AC: #2)
  - [ ] Subtask 3.1: Design non-intrusive notification widget using PySide6
  - [ ] Subtask 3.2: Implement co-pilot message display panel (atom/molecule level per Atomic Design)
  - [ ] Subtask 3.3: Add subtle animations for message appearance (fade-in, slide-in)
  - [ ] Subtask 3.4: Create dismiss/acknowledge interaction patterns
  - [ ] Subtask 3.5: Apply QSS styling consistent with minimalist RPG aesthetic
  - [ ] Subtask 3.6: Ensure keyboard accessibility for all co-pilot interactions (NFR7)

- [ ] **Task 4: Implement Context-Aware Delivery System** (AC: #2)
  - [ ] Subtask 4.1: Create `models.py` with `UserContext` and `CommunicationEvent` SQLAlchemy models
  - [ ] Subtask 4.2: Implement user state detection (idle, active, flow state) mechanism
  - [ ] Subtask 4.3: Create intelligent timing algorithm for message delivery
  - [ ] Subtask 4.4: Add "Do Not Disturb" mode integration with user preferences
  - [ ] Subtask 4.5: Implement message queue system for deferred delivery
  - [ ] Subtask 4.6: Store communication history in SQLite for learning and refinement

- [ ] **Task 5: Integrate with Mood Check-in System** (AC: #1)
  - [ ] Subtask 5.1: Connect to `mood_checkin` module from Story 1.3
  - [ ] Subtask 5.2: React to `moodCheckInCompleted` signal to provide empathetic response
  - [ ] Subtask 5.3: Customize communication tone based on user's logged mood/energy
  - [ ] Subtask 5.4: Provide appropriate encouragement or support messages
  - [ ] Subtask 5.5: Use PySide6 Signals & Slots with `verbNoun` naming (e.g., `copilotMessageGenerated`)

- [ ] **Task 6: Implement MVVM Architecture for Co-Pilot** (AC: #1, #2, #3)
  - [ ] Subtask 6.1: Create `view_models.py` with `CopilotViewModel` class
  - [ ] Subtask 6.2: Manage UI state for co-pilot messages and notifications
  - [ ] Subtask 6.3: Use Qt Property system for reactive UI updates
  - [ ] Subtask 6.4: Connect ViewModel to `CopilotCommunicationService`
  - [ ] Subtask 6.5: Implement signal emissions for message events (`messageReady`, `messageDisplayed`, `messageDismissed`)

- [ ] **Task 7: Create Testing Suite** (AC: #1, #2, #3)
  - [ ] Subtask 7.1: Create `tests/` directory within `app/modules/ai_copilot/`
  - [ ] Subtask 7.2: Write unit tests for `CopilotCommunicationService` message generation
  - [ ] Subtask 7.3: Write tone validation tests to ensure calm, supportive language
  - [ ] Subtask 7.4: Test context-awareness and non-intrusive delivery timing
  - [ ] Subtask 7.5: Write UI tests with pytest-qt for message display components
  - [ ] Subtask 7.6: Add integration tests with mood check-in module
  - [ ] Subtask 7.7: Verify performance (\u003c100ms for message display, NFR1)

- [ ] **Task 8: Create Sample Message Library and Persona Documentation** (AC: #1, #3)
  - [ ] Subtask 8.1: Document "Jarvis" persona characteristics in code comments or docs
  - [ ] Subtask 8.2: Create library of pre-approved empathetic message templates
  - [ ] Subtask 8.3: Define forbidden phrases and jargon blacklist
  - [ ] Subtask 8.4: Create guidelines for future message additions
  - [ ] Subtask 8.5: Add examples of good vs. bad communication styles

## Dev Notes

This story establishes the **foundational AI persona** for the entire Sageframe application. The empathetic "Jarvis" co-pilot is a core differentiator and must communicate with unwavering calm, support, and user-centricity. This is NOT just a notification system—it's the personality of the application.

### 🎯 CRITICAL SUCCESS FACTORS

1. **Tone is Everything:** The co-pilot's communication must ALWAYS be calm, supportive, and non-intrusive. This is non-negotiable.
2. **Context Awareness:** Never interrupt flow states. Respect the user's focus and timing.
3. **Simplicity:** Avoid technical jargon. Communicate like a supportive friend, not a technical manual.
4. **Consistency:** Every message should feel like it comes from the same empathetic persona.

### Relevant Architecture Patterns and Constraints

- **Frontend Architecture:** Strictly follow **MVVM (Model-View-ViewModel)** pattern
  - **Model:** `UserContext`, `CommunicationEvent` (SQLAlchemy models for context and history)
  - **ViewModel:** `CopilotViewModel` (manages message state, timing, delivery coordination)
  - **View:** Co-pilot message display widgets/panels (PySide6)

- **Component Architecture:** Apply **Atomic Design** principles
  - **Atoms:** Message text label, dismiss button, notification icon
  - **Molecules:** Single message card/notification
  - **Organisms:** Co-pilot panel with message queue/history

- **LLM Integration:**
  - **Primary LLM Provider:** **Google Gemini 2.5 Flash**
  - **Architecture Pattern:** **Hybrid Template + LLM** (Templates for instant feedback and offline, LLM for intelligent reasoning)
  - **Integration Pattern:** **User-Provided API Key** (for privacy and control)

- **Data Architecture:** 
  - Use **SQLite** (via SQLAlchemy ORM) for storing communication events and user context
  - Apply **Pydantic** for message schema validation before display
  - Database naming: **`snake_case`** (e.g., `communication_events`, `message_text`, `delivered_at`)

- **Event Communication:** 
  - Use PySide6 **Signals & Slots** with **`verbNoun`** naming convention
  - Example signals: `messageGenerated`, `messageDelivered`, `messageDismissed`, `contextChanged`
  - For complex message payloads, use **Pydantic models**

- **Styling:** 
  - All UI styling via **Qt Style Sheets (QSS)**
  - Reuse `resources/styles/main.qss` (from Story 1.2) for consistency
  - Create `app/modules/ai_copilot/copilot.qss` for specific co-pilot widget styling
  - Subtle animations for non-intrusive appearance (fade-in, gentle slide)

- **Code Standards:** 
  - Strict adherence to **PEP 8** for all Python code
  - Clear docstrings for all classes and methods explaining the empathetic communication approach

- **Performance (NFR1, NFR2):** 
  - Message generation and display must be responsive (\u003c100ms visual feedback)
  - UI transitions must be fluid (\u003c200ms for full message panel display)
  - Do NOT block the main thread with LLM calls—use async or background processing

- **Accessibility (NFR7):** 
  - Ensure keyboard navigability for all co-pilot interactions
  - Clear focus indicators, readable fonts/contrast
  - Screen reader support for message content

### Source Tree Components to Touch

**New Files:**
- `app/modules/ai_copilot/__init__.py`
- `app/modules/ai_copilot/models.py` (SQLAlchemy: UserContext, CommunicationEvent + Pydantic schemas)
- `app/modules/ai_copilot/services.py` (CopilotCommunicationService)
- `app/modules/ai_copilot/view_models.py` (CopilotViewModel)
- `app/modules/ai_copilot/views.py` (CopilotMessageWidget, CopilotPanel)
- `app/modules/ai_copilot/persona.py` (Persona definitions, message templates, tone guidelines)
- `app/modules/ai_copilot/tests/__init__.py`
- `app/modules/ai_copilot/tests/test_communication_service.py`
- `app/modules/ai_copilot/tests/test_copilot_viewmodel.py`
- `app/modules/ai_copilot/tests/test_tone_validation.py`
- `app/modules/ai_copilot/tests/test_context_awareness.py`
- `app/modules/ai_copilot/copilot.qss` (Co-pilot widget-specific styles)
- `migrations/versions/XXXX_add_communication_events_table.py` (Alembic migration)
- `docs/copilot_persona_guide.md` (Documentation for the Jarvis persona and communication principles)

**Modified Files:**
- `app/main_window.py` (Add co-pilot panel/widget to main window layout)
- `resources/styles/main.qss` (If extending global styles for co-pilot)
- `app/modules/mood_checkin/view_models.py` (Connect `moodCheckInCompleted` signal to co-pilot)

### Testing Standards Summary

- **Unit Tests:** 
  - Test `CopilotCommunicationService` message generation with various inputs
  - Verify tone validation (ensure calm, supportive, non-jargon language)
  - Test context-aware timing algorithms (flow state detection, delivery deferral)
  - Mock database interactions for isolated testing

- **Integration Tests:** 
  - Test signal connections between mood check-in and co-pilot modules
  - Verify end-to-end message flow: generation → validation → delivery → display
  - Test with real SQLite database for communication event storage

- **UI Tests:** 
  - Use `pytest-qt` to verify co-pilot widgets appear correctly
  - Test message display, dismiss, and acknowledge interactions
  - Verify keyboard navigation and accessibility

- **Tone Validation Tests:** 
  - Create test cases with "good" and "bad" example messages
  - Verify the tone filter catches anxiety-inducing or jargon-heavy language
  - Ensure consistency across different message types

- **Performance Tests:** 
  - Verify \u003c100ms for message generation and initial display (NFR1)
  - Verify \u003c200ms for full co-pilot panel rendering (NFR2)

### Project Structure Notes

- **Feature-Based Organization:** All AI co-pilot related files grouped under `app/modules/ai_copilot/`
- **Consistency with Story 1.3:** 
  - Reuse the MVVM pattern from mood check-in
  - Follow the same SQLAlchemy + Pydantic hybrid validation approach
  - Use Alembic for database migrations
  - Reuse established signal naming patterns (`verbNoun`)

- **Modular Design:** 
  - The co-pilot communication engine should be designed for future expansion
  - Easy to add new message types, communication channels, and persona variations
  - Support for future LLM integration (initially use templates, prepare for GPT/Gemini)

- **Database Migration:** 
  - Use **Alembic** to create migration for `communication_events` and `user_context` tables
  - Ensure safe schema evolution with proper rollback support

### Previous Story Intelligence (Story 1.3)

From Story 1.3 implementation, we learned:

**✅ What Worked Well:**
- **MVVM Pattern:** The separation of Model (SQLAlchemy), ViewModel (Qt properties), and View (PySide6) was clean and testable
- **Feature-Based Organization:** Grouping all related files in `app/modules/mood_checkin/` made development straightforward
- **SQLAlchemy + Pydantic Hybrid:** Combining ORM with validation schemas provided robust data handling
- **Signal Naming (`verbNoun`):** Consistent signal naming (`moodCheckInCompleted`) made signal/slot connections clear
- **Accessibility Features:** Adding `setAccessibleName/Description` to UI elements improved keyboard navigation
- **Comprehensive Testing:** 24 total tests (15 unit + 9 integration) caught multiple issues early

**⚠️ Issues Encountered:**
- **Database Security:** Data stored in plaintext in `~/.sageframe/sageframe.db` (CRITICAL issue, needs encryption)
- **Performance Testing Gap:** NFR1/NFR2 performance tests were NOT implemented (need timing assertions)
- **Font Loading:** RPG-style fonts failed to load in Story 1.2, ensure fallback fonts are robust
- **UI Test Hanging:** One UI test (dialog submit interaction) hangs but was non-critical

**🔧 Applied Fixes from Code Review:**
- Used `Literal` type validation for enums (mood/energy levels)
- Added error handling for database session initialization
- Added `SAGEFRAME_DB_PATH` environment variable for configurable database path
- Fixed deprecated `datetime.utcnow()` → `datetime.now(timezone.utc)`
- Fixed signal naming inconsistency (`checkInCompleted` → `moodCheckInCompleted`)

**📋 Key Takeaways for This Story:**

1. **Reuse Established Patterns:** 
   - Follow the exact MVVM structure from Story 1.3
   - Reuse SQLAlchemy + Pydantic validation approach
   - Use the same testing framework setup (pytest + pytest-qt)

2. **Address Known Issues:**
   - **CRITICAL:** Plan for database encryption or verify OS-level encryption is enabled
   - **IMPORTANT:** Add performance timing tests for NFR1/NFR2 compliance
   - Ensure robust font fallbacks for co-pilot UI

3. **Signal Integration:**
   - Connect to `moodCheckInCompleted` signal from Story 1.3
   - Use `verbNoun` naming for all new signals
   - Use Pydantic models for complex signal payloads

4. **Database Setup:**
   - Reuse `app/database.py` setup from Story 1.3
   - Add Alembic migration for new tables
   - Respect `SAGEFRAME_DB_PATH` environment variable

5. **Testing Coverage:**
   - Aim for 20+ tests (unit + integration + UI)
   - Include error scenario tests (DB failures, invalid inputs)
   - Add performance timing assertions

6. **Code Review Preparation:**
   - Use `Literal` types for enum validation
   - Add comprehensive error handling with try/except blocks
   - Add accessibility attributes to all UI elements
   - Fix any deprecated API usage
   - Ensure signal names are consistent

### 🚨 CRITICAL WARNINGS TO PREVENT LLM DEVELOPER MISTAKES

1. **PRIORITIZE TEMPLATE-BASED MESSAGES FOR MVP, ARCHITECT FOR LLM INTEGRATION:**
   - For the MVP, focus on robust **template-based messages** with tone enforcement and contextual logic.
   - **DO NOT** directly integrate with Google Gemini (or any LLM) APIs for initial MVP.
   - Design the architecture (e.g., `CopilotCommunicationService`) to easily swap in the **Google Gemini 2.5 Flash LLM** (as per Architecture) later without re-architecting.
   - Mock LLM responses for testing the eventual integration.

2. **DO NOT block the UI thread:**
   - If using any async operations, use Qt's threading (QThread) or Python's asyncio
   - Message generation must remain \u003c100ms (NFR1)

3. **DO NOT store API keys in code or config files:**
   - If LLM integration is added, use environment variables or secure key storage
   - Follow security best practices (NFR3, NFR4)

4. **DO NOT ignore the tone guidelines:**
   - Every message MUST pass tone validation before display
   - Create a blacklist of forbidden phrases (e.g., "Error", "Failed", "Warning" → reframe as "Let's try again", "I'll help with that")

5. **DO NOT interrupt flow states:**
   - Implement proper context detection before message delivery
   - Respect user focus and timing—the co-pilot is supportive, not annoying

6. **DO NOT forget database migrations:**
   - Use Alembic for all schema changes
   - Test migrations in both directions (upgrade and downgrade)

7. **DO NOT skip accessibility:**
   - All co-pilot interactions must be keyboard accessible
   - Add proper ARIA attributes and accessible names

8. **DO NOT reinvent established patterns:**
   - Reuse the MVVM structure from Story 1.3
   - Follow the exact signal/slot patterns already established
   - Reuse QSS styling from `main.qss`

### 🎨 Design Guidance for Co-Pilot UI

**Visual Aesthetic:**
- Minimalist design consistent with Sageframe's RPG-style theme
- Subtle, non-intrusive notifications (bottom-right corner or dedicated side panel)
- Use calming colors (soft blues, gentle greens, warm neutrals)
- Gentle animations (fade-in, slide-in) for message appearance
- Clear typography with excellent readability

**Interaction Patterns:**
- Messages should be dismissible with a single click or keyboard shortcut
- Optional "acknowledge" action for important messages
- Auto-dismiss for low-priority notifications after 5-10 seconds
- Persistent display for high-priority messages requiring user action

**Persona Visual Identity:**
- Consider a subtle icon or avatar for "Jarvis" (optional for MVP)
- Consistent visual treatment for all co-pilot messages
- Clear distinction from system notifications or error messages

### 🧠 Communication Persona Guidelines ("Jarvis" Characteristics)

**Core Principles:**
1. **Calm:** Never use alarming or urgent language. Reframe issues as opportunities.
2. **Supportive:** Encourage, don't criticize. Celebrate small wins.
3. **Non-Intrusive:** Suggest, don't demand. Respect user autonomy.
4. **Empathetic:** Acknowledge user state (mood, energy). Adapt communication accordingly.
5. **Simple:** Use plain language. Avoid technical jargon.
6. **Consistent:** Maintain the same tone across all interactions.

**Example Message Transformations:**

❌ **BAD (Alarming, Technical):**
- "Error: Task creation failed. Database exception occurred."
- "Warning: You have 15 overdue tasks. [!]"
- "System alert: Low energy detected. Productivity may be impacted."

✅ **GOOD (Calm, Supportive, Empathetic):**
- "I noticed something didn't go quite right. Let's try creating that task again together."
- "You've been working hard! Would you like help prioritizing your tasks?"
- "I see you're feeling low energy today. How about starting with something light?"

**Message Categories and Templates:**

1. **Greetings:**
   - "Good morning! Ready to tackle today together?"
   - "Welcome back! What would you like to focus on?"

2. **Mood-Based Responses:**
   - **High Energy:** "Great energy! Let's channel that into your top priorities."
   - **Low Energy:** "I understand. How about we start with something simple?"
   - **Stressed:** "I'm here to help lighten the load. Let's take it one step at a time."

3. **Task Suggestions:**
   - "Based on your schedule, you have a free hour. Would you like to work on [Task Name]?"
   - "I noticed you completed [Task]. Nice work! Ready for the next one?"

4. **Encouragement:**
   - "You're making great progress!"
   - "Every step forward counts. Keep going!"
   - "I noticed you've been focused for a while. How about a short break?"

5. **Gentle Reminders:**
   - "Just a friendly reminder: [Event] is coming up soon."
   - "Would you like to plan some time for [Task] this week?"

### 📚 References

- [Source: `epics.md`#Story 1.4: Implement Empathetic AI Co-Pilot Communication]
- [Source: `prd.md`#Functional Requirements: FR1, FR4]
- [Source: `prd.md`#Success Criteria: User Success - Trust in the Co-Pilot]
- [Source: `prd.md`#User Journeys: Alex's Journey - LLM-powered Jarvis]
- [Source: `prd.md`#Product Scope: MVP - The Jarvis Co-Pilot (Enhanced Communication)]
- [Source: `prd.md`#SaaS Platform / Web App Specific Requirements: Technical Architecture Considerations - LLM Integration]
- [Source: `prd.md`#MVP Feature Set (Phase 1): Must-Have Capabilities - The Jarvis Co-Pilot (Enhanced Communication)]
- [Source: `prd.md`#LLM Integration Requirements: Provider, User Requirements, Cost Transparency, Privacy Guarantees]
- [Source: `prd.md`#Non-Functional Requirements: NFR1 (Responsiveness), NFR2 (Fluidity), NFR7 (Accessibility)]
- [Source: `prd.md`#Industry Best Practices & Patterns: Ethical AI & Transparency]
- [Source: `architecture.md`#Cross-Cutting Concerns Identified: AI/ML]
- [Source: `architecture.md`#Frontend Architecture: MVVM Pattern, Atomic Design]
- [Source: `architecture.md`#Data Architecture: SQLite, SQLAlchemy, Pydantic, Alembic]
- [Source: `architecture.md`#API & Communication Patterns: Event System Patterns (PySide6 Signals & Slots)]
- [Source: `architecture.md`#AI/ML Integration Architecture: LLM Service Integration, Agent Prompt System, API Key Security, LLM Response Processing, Performance Optimization Strategies]
- [Source: `architecture.md`#Implementation Patterns & Consistency Rules: Naming, Structure, Format, Communication, Process Patterns]
- [Source: Previous Story 1.3 - `1-3-implement-mood-check-in.md`]
- [Source: User Journey - Alex's Journey: Calm "Jarvis-like" co-pilot guidance]
- [Source: PRD Persona: "Jarvis" AI as essential and supportive partner]

### 🔗 Integration Points with Other Stories

**Dependencies:**
- **Story 1.3 (Mood Check-in):** React to `moodCheckInCompleted` signal to provide empathetic responses
- **Story 1.2 (Theming):** Reuse QSS styling system and main window layout

**Future Integration:**
- **Story 1.5 (Proactive Suggestions):** Co-pilot will deliver mood-aware task suggestions
- **Story 1.6 (Keyboard Shortcuts):** Co-pilot messages should be accessible via keyboard
- **Epic 2 (Task Management):** Co-pilot will provide encouragement and guidance on task completion
- **Epic 4 (Calendar):** Co-pilot will suggest scheduling based on calendar availability

### 🎯 Definition of Done

This story is considered complete when:

1. ✅ Co-pilot communication module is fully implemented with MVVM architecture
2. ✅ All messages consistently use calm, supportive, non-intrusive tone
3. ✅ Context-aware delivery system respects user flow states and timing
4. ✅ Integration with mood check-in module is functional (responds to mood signals)
5. ✅ UI components are styled, accessible, and keyboard-navigable
6. ✅ Database models and migrations are created and tested
7. ✅ Comprehensive test suite (\u003e20 tests) with tone validation and performance testing
8. ✅ Documentation of "Jarvis" persona characteristics is complete
9. ✅ All acceptance criteria are verifiably met
10. ✅ Code review completed and all CRITICAL/HIGH issues resolved

## Dev Agent Record

### Agent Model Used

_To be filled by implementing developer agent_

### Debug Log References

_To be filled during implementation_

### Completion Notes List

_To be filled during implementation_

### File List

_To be filled during implementation_

---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - _bmad-output/implementation-artifacts/Project_Sageframe_Product_Brief_2026-01-22_v1.0.md
  - _bmad-output/planning-artifacts/prd-validation-report.md
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/implementation-readiness-report-2026-01-24.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/analysis/brainstorming-session-2026-01-19.md
---

# UX Design Specification PROJECT_SAGEFRAME

**Author:** Timothy
**Date:** 2026-01-25

---

<!-- UX design content will be appended sequentially through collaborative workflow steps -->
## UX Pattern Analysis & Inspiration

### Inspiring Products Analysis
Our analysis of inspiring products focused on how they achieve a "minimal feel but amount of features accessible," a core tenet for Sageframe.
-   **Todoist:** Celebrated for its **Frictionless Capture** (e.g., Quick Add with natural language processing) and its **Clean Simplicity** that promotes a calm user experience.
-   **Finch:** Offers insights into **Empathetic Design**, using joyful micro-interactions and gentle gamification to encourage self-care and make users feel supported.
-   **Obsidian:** Exemplifies the "low floor, high ceiling" concept, with powerful **Keyboard-First Navigation** and a **Command Palette** that empowers users and fosters a deep "Sense of Flow."
-   **Habitica:** Provides a direct model for **Direct Gamification**, transforming tasks into RPG-style quests and leveraging XP for motivation and a sense of accomplishment.
-   **General takeaway:** Minimal feel but with accessible features.

### Transferable UX Patterns
Based on the analysis, the following patterns are highly transferable and will be integrated into Sageframe:
-   **Navigation Patterns:**
    -   **Unified Dashboard with Smart Drill-Down:** A central "command center" offering a bird's eye view with intuitive access to detailed information.
    -   **Universal Command Palette:** A keyboard-accessible interface for rapid command execution and navigation.
-   **Interaction Patterns:**
    -   **Natural Language Input:** For effortless and intelligent parsing of task and note details during quick capture.
    -   **Empathetic Gamification & Positive Reinforcement:** Subtle, encouraging feedback and progress visualization to enhance motivation and accomplishment.
-   **Visual Patterns:**
    -   **Adaptive Minimalism:** A clean, focused UI that introduces complexity only as needed, aligning with our aesthetic choices.
    -   **Thematic Consistency:** A cohesive visual language that integrates the chosen "blue/black/RPG" style across all elements.

### Anti-Patterns to Avoid
To ensure Sageframe avoids common pitfalls and frustrations, we will actively avoid:
-   **Burying Features in Menus:** All core functionalities must be easily discoverable and accessible.
-   **Noisy, Intrusive Gamification:** Gamified elements should be subtle, supportive, and non-distracting, aligning with our "Calm" emotional goal.
-   **Rigid, Prescriptive Workflows:** The system should offer flexibility, adapting to the user's preferred CODE workflow.
-   **Unhelpful "Magic":** AI assistance must be consistently accurate, transparent, and user-controlled to build trust.
-   **Information Overload on the Dashboard:** The dashboard must maintain clarity and calm, providing a curated overview rather than overwhelming the user.

### Design Inspiration Strategy
Our strategy for leveraging this inspiration is threefold:
-   **Adopt:** Directly implement Natural Language Input, the Universal Command Palette, and Adaptive Minimalism as foundational elements.
-   **Adapt:** Customize Empathetic Gamification & Positive Reinforcement (integrating the blue/black/RPG theme) and the Unified Dashboard with Smart Drill-Down to fit Sageframe's unique vision and the CODE workflow.
-   **Avoid:** Diligently sidestep the identified anti-patterns to ensure a frustration-free and supportive user experience.

## Executive Summary

### Project Vision
Project Sageframe is an empathetic co-pilot designed to revolutionize personal productivity. It shifts the focus from simple task management to holistic well-being, actively helping users manage their energy and focus to prevent burnout. It's a productivity partner that adapts to the user's state of mind.

### Target Users
Our target users are tech-savvy (rating themselves 4 out of 5) students and young professionals. They primarily use a Windows desktop environment and require a tool that can be used throughout the day to plan and execute tasks, schedules, and meetings. Their core need is a "bird's eye view" dashboard showing all pending and upcoming items, with the immediate ability to drill down into specifics as required.

### Key Design Challenges
- **Information vs. Calm:** The central challenge is to design a dashboard that provides a comprehensive "bird's eye view" of a user's day without inducing cognitive overload. The UI must be clean and scannable while allowing for intuitive deep-dives into task details.
- **Helpful AI vs. User Control:** The proactive "Jarvis" AI must offer timely and valuable suggestions without undermining the user's sense of autonomy. The design must make it effortless for users to accept, reject, or modify AI recommendations.
- **Habit Formation:** The success of mood-aware features depends on user adoption. The onboarding and daily interaction loop must be frictionless and immediately demonstrate the value of checking in with one's energy levels.

### Design Opportunities
- **The "Zoomable" Dashboard:** We have a significant opportunity to create an innovative dashboard that visualizes the user's day in terms of energy and focus. This could become a signature feature, allowing users to fluidly "zoom" between a high-level overview and detailed task analysis.
- **A Powerful Desktop Experience:** By focusing on a keyboard-first, command-palette-driven interface for the Windows app, we can create a true power tool that resonates deeply with our tech-savvy audience.
- **Tangible Well-being:** We can make the abstract concept of well-being visible and actionable through the UI, offering visual feedback on the user's progress in maintaining a healthy balance between work and rest.
## Core User Experience

### Defining Experience
The core of Sageframe's experience is built around the daily interaction with a dynamic dashboard and the seamless quick capture of information. This revolves fundamentally around the **CODE (Capture, Organise, Review, Edit)** workflow. Users will primarily engage by checking their dashboard to gain a comprehensive overview of their day, tasks, and schedule, and then quickly capturing new thoughts, tasks, or notes. The AI co-pilot's critical role will be to intelligently assist in the 'Organise' phase and gently facilitate the 'Review' and 'Edit' sessions, ensuring a guided yet autonomous workflow.

### Platform Strategy
Sageframe will be delivered across multiple platforms, with **Windows Desktop** as the primary focus, leveraging mouse and keyboard interactions for a robust, power-user experience. **Android Mobile** will serve as the secondary platform, utilizing touch interactions and specific device capabilities like the camera for "Short Notes Ingestion" and haptic feedback where applicable. A crucial requirement is **offline functionality**, ensuring users can access and manage their information irrespective of internet connectivity. We will explore opportunities for platform-specific optimizations, such as extensive keyboard shortcuts for Windows desktop.

### Effortless Interactions
Key to Sageframe's success will be interactions that feel completely effortless:
-   **Quick Capture:** Implementing a global keyboard shortcut that triggers an immediate pop-up window for capturing notes or tasks.
-   **Seamless Dashboard Interactions:** Ensuring that navigation, filtering, and interaction with tasks, schedules, and various information elements on the dashboard are fluid and intuitive.
-   **Smart Information Allotment:** Automatic, intelligent classification and routing of captured information (e.g., distinguishing between quick tasks, long tasks, notes, meetings, and social engagements), reducing manual effort for the user.
-   **Automatic Syncing:** Background synchronization of data to ensure consistency across devices, with user-controlled cloud options.

### Critical Success Moments
Defining moments that will forge user loyalty and indicate the product's success include:
-   The profound relief and sense of accomplishment a user experiences when they **clear their task list**, feeling in complete control of their day.
-   The successful and intuitive execution of the **CODE workflow**, particularly the intelligent assistance provided by the AI in the 'Organise' phase and the gentle, effective guidance during 'Review' and 'Edit' sessions.
-   The first "aha!" moment where a new user realizes Sageframe provides a superior, more empathetic way to manage their productivity and well-being.

### Experience Principles
1.  **Dashboard as Command Center:** The dashboard is the user's single source of truth, providing an immediate, scannable overview of their day, with seamless navigation to deep-dive into details.
2.  **Frictionless Capture:** Getting information *into* Sageframe must be instant and effortless, epitomized by a global keyboard shortcut for a "quick capture" popup.
3.  **The "CODE" Workflow is Everything:** The entire user experience is built around the "Capture, Organise, Review, Edit" methodology, with the system intelligently automating 'Organise' and facilitating 'Review' and 'Edit'.
4.  **The Relief of "Done":** The ultimate feeling of success comes from clearing the task list, a moment the UI will reinforce, celebrating accomplishment and fostering calm control.
5.  **Always Available, Always Reliable:** The experience must be dependable, with offline functionality ensuring constant access and management of information, regardless of connectivity.
## Desired Emotional Response

### Primary Emotional Goals
The paramount emotional goals for Sageframe are to make users feel **Calm, Supported, and Productive**. These feelings are foundational to combating burnout and fostering a healthier approach to productivity.

### Emotional Journey Mapping
(Detailed emotional journey mapping was skipped to focus on core definitions; this will be addressed in future, more detailed design phases if required.)

### Micro-Emotions
To support the primary emotional goals, Sageframe will also cultivate specific micro-emotions: **Confidence, Trust, Excitement, Accomplishment, Satisfaction, Belonging,** and a profound **Sense of Flow**. Conversely, we will actively design to avoid feelings of frustration, confusion, anxiety, and being overwhelmed or criticized.

### Design Implications
The desired emotional responses will be woven into the fabric of Sageframe's UX through:
-   **Visual & Thematic Elements:** A calming "blue and black" color scheme paired with "RPG-style fonting" will evoke a sense of focused quest and clarity.
-   **Building Trust & Confidence (in AI):** AI suggestions will be accompanied by transparent, concise explanations of their rationale, and all AI-driven actions will be easily reversible with clear undo options. The AI's communication will consistently maintain a calm, supportive, and non-judgmental tone.
-   **Evoking Excitement & Accomplishment:** Subtle, satisfying visual and audio cues will celebrate task completion and significant milestones. Progress will be visually reinforced through elements like progress bars, "XP" systems, or streak counters on the dashboard, utilizing the RPG theme for positive reinforcement.
-   **Fostering Belonging & Satisfaction:** Deep personalization options (e.g., customizable themes beyond blue/black, AI co-pilot naming) will empower users to make Sageframe truly their own. Future considerations include optional, anonymized community insights for shared learning.
-   **Enhancing Flow:** A powerful, keyboard-first "Command Palette" (e.g., Ctrl+K) will allow rapid, context-aware actions. Dedicated "Focus Modes" will temporarily declutter the UI, ensuring uninterrupted concentration on tasks, and the frictionless quick capture (global keyboard shortcut with pop-up) will prevent context switching.

### Emotional Design Principles
The emotional design principles for Sageframe are:
1.  **Empathetic Guidance:** The system should always feel like a supportive co-pilot, not a taskmaster.
2.  **Celebration of Progress:** Acknowledge and reinforce user accomplishments, big and small.
3.  **Clarity & Control:** Provide clear information and ensure users always feel in command of their experience.
4.  **Seamless Immersion:** Design for uninterrupted focus and effortless interaction to foster a state of flow.

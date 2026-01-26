# Project Scoping & Phased Development

## MVP Strategy & Philosophy

**MVP Approach:** Our strategy is a **Platform MVP**. This means we prioritize building a robust, scalable technical foundation and the core "empathetic co-pilot" experience. The goal is to deliver a highly stable and valuable initial offering that solves fundamental productivity and well-being challenges, while laying the groundwork for significant future expansion. This approach will attract early adopters who value a unique, high-quality experience and demonstrate Sageframe's core potential.

**Resource Requirements:** (To be defined in a later planning phase, but will focus on a lean, skilled team capable of delivering high-quality core functionality and a stable platform.)

## MVP Feature Set (Phase 1)

This phase focuses on core features essential for the "empathetic co-pilot" experience and foundational productivity.

**Core User Journeys Supported:**
*   **Alex's Journey:** Primary support for managing academic and social life, leveraging mood-aware task triage and calendar integration.
*   **Ben's Journey (Core):** Basic task and project management, calendar integration for life admin, and social scheduling. Specialized job hunt features will be deferred.

**Must-Have Capabilities:**
*   **The Jarvis Co-Pilot (Enhanced Communication):** Empathetic AI persona powered by **Google Gemini 2.5 Flash LLM**, with hybrid template + intelligent reasoning architecture. Supports:
    *   Calm, supportive, non-intrusive communication tone (enforced via agent prompt system)
    *   User-provided Gemini API key for privacy and control
    *   Offline fallback to template-based responses
    *   Secure API key storage in system keychain
*   **Mood-Aware Task Triage:** Simple mood check-in with **LLM-powered intelligent task suggestions** aligned with energy state and mood context.
*   **Proactive Social Scheduling:** Analyze calendar gaps for social/professional engagements using **LLM reasoning** for optimal time blocking.
*   **Intelligent Curation via Smart Tags:** Frictionless information capture (`@tag: content`), auto-enrichment of content.
*   **Short Notes Ingestion:** OCR-based digitization of physical notes (Windows/Android).
*   **Core Task & Project Management:** Creation/management of tasks and projects, Kanban/Gantt chart views.
*   **Bi-directional Calendar Integration:** Sync with major calendar providers.
*   **Core Platform & Infrastructure:**
    *   **Local-First Data Storage** with **User-Controlled Cloud Sync**.
    *   **Python-only** technology stack.
    *   **Windows-first** development.
    *   **Minimalist UI** with RPG-style aesthetic.
    *   **User-accessible API** for IFTTT/Zapier integration.
    *   Adherence to **Ethical AI & Transparency** principles.
    *   **Data Portability & No Lock-in**.
    *   **Forgiving & Reversible Actions**.
    *   **Keyboard-First Navigation** (with shortcut menu).

## Post-MVP Features

**Phase 2 (Growth Features):** These features will build upon the stable MVP, expanding functionality and addressing more specialized use cases.
*   **Job Hunt Specific Features:** Application tracker, resume repository with content tailoring capabilities.
*   **Gamified Goal Decomposition:** Breaking large goals into scheduled tasks with non-visual rewards.
*   **The Hub-and-Spoke Knowledge Workflow:** Advanced integration with external knowledge bases (e.g., Obsidian).
*   **The Daily Debrief Dashboard:** Visual daily review of mood, tasks, and planning nudges.
*   **Pomodoro Support:** Integrated timers for focused work sessions.

**Phase 3 (Vision Features):** These represent the long-term vision, adding highly advanced and potentially transformative capabilities.
*   **The Quest Log Dashboard:** Redesigned productivity dashboard with a comprehensive gamified interface.
*   **The Personal Performance Consultant:** Data-driven insights and personalized coaching based on user activity trends.
*   **Advanced AI-driven insights and automation:** More predictive and proactive assistance.

## Risk Mitigation Strategy

**Technical Risks:** Mitigated by prioritizing Windows development first to establish a stable core, focusing on a single tech stack (Python), and deferring complex integrations. The platform MVP approach reduces initial technical surface area.
**Market Risks:** Mitigated by focusing the MVP on core user pain points (disorganization, stress) and validating the unique empathetic AI approach early. User feedback on the MVP will guide future feature development.
**Resource Risks:** Mitigated by defining a lean MVP and phased roadmap, allowing for more precise resource allocation and adjustments based on early success and funding.

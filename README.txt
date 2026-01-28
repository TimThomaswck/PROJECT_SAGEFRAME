================================================================================
                            PROJECT_SAGEFRAME
                       Your Empathetic AI Co-Pilot
================================================================================

PROJECT OVERVIEW
================================================================================

SageFrame is an intelligent personal productivity assistant designed to help
busy professionals and knowledge workers manage their tasks, projects, and
well-being with the support of an empathetic AI co-pilot. Built with Python
and PySide6, SageFrame combines mood-aware task management, intelligent
calendar integration, and effortless information capture to create a calm,
supportive productivity experience.

Current Status: MVP in Progress (Version 0.1.0)


PROBLEM STATEMENT & INTENDED USERS
================================================================================

THE PROBLEM:
Modern productivity tools often overwhelm users with complex interfaces and
fail to consider individual well-being and energy levels. Many professionals
struggle to balance their workload, maintain social connections, and stay on
top of their schedules while managing mental energy effectively.

INTENDED USERS:
- Busy professionals juggling multiple projects and responsibilities
- Knowledge workers seeking better work-life balance
- Early-career professionals navigating complex schedules
- Anyone looking for an empathetic, supportive productivity system

USER PERSONAS:
1. "Alex" - A professional managing chaos across work and personal life,
   seeking calm control through intelligent task prioritization
2. "Ben" - An early-career professional navigating the maze of competing
   priorities and building sustainable productivity habits


KEY FUNCTIONALITIES
================================================================================

CORE FEATURES (MVP):
1. Empathetic AI Co-Pilot
   - Calm, supportive, non-intrusive communication
   - Proactive context-aware suggestions

2. Mood-Aware Task Management
   - Mood/energy level check-ins
   - Task suggestions based on current mental state
   - Manual energy/effort estimation for tasks

3. Comprehensive Project & Task Management
   - Create, view, edit, and delete projects and tasks
   - Assign properties (priority, complexity, energy level)
   - Hierarchical tasks with subtasks
   - Multiple visualization options (Kanban, Gantt chart)
   - Gamified progress tracking (levels & XP)

4. Intelligent Calendar Integration
   - Bi-directional sync with Google Calendar
   - Automatic free/busy time identification
   - Proactive scheduling suggestions for social/professional engagements
   - Time blocking with calendar push

5. Effortless Information Capture
   - Quick-capture inbox for unstructured thoughts
   - Smart tags (@movie, @book, etc.) for automatic categorization
   - Automatic content enrichment from external sources
   - Bill/note import with OCR extraction (image/PDF)
   - One-click task creation from extracted information

6. Focus & Well-being Tools
   - Simple habit tracker with daily checkmarks
   - Pomodoro timer with focus mode
   - Reminders for overdue/untouched tasks

7. Core UX Features
   - Keyboard-first navigation with comprehensive shortcuts
   - Undo functionality for actions
   - Customizable themes (light/dark mode)
   - Local-first data storage for privacy
   - Tags and smart filters with AND/OR logic

PLATFORM:
- Windows Desktop (Primary)
- Android Mobile (Planned for future)


HOW TO RUN THE CODE
================================================================================

SYSTEM REQUIREMENTS:
- Operating System: Windows 10 or later
- Python: Version 3.12 or higher
- Internet connection (for calendar sync and external API features)

INSTALLATION STEPS:

1. EXTRACT THE SOURCE CODE
   Extract the zip file to your desired location, for example:
   C:\Users\YourName\Documents\PROJECT_SAGEFRAME

2. SET UP PYTHON ENVIRONMENT
   Open PowerShell or Command Prompt and navigate to the project directory:
   
   cd C:\path\to\PROJECT_SAGEFRAME\sageframe_desktop

3. CREATE A VIRTUAL ENVIRONMENT
   Create and activate a Python virtual environment:
   
   python -m venv .venv
   .venv\Scripts\activate

4. INSTALL DEPENDENCIES
   Install all required Python packages:
   
   pip install -e .
   
   Key dependencies include:
   - PySide6 (6.1.3+) - Qt for Python GUI framework
   - SQLAlchemy (2.0.0+) - ORM for database management
   - Alembic (1.13.0+) - Database migrations
   - Pydantic (2.0.0+) - Data validation
   - google-api-python-client (2.0.0+) - Google Calendar API
   - google-auth-oauthlib (1.0.0+) - OAuth 2.0 authentication
   - httpx (0.28.1+) - HTTP client
   - PyPDF2 (3.0.0+) - PDF processing
   - Pillow (10.0.0+) - Image processing
   - keyring (24.0.0+) - Secure credential storage
   - aiohttp (3.9.0+) - Async HTTP client
   
   For a complete list, see pyproject.toml in the sageframe_desktop directory.

5. SET UP GOOGLE VISION API (REQUIRED FOR OCR FEATURES)
   For bill/note import and OCR extraction features, you need to configure
   the Google Vision API key. Please refer to the setup guide:
   
   See: GOOGLE_VISION_API_SETUP.md
   
   This document contains detailed instructions for obtaining and configuring
   your Google Vision API credentials.

6. INITIALIZE DATABASE
   Set up the local SQLite database and run migrations:
   
   cd sageframe_desktop
   alembic upgrade head

7. RUN THE APPLICATION
   Launch SageFrame using the test launcher:
   
   .venv\Scripts\python.exe test_launch.py
   
   The application window should appear, and you can begin using SageFrame!


FIRST-TIME SETUP:
- On first launch, you'll be guided through initial setup
- Configure your preferred theme (light/dark mode)
- Optionally connect your Google Calendar for smart scheduling
- Explore keyboard shortcuts by pressing '?' in the application


PROJECT STRUCTURE
================================================================================

PROJECT_SAGEFRAME/
├── sageframe_desktop/          # Main application directory
│   ├── app/                    # Core application code
│   │   ├── core/               # Core business logic & utilities
│   │   ├── modules/            # Feature modules (mood, tasks, calendar)
│   │   ├── ui/                 # PySide6 UI components
│   │   ├── database.py         # Database configuration
│   │   └── __main__.py         # Application entry point
│   ├── alembic/                # Database migration scripts
│   ├── alembic.ini             # Alembic configuration
│   ├── pyproject.toml          # Project metadata & dependencies
│   ├── test_launch.py          # Test launcher script
│   └── README.md               # Technical documentation
├── _bmad-output/               # BMAD planning & implementation artifacts
│   ├── planning-artifacts/     # PRD, Architecture, Epics
│   └── implementation-artifacts/ # Story implementation details
├── docs/                       # Project knowledge base
├── .agent/                     # BMAD workflow configurations
└── README.txt                  # This file


AI TOOLS USED IN DEVELOPMENT
================================================================================

The development of SageFrame leveraged multiple AI-powered tools to enhance
productivity, code quality, and project planning:

1. GITHUB COPILOT
   Purpose: AI-powered code completion and generation
   Usage: Real-time coding assistance, boilerplate generation, and intelligent
          code suggestions throughout the development process

2. BMAD SYSTEM (Build, Manage, And Deploy)
   Purpose: AI-driven Agile methodology and project orchestration
   Technology: Powered by Gemini CLI
   Usage: 
   - Automated epic and story creation from requirements
   - Sprint planning and status tracking
   - Implementation workflow orchestration
   - Multi-agent collaboration for different development roles
   - Code review automation
   - Test architecture planning
   Key Agents Used:
   - Project Manager (pm) - Sprint planning & story management
   - Developer (dev) - Story implementation
   - Technical Writer (tech-writer) - Documentation
   - Architect (architect) - System design decisions
   - Scrum Master (sm) - Sprint retrospectives

3. CHATGPT
   Purpose: Code debugging, problem-solving, and brainstorming
   Usage: Critical code fixes, debugging complex issues, and independent
          brainstorming for architectural decisions and feature design

4. ANTIGRAVITY (Google Deepmind)
   Purpose: Advanced code review and BMAD agent backup
   Usage: Comprehensive code quality reviews, suggestion validation, and
          serving as a backup expert for BMAD agent workflows


TECHNOLOGY STACK
================================================================================

CORE TECHNOLOGIES:
- Language: Python 3.12+
- GUI Framework: PySide6 (Qt for Python)
- Architecture Pattern: MVVM (Model-View-ViewModel)
- UI Design Pattern: Atomic Design principles

DATA & PERSISTENCE:
- Database: SQLite (local-first storage)
- ORM: SQLAlchemy 2.0+
- Migrations: Alembic
- Data Validation: Pydantic

INTEGRATIONS:
- Calendar: Google Calendar API (OAuth 2.0)
- OCR: Google Vision API
- Cloud Sync: User-controlled cloud providers (planned)

DEVELOPMENT STANDARDS:
- Code Style: PEP 8 (Python)
- Naming Conventions: snake_case for database/JSON, verbNoun for signals
- API Design: RESTful with OpenAPI documentation (planned)
- Error Handling: Global error handling with loading states
- Testing: pytest, pytest-qt (UI testing)

SECURITY:
- Authentication: OAuth 2.0 for external services
- Credential Storage: OS keyring integration
- Data Encryption: OS-level for local data, HTTPS/TLS for transit
- Privacy: Local-first architecture, data isolation (NFR3)

DEVELOPMENT TOOLS:
- CLI Tool: pyside-cli for project scaffolding
- Build Tools: Nuitka (native compilation), PyInstaller (packaging)
- CI/CD: GitHub Actions (planned)
- Version Control: Git


OPTIONAL: GITHUB REPOSITORY
================================================================================

GitHub Repository: [PLACEHOLDER - TO BE UPDATED]
https://github.com/yourusername/PROJECT_SAGEFRAME

The repository includes:
- Complete source code and commit history
- Development documentation
- Issue tracking and feature requests
- Release notes and version history


ARCHITECTURE HIGHLIGHTS
================================================================================

LOCAL-FIRST DESIGN:
All user data is stored locally by default in SQLite, ensuring privacy and
offline functionality. Cloud sync is optional and user-controlled.

MODULAR ARCHITECTURE:
Features are organized as isolated modules (mood_checkin, calendar, tasks)
following clean architecture principles for easy extensibility.

KEYBOARD-FIRST UX:
Comprehensive keyboard shortcuts for power users, with visual reference menu
accessible via '?' key.

RESPONSIVE PERFORMANCE:
- Core actions: <100ms visual feedback (NFR1)
- UI transitions: <200ms for full content load (NFR2)
- Async operations for external API calls to prevent UI blocking


FUTURE ROADMAP
================================================================================

POST-MVP FEATURES:
- Gamified Goal Decomposition
- Hub-and-Spoke Knowledge Workflow
- Daily Debrief Dashboard
- Enhanced Pomodoro Support

VISION (LONG-TERM):
- Quest Log Dashboard
- Personal Performance Consultant with advanced AI insights
- Android mobile platform support
- Advanced automation and integrations


TROUBLESHOOTING
================================================================================

COMMON ISSUES:

1. Import Errors / Missing Dependencies
   Solution: Ensure virtual environment is activated and run:
             pip install -e .

2. Database Errors
   Solution: Run database migrations:
             cd sageframe_desktop
             alembic upgrade head

3. Google Calendar Sync Issues
   Solution: Check OAuth credentials and internet connection
             Refer to NFR8/NFR9 for automatic retry behavior

4. OCR/Vision API Errors
   Solution: Verify Google Vision API key is properly configured
             See: GOOGLE_VISION_API_SETUP.md

5. Application Won't Start
   Solution: Check Python version (must be 3.12+)
             Verify all dependencies are installed
             Check console output for specific error messages


CONTACT & SUPPORT
================================================================================

For questions, issues, or contributions, please refer to the GitHub repository
or contact the development team.

Project maintained with ❤️ using AI-assisted development methodologies.


LICENSE
================================================================================

[Add your license information here]


================================================================================
                    Thank you for using SageFrame!
           "Your calm, supportive companion for productive living"
================================================================================

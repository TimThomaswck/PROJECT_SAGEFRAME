import os
from datetime import datetime

from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QVBoxLayout, QWidget, QHBoxLayout, QDockWidget, QMenu, QToolBar, QPushButton, QListWidget, QGraphicsOpacityEffect
from httpx import HTTPError

import app.resources.resource  # type: ignore
from app.builtin.update_widget import UpdateWidget
from app.modules.suggestions.views import SuggestionPanel
from app.modules.suggestions.view_models import SuggestionViewModel
from app.modules.suggestions.integration import MoodSuggestionIntegration
from app.modules.projects.view_models import ProjectViewModel
from app.modules.projects.views import ProjectCreateDialog, ProjectViewWidget, ProjectEditDialog
from app.modules.tasks.view_models import TaskViewModel
from app.modules.tasks.views import TaskCreateDialog, TaskViewWidget
from app.modules.tasks.gantt_view_model import GanttViewModel
from app.ui.gantt.gantt_view import GanttChartWidget
from app.modules.tasks.models import TaskStatus
from app.modules.gamification.view_models import ProgressViewModel
from app.ui.gamification.progress_widget import ProgressWidget
from app.ui.kanban.kanban_board import KanbanBoardWidget
from app.core.shortcut_manager import ShortcutManager
from app.core.undo_manager import UndoManager
from app.ui.shortcut_help_dialog import ShortcutHelpDialog
from app.utils.shortcut_definitions import get_default_shortcuts
from app.modules.tag_enrichment.enrichment_service import EnrichmentService
from app.modules.tag_enrichment.integration import TagEnrichmentIntegration
from app.modules.tag_management.services import TagService
from app.ui.settings.api_keys_dialog import ApiKeysDialog
from app.modules.file_ingestion.views import ImportDialog
from app.modules.file_ingestion.services import ExtractionService
from app.ui.tag_management.filter_panel import FilterPanel
from app.modules.tag_management.view_models import TagViewModel
# from app.modules.habits.ui import HabitTrackerView  # Using placeholder for now
# from app.modules.habits.service import HabitService  # Using placeholder for now
from app.modules.ai_copilot.services import CopilotCommunicationService
from app.modules.ai_copilot.view_models import CopilotViewModel
from app.modules.ai_copilot.mood_integration import MoodAwareCopilotIntegration
from app.database import SessionLocal
from app.ui.navigation.sidebar import NavigationSidebar
from app.ui.navigation.content_area import ContentArea
from app.ui.tasks.task_view_container import TaskViewContainer
from app.ui.tasks.task_list_view import TaskListView
from app.ui.dashboard.dashboard_widget import DashboardWidget
from app.ui.dashboard.dashboard_view import DashboardView
from app.ui.copilot.action_panel import CopilotActionPanel
from app.ui.calendar.calendar_view import CalendarView
from app.ui.habits.habits_view import HabitsView
from app.ui.progress.progress_view import ProgressView
from app.modules.notes.view_models import NotesViewModel
from app.ui.notes.notes_view import NotesView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("Sageframe"))
        self.setWindowIcon(QIcon(":/logo.png"))

        self.setMinimumSize(960, 640)
        
        # Initialize undo/redo manager
        self.undo_manager = UndoManager(self)
        
        # Create new navigation layout
        self._setup_navigation_layout()
        
        # Initialize co-pilot action panel (EARLY - before dashboard setup)
        self._initialize_copilot_action_panel()
        
        # Initialize project management system
        self._initialize_project_system()
        
        # Initialize task management system
        self._initialize_task_system()

        # Initialize gamification progress display
        self._initialize_gamification()
        
        # Initialize habit tracker
        self._initialize_habit_tracker()
        
        # Initialize calendar view
        self._initialize_calendar_view()
        
        # Initialize notes view
        self._initialize_notes_view()
        
        # Initialize suggestion system
        self._initialize_suggestion_system()
        from app.modules.tag_enrichment.enrichment_service import EnrichmentService
        from app.modules.tag_enrichment.integration import TagEnrichmentIntegration
        from app.modules.tag_management.services import TagService
        from app.ui.settings.api_keys_dialog import ApiKeysDialog
        from app.modules.file_ingestion.views import ImportDialog
        from app.modules.file_ingestion.services import ExtractionService
        
        # Initialize keyboard shortcuts and menus (BEFORE copilot so it can reference shortcuts)
        self._initialize_shortcuts()
        self._create_menus_and_toolbars()
        
        # Initialize AI co-pilot communication (AFTER shortcuts)
        self._initialize_copilot()
        from app.modules.tag_management.services import TagService
        from app.ui.settings.api_keys_dialog import ApiKeysDialog
    
    def _setup_navigation_layout(self):
        """Set up the new side navigation + content area layout."""
        # Create central widget with horizontal layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create navigation sidebar
        self.nav_sidebar = NavigationSidebar(self)
        self.nav_sidebar.navigationChanged.connect(self._on_navigation_changed)
        main_layout.addWidget(self.nav_sidebar)
        
        # Create content area
        self.content_area = ContentArea(self)
        main_layout.addWidget(self.content_area, stretch=1)
        
        # Set central widget
        self.setCentralWidget(central_widget)
    
    def _show_toast(self, message: str, color: str = "#2ecc71", duration_ms: int = 1800):
        """Show a transient toast-style notification with fade in/out."""
        try:
            if hasattr(self, "_toast_label") and getattr(self, "_toast_label", None):
                self._toast_label.deleteLater()
            toast = QLabel(message, self)
            toast.setObjectName("toastNotification")
            toast.setStyleSheet(
                f"""
                QLabel#toastNotification {{
                    background-color: {color};
                    color: #0d1f0d;
                    border-radius: 10px;
                    padding: 10px 16px;
                    font-weight: bold;
                }}
                """
            )
            toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
            toast.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            toast.adjustSize()
            x_pos = max(12, (self.width() - toast.width()) // 2)
            toast.move(x_pos, 20)

            effect = QGraphicsOpacityEffect(toast)
            effect.setOpacity(0.0)
            toast.setGraphicsEffect(effect)
            toast.show()

            anim = QPropertyAnimation(effect, b"opacity", self)
            anim.setDuration(duration_ms + 400)
            anim.setStartValue(0.0)
            anim.setKeyValueAt(0.1, 1.0)
            anim.setEndValue(0.0)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            anim.finished.connect(lambda: toast.deleteLater())
            anim.start()

            self._toast_label = toast
            self._toast_animation = anim
        except Exception as e:
            print(f"Warning: Could not show toast notification: {e}")
    
    def _initialize_copilot_action_panel(self):
        """Initialize the co-pilot action panel (Phase 2 central hub)."""
        # Create the action panel
        self.copilot_action_panel = CopilotActionPanel(parent=self)
        
        # Connect action buttons to handlers
        self.copilot_action_panel.actionTriggered.connect(self._on_copilot_action_triggered)
        
        # Create dashboard with action panel embedded
        self.dashboard_widget = DashboardWidget(action_panel=self.copilot_action_panel, parent=self)
        
        # Connect dashboard quick add signals
        self.dashboard_widget.create_task_requested.connect(self._on_quick_add_task)
        self.dashboard_widget.create_note_requested.connect(self._on_quick_add_note)
        self.dashboard_widget.import_document_requested.connect(self._on_quick_add_import)
        
        self.content_area.set_widget_for_section("dashboard", self.dashboard_widget)
        
        # Show dashboard by default
        self.content_area.show_dashboard()
    
    def _on_copilot_action_triggered(self, action_name: str):
        """Handle co-pilot action button clicks."""
        action_handlers = {
            CopilotActionPanel.ACTION_CALENDAR: self._on_action_calendar,
            CopilotActionPanel.ACTION_NOTES: self._on_action_notes,
            CopilotActionPanel.ACTION_SUGGESTIONS: self._on_action_suggestions,
            CopilotActionPanel.ACTION_PROGRESS: self._on_action_progress,
            CopilotActionPanel.ACTION_HABITS: self._on_action_habits,
            CopilotActionPanel.ACTION_MOOD: self._on_action_mood,
        }
        
        if action_name in action_handlers:
            action_handlers[action_name]()
    
    def _on_action_calendar(self):
        """Handle Calendar action button."""
        self.nav_sidebar.set_active_section(NavigationSidebar.CALENDAR)
        # TODO: Phase 4 - Load calendar view and display
    
    def _on_action_notes(self):
        """Handle Notes action button."""
        self.nav_sidebar.set_active_section(NavigationSidebar.NOTES)
    
    def _on_action_suggestions(self):
        """Handle Suggestions action button."""
        # TODO: Phase 5 - Generate and display suggestions in action panel
        self.copilot_action_panel.display_message("✨ Generating personalized suggestions...", "suggestions_loading")
    
    def _on_action_progress(self):
        """Handle Progress action button."""
        self.nav_sidebar.set_active_section(NavigationSidebar.PROGRESS)
    
    def _on_action_habits(self):
        """Handle Habits action button."""
        self.nav_sidebar.set_active_section(NavigationSidebar.HABITS)
    
    def _on_action_mood(self):
        """Handle Mood action button."""
        self._open_mood_checkin()
    
    def _on_navigation_changed(self, section: str):
        """Handle navigation section change."""
        section_map = {
            NavigationSidebar.DASHBOARD: self.content_area.show_dashboard,
            NavigationSidebar.CALENDAR: self.content_area.show_calendar,
            NavigationSidebar.TASKS: self.content_area.show_tasks,
            NavigationSidebar.NOTES: self.content_area.show_notes,
            NavigationSidebar.PROJECTS: self.content_area.show_projects,
            NavigationSidebar.HABITS: self.content_area.show_habits,
            NavigationSidebar.PROGRESS: self.content_area.show_progress,
            NavigationSidebar.SETTINGS: self.content_area.show_settings,
        }
        
        if section in section_map:
            section_map[section]()
    
    def _initialize_project_system(self):
        """Initialize the project management system with view model and UI."""
        from PySide6.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QSplitter
        
        # Create view model for projects with undo support
        self.project_view_model = ProjectViewModel(parent=self, undo_manager=self.undo_manager)
        
        # Create project list widget (no dock, will be embedded)
        project_list_widget = QWidget()
        project_layout = QVBoxLayout(project_list_widget)
        project_layout.setContentsMargins(12, 12, 12, 12)
        
        # Add "New Project" button
        new_project_btn = QPushButton("+ New Project")
        new_project_btn.setObjectName("newProjectButton")
        new_project_btn.clicked.connect(self._open_create_project_dialog)
        project_layout.addWidget(new_project_btn)
        
        # Add project list
        self.project_list = QListWidget()
        self.project_list.setObjectName("projectList")
        self.project_list.itemDoubleClicked.connect(self._on_project_double_clicked)
        project_layout.addWidget(self.project_list)
        
        # Store reference and embed in content area
        self.projects_view = project_list_widget
        self.content_area.set_widget_for_section("projects", self.projects_view)
        
        # Connect ViewModel signals
        self.project_view_model.projectCreated.connect(self._on_project_created)
        self.project_view_model.projectUpdated.connect(self._on_project_updated)
        self.project_view_model.projectDeleted.connect(self._on_project_deleted)
        self.project_view_model.projectsListChanged.connect(self._refresh_project_list)
        self.project_view_model.validationError.connect(
            lambda msg: QMessageBox.warning(self, self.tr("Validation Error"), msg)
        )
        self.project_view_model.operationError.connect(
            lambda msg: QMessageBox.critical(self, self.tr("Error"), msg)
        )
        
        # Load initial projects (signal will trigger _refresh_project_list)
        self.project_view_model.refresh_projects()
        
        # Defer greeting until after full initialization
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, self._show_startup_greeting)

    def _initialize_task_system(self):
        """Initialize the task management system with view model and UI."""
        # Create view model for tasks with undo support
        self.task_view_model = TaskViewModel(parent=self, undo_manager=self.undo_manager)

        # Create task view container with switcher
        self.task_view_container = TaskViewContainer(parent=self)
        
        # Create list view
        self.task_list_view = TaskListView(self.task_view_model, parent=self)
        self.task_list_view.taskDoubleClicked.connect(self._on_task_item_double_clicked)
        self.task_list_view.createTaskRequested.connect(self._open_create_task_dialog)
        self.task_view_container.set_list_view(self.task_list_view)
        
        # Create Kanban board
        self.kanban_board = KanbanBoardWidget(self.task_view_model, parent=self)
        self.task_view_container.set_kanban_view(self.kanban_board)

        # Create Gantt chart
        self.gantt_view_model = GanttViewModel(
            service=self.task_view_model._service,
            refresh_callback=self._on_gantt_data_changed,
        )
        self.gantt_chart = GanttChartWidget(self.gantt_view_model, parent=self)
        self.gantt_chart.taskClicked.connect(self._on_task_item_double_clicked)
        self.task_view_container.set_gantt_view(self.gantt_chart)
        
        # Embed task container in content area
        self.content_area.set_widget_for_section("tasks", self.task_view_container)

        # Connect ViewModel signals
        self.task_view_model.taskCreated.connect(self._on_task_created)
        self.task_view_model.taskUpdated.connect(self._on_task_updated)
        self.task_view_model.taskDeleted.connect(self._on_task_deleted)
        self.task_view_model.tasksListChanged.connect(self._refresh_gantt_chart)
        self.task_view_model.taskUpdated.connect(self._refresh_progress)
        self.task_view_model.taskCreated.connect(self._refresh_progress)
        self.task_view_model.taskDeleted.connect(self._refresh_progress)
        self.task_view_model.validationError.connect(
            lambda msg: QMessageBox.warning(self, self.tr("Validation Error"), msg)
        )
        self.task_view_model.operationError.connect(
            lambda msg: QMessageBox.critical(self, self.tr("Error"), msg)
        )

        # Load initial tasks
        self.task_view_model.refresh_tasks()
        self.gantt_chart.refresh()
    
    def _on_task_item_double_clicked(self, task_id: int):
        """Handle task item double click from list view."""
        # Load task and open edit dialog
        if self.task_view_model.load_task(task_id):
            from PySide6.QtWidgets import QDialog, QVBoxLayout
            
            # Create a dialog to wrap the TaskViewWidget
            dialog = QDialog(self)
            dialog.setWindowTitle("Task Details")
            dialog.setMinimumSize(600, 500)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Add TaskViewWidget to the dialog
            task_widget = TaskViewWidget(
                view_model=self.task_view_model,
                task_id=task_id,
                parent=dialog
            )
            layout.addWidget(task_widget)
            
            # Show as modal dialog
            dialog.exec()
    
    def _initialize_suggestion_system(self):
        """Initialize the suggestion system with integration layer."""
        # Create view model for suggestions
        self.suggestion_view_model = SuggestionViewModel()
        
        # Create suggestion panel (will be embedded in co-pilot area later)
        self.suggestion_panel = SuggestionPanel(self.suggestion_view_model, parent=self)
        
        # Create integration layer
        self.mood_suggestion_integration = MoodSuggestionIntegration(
            parent=self
        )
        
        # Connect integration to view model
        self.mood_suggestion_integration.suggestionsReady.connect(
            self._on_suggestions_ready
        )

        # Track last mood context for refresh shortcut
        self._last_mood = "neutral"
        self._last_energy = "medium"
        
        # Initialize enrichment system (workers + global integration)
        self._initialize_enrichment_system()

        # Initialize extraction system
        self._initialize_extraction_system()

    def _initialize_gamification(self):
        """Set up gamification progress view."""
        self.progress_view_model = ProgressViewModel(parent=self)
        self.progress_widget = ProgressWidget(self.progress_view_model, parent=self)
        self.progress_view_model.levelUp.connect(self._on_level_up)

        # Embed old progress widget in content area
        self.content_area.set_widget_for_section("progress", self.progress_widget)
        self._last_known_level = self.progress_view_model.get_cached().get("current_level", 1)
        
        # Also create new progress view (placeholder)
        # self.progress_view = ProgressView(parent=self)
        # self.content_area.set_widget_for_section("progress", self.progress_view)

    def _initialize_habit_tracker(self):
        """Set up habit tracker view."""
        # Use new placeholder view for now
        self.habit_tracker_view = HabitsView(parent=self)
        
        # Embed in content area
        self.content_area.set_widget_for_section("habits", self.habit_tracker_view)
    
    def _toggle_habit_panel(self):
        """Navigate to habits view."""
        if hasattr(self, 'nav_sidebar'):
            self.nav_sidebar.set_active_section(NavigationSidebar.HABITS)
    
    def _initialize_calendar_view(self):
        """Set up calendar view with Google Calendar integration."""
        self.calendar_view = CalendarView(parent=self)
        self.content_area.set_widget_for_section("calendar", self.calendar_view)
    
    def _initialize_notes_view(self):
        """Set up notes view with Google Keep-style interface."""
        # Create notes view model
        self.notes_view_model = NotesViewModel(parent=self)
        
        # Create notes view
        self.notes_view = NotesView(self.notes_view_model, parent=self)
        
        # Set notes view in content area
        self.content_area.set_widget_for_section("notes", self.notes_view)

    def _initialize_copilot(self):
        """Initialize the AI Co-Pilot communication system."""
        try:
            # Create database session for co-pilot
            db_session = SessionLocal()
            
            # Initialize co-pilot service (Message generation, tone validation, storage)
            self.copilot_service = CopilotCommunicationService(db_session)
            
            # Initialize co-pilot view model (MVVM state management)
            self.copilot_vm = CopilotViewModel(db_session)
            
            # Connect ViewModel signals to Panel (disconnect first to prevent duplicates)
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                try:
                    self.copilot_vm.messageReady.disconnect()
                except (RuntimeError, TypeError):
                    pass  # Signal wasn't connected yet, ignore
            self.copilot_vm.messageReady.connect(self._on_copilot_message_ready)
            
            # Connect co-pilot to mood check-in for automatic mood-aware responses
            try:
                self.mood_integration = MoodAwareCopilotIntegration(
                    mood_service=None,  # Will be set up when mood check-in completes
                    copilot_service=self.copilot_service,
                    copilot_viewmodel=self.copilot_vm,
                )
                # Mood integration will be fully wired up in _on_mood_checkin_completed
            except Exception as e:
                print(f"Warning: Could not initialize mood integration: {e}")
            
        except Exception as e:
            print(f"Error initializing co-pilot: {e}")
            # Continue without co-pilot if initialization fails
    
    def _initialize_shortcuts(self):
        """Set up global keyboard shortcuts and help dialog trigger."""
        self.shortcut_manager = ShortcutManager(self)

        definitions = get_default_shortcuts()
        callbacks = {
            "open_shortcut_help": self._open_shortcut_help,
            "open_mood_checkin": self._open_mood_checkin,
            "toggle_suggestion_panel": self._toggle_suggestion_panel,
            "refresh_suggestions": self._refresh_suggestions,
            "undo": self._undo,
            "redo": self._redo,
                "create_task": self._open_create_task_dialog,
        }
        self.shortcut_manager.register_many(definitions, callbacks)
        
        # Connect undo manager signals to UI updates
        self.undo_manager.can_undo_changed.connect(self._on_undo_state_changed)
        self.undo_manager.can_redo_changed.connect(self._on_redo_state_changed)
    
    def _create_menus_and_toolbars(self) -> None:
        """Create menu bar and toolbar with Undo/Redo actions.
        
        Addresses AC3 requirement: UI elements reflect undo/redo availability.
        """
        # Create Edit menu
        edit_menu = self.menuBar().addMenu(self.tr("Edit"))
        
        # Create Undo action
        self.undo_action = QAction(self.tr("Undo"), self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.setStatusTip(self.tr("Undo the last action"))
        self.undo_action.triggered.connect(self._undo)
        self.undo_action.setEnabled(False)
        edit_menu.addAction(self.undo_action)
        
        # Create Redo action
        self.redo_action = QAction(self.tr("Redo"), self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.setStatusTip(self.tr("Redo the last undone action"))
        self.redo_action.triggered.connect(self._redo)
        self.redo_action.setEnabled(False)
        edit_menu.addAction(self.redo_action)
        
        # Create Projects menu
        projects_menu = self.menuBar().addMenu(self.tr("Projects"))
        
        # New Project action
        new_project_action = QAction(self.tr("New Project..."), self)
        new_project_action.setShortcut(QKeySequence("Ctrl+N"))
        new_project_action.setStatusTip(self.tr("Create a new project"))
        new_project_action.triggered.connect(self._open_create_project_dialog)
        projects_menu.addAction(new_project_action)
        
        projects_menu.addSeparator()
        
        # Toggle Project Panel action
        toggle_projects_action = QAction(self.tr("Show/Hide Projects Panel"), self)
        toggle_projects_action.triggered.connect(self._toggle_project_panel)
        projects_menu.addAction(toggle_projects_action)
        
        # Create Tasks menu
        tasks_menu = self.menuBar().addMenu(self.tr("Tasks"))
        
        # New Task action
        new_task_action = QAction(self.tr("New Task..."), self)
        new_task_action.setShortcut(QKeySequence("Ctrl+T"))
        new_task_action.setStatusTip(self.tr("Create a new task"))
        new_task_action.triggered.connect(self._open_create_task_dialog)
        tasks_menu.addAction(new_task_action)
        
        tasks_menu.addSeparator()
        
        # Toggle Task Panel action
        toggle_tasks_action = QAction(self.tr("Show/Hide Tasks Panel"), self)
        toggle_tasks_action.triggered.connect(self._toggle_task_panel)
        tasks_menu.addAction(toggle_tasks_action)

        # Toggle Kanban action
        toggle_kanban_action = QAction(self.tr("Show/Hide Kanban Board"), self)
        toggle_kanban_action.triggered.connect(self._toggle_kanban_panel)
        tasks_menu.addAction(toggle_kanban_action)

        # Toggle Gantt action
        toggle_gantt_action = QAction(self.tr("Show/Hide Gantt Chart"), self)
        toggle_gantt_action.triggered.connect(self._toggle_gantt_panel)
        tasks_menu.addAction(toggle_gantt_action)
        
        # Create Habits menu
        habits_menu = self.menuBar().addMenu(self.tr("Habits"))
        
        # Toggle Habits Panel action
        toggle_habits_action = QAction(self.tr("Show/Hide Habits Panel"), self)
        toggle_habits_action.triggered.connect(self._toggle_habit_panel)
        habits_menu.addAction(toggle_habits_action)
        
        # Create File menu
        file_menu = self.menuBar().addMenu(self.tr("File"))
        import_action = QAction(self.tr("Import Document..."), self)
        import_action.setStatusTip(self.tr("Import a PDF/Image and extract information"))
        import_action.triggered.connect(self._open_import_dialog)
        file_menu.addAction(import_action)
        # Create toolbar
        toolbar = self.addToolBar(self.tr("Edit"))
        toolbar.setObjectName("EditToolBar")
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        toolbar.addAction(new_project_action)
        toolbar.addAction(new_task_action)

        # Create Settings menu
        settings_menu = self.menuBar().addMenu(self.tr("Settings"))
        api_keys_action = QAction(self.tr("API Keys..."), self)
        api_keys_action.setStatusTip(self.tr("Configure API keys for integrations"))
        api_keys_action.triggered.connect(self._open_api_keys_dialog)
        settings_menu.addAction(api_keys_action)
    
    def _undo(self) -> None:
        """Execute undo action."""
        self.undo_manager.undo()
    
    def _redo(self) -> None:
        """Execute redo action."""
        self.undo_manager.redo()
    
    def _on_undo_state_changed(self, can_undo: bool) -> None:
        """Handle undo availability state changes.
        
        Updates UI elements to reflect whether undo is available.
        Addresses AC3: "undo action is gracefully disabled or provides feedback"
        
        Args:
            can_undo: Whether undo is currently available
        """
        # Update menu and toolbar button states
        if hasattr(self, 'undo_action'):
            self.undo_action.setEnabled(can_undo)
            if can_undo:
                undo_description = self.undo_manager._undo_stack[-1].description if self.undo_manager._undo_stack else ""
                self.undo_action.setStatusTip(self.tr(f"Undo: {undo_description}"))
            else:
                self.undo_action.setStatusTip(self.tr("Undo (nothing to undo)"))
    
    def _on_redo_state_changed(self, can_redo: bool) -> None:
        """Handle redo availability state changes.
        
        Updates UI elements to reflect whether redo is available.
        
        Args:
            can_redo: Whether redo is currently available
        """
        # Update menu and toolbar button states
        if hasattr(self, 'redo_action'):
            self.redo_action.setEnabled(can_redo)
            if can_redo:
                redo_description = self.undo_manager._redo_stack[-1].description if self.undo_manager._redo_stack else ""
                self.redo_action.setStatusTip(self.tr(f"Redo: {redo_description}"))
            else:
                self.redo_action.setStatusTip(self.tr("Redo (nothing to redo)"))
    
    
    def _on_suggestions_ready(self, suggestions):
        """Handle suggestions from integration layer.
        
        Args:
            suggestions: List of suggestion dictionaries with messages
        """
        # Generate suggestions through the view model
        self.suggestion_view_model.generate_suggestions(
            mood=suggestions[0].get("mood_context", "neutral"),
            energy_level=suggestions[0].get("energy_context", "medium"),
            available_tasks=[],  # Tasks already used for generation
        )
        self._last_mood = suggestions[0].get("mood_context", "neutral")
        self._last_energy = suggestions[0].get("energy_context", "medium")
    
    def _add_mood_checkin_button(self):
        """Add mood check-in button to the main window."""
        from PySide6.QtWidgets import QPushButton
        from app.modules.mood_checkin.views import MoodCheckInDialog
        
        # Create mood check-in button
        self.mood_checkin_button = QPushButton("Mood Check-in", self)
        self.mood_checkin_button.setObjectName("moodCheckInButton")
        self.mood_checkin_button.setGeometry(20, 20, 150, 40)  # Top-left corner
        self.mood_checkin_button.clicked.connect(self._open_mood_checkin)
        self.mood_checkin_button.setToolTip("Mood Check-in (Shortcut: Ctrl+Shift+M)")
    
    def _open_mood_checkin(self):
        """Open mood check-in dialog."""
        from app.modules.mood_checkin.views import MoodCheckInDialog
        
        dialog = MoodCheckInDialog(self)
        
        # Connect dialog's mood check-in completion to suggestion generation
        if hasattr(dialog, 'view_model'):
            dialog.view_model.moodCheckInCompleted.connect(
                lambda success, msg: self._on_mood_checkin_completed(dialog)
                if success else None
            )
        
        dialog.exec()
    
    def _on_mood_checkin_completed(self, dialog):
        """Handle mood check-in completion and trigger suggestions + co-pilot.
        
        Args:
            dialog: The MoodCheckInDialog instance
        """
        print("\n=== MOOD CHECK-IN COMPLETED ===")
        if hasattr(dialog, 'view_model'):
            mood = dialog.view_model.moodLevel
            energy = dialog.view_model.energyLevel
            print(f"Mood: {mood}, Energy: {energy}")
            self._show_toast("Mood saved", "#2ecc71")
            # If Gemini isn't configured, surface it in the UI so users know why responses may be basic
            try:
                if hasattr(self, 'copilot_service') and not getattr(self.copilot_service, 'use_llm', False):
                    import uuid
                    missing_msg = (
                        "🔑 Gemini API key not detected. Add it in Settings → API Keys to unlock full co-pilot responses. "
                        "Showing fallback guidance for now."
                    )
                    msg_id = str(uuid.uuid4())
                    if hasattr(self, 'copilot_action_panel'):
                        self.copilot_action_panel.display_message(
                            message_text=missing_msg,
                            message_id=msg_id,
                            response_buttons=[
                                {
                                    "id": "open_settings",
                                    "text": "Open Settings",
                                    "icon": "⚙️",
                                    "callback": lambda: self.nav_sidebar.set_active_section(NavigationSidebar.SETTINGS)
                                }
                            ],
                        )
            except Exception as diag_err:
                print(f"Warning: Could not show Gemini configuration notice: {diag_err}")
            
            # Set sample tasks for demonstration (will be replaced with real task list)
            sample_tasks = [
                {"id": "task_1", "name": "Focus work", "difficulty": "hard"},
                {"id": "task_2", "name": "Quick break", "difficulty": "easy"},
                {"id": "task_3", "name": "Code review", "difficulty": "medium"},
            ]
            
            self.mood_suggestion_integration.set_available_tasks(sample_tasks)
            
            # Trigger suggestion generation
            self.mood_suggestion_integration.on_mood_checkin_completed(
                mood=mood,
                energy_level=energy,
                user_activity_state=None,
            )
            
            # Trigger co-pilot mood-aware response
            try:
                print("Attempting to generate co-pilot response...")
                if hasattr(self, 'copilot_service') and hasattr(self, 'copilot_vm'):
                    print(f"Co-pilot service available: {self.copilot_service is not None}")
                    print(f"Using LLM: {getattr(self.copilot_service, 'use_llm', False)}")
                    # Generate mood-aware response from co-pilot
                    response = self.copilot_service.generate_mood_response(
                        mood=mood,
                        energy_level=energy
                    )
                    print(f"Generated response: {response[:100] if response else 'None'}...")
                    if not response:
                        response = "Thanks for sharing how you're feeling. I've saved it—want to review priorities now?"
                        print("Using fallback response (no LLM response)")
                    
                    # Validate tone compliance; if invalid, fall back to safe copy
                    is_valid, validation_err = self.copilot_service.validate_message_tone(response)
                    print(f"Mood response validation: {is_valid}, Error: {validation_err}")
                    if not is_valid:
                        response = "Thanks for sharing how you're feeling. I've saved it—want to review priorities now?"
                        print("Using fallback response (validation failed)")
                    
                    msg_id = None
                    try:
                        msg_id = self.copilot_service.generate_and_store_message(
                            message_text=response,
                            category="mood_response",
                            user_mood=mood,
                            energy_level=energy,
                        )
                        print(f"Stored mood response with ID: {msg_id}")
                    except Exception as store_err:
                        print(f"Warning: Could not store mood response: {store_err}")
                    
                    # Display through ViewModel (which triggers UI update)
                    print(f"Attempting to display mood response. msg_id={msg_id}, has_vm={hasattr(self, 'copilot_vm')}")
                    if msg_id and hasattr(self, 'copilot_vm'):
                        print("Emitting message via copilot_vm...")
                        self.copilot_vm.emit_message_ready(response, msg_id)
                    elif not msg_id:
                        # Only use direct display if storage failed (no msg_id)
                        print("Using direct panel display (storage failed)")
                        try:
                            import uuid
                            fallback_id = str(uuid.uuid4())
                            print(f"Fallback display ID: {fallback_id}")
                            if hasattr(self, 'copilot_action_panel'):
                                print("Displaying mood response directly in action panel...")
                                self.copilot_action_panel.display_message(
                                    message_text=response,
                                    message_id=fallback_id,
                                )
                                print("Mood response displayed successfully")
                        except Exception as panel_err:
                            print(f"Warning: Could not display mood response: {panel_err}")

                    # Generate task prioritization guidance using LLM with tasks snapshot
                    print("\n--- Generating task prioritization ---")
                    try:
                        tasks_snapshot = []
                        if hasattr(self, 'task_view_model') and hasattr(self.task_view_model, 'get_tasks_list'):
                            try:
                                tasks_snapshot = self.task_view_model.get_tasks_list()
                            except Exception:
                                tasks_snapshot = []

                        # Trim to top 6 tasks by due/priority if available
                        tasks_snapshot = tasks_snapshot[:6] if isinstance(tasks_snapshot, list) else []

                        print(f"Tasks snapshot count: {len(tasks_snapshot)}")
                        prioritization = self.copilot_service.generate_task_prioritization(
                            mood=mood,
                            energy_level=energy,
                            tasks_snapshot=tasks_snapshot,
                        )
                        print(f"Generated prioritization: {prioritization[:100] if prioritization else 'None'}...")

                        # Store and display prioritization
                        msg_id2 = self.copilot_service.generate_and_store_message(
                            message_text=prioritization,
                            category="mood_task_recommendation",
                            user_mood=mood,
                            energy_level=energy,
                        )
                        print(f"Stored prioritization with ID: {msg_id2}")

                        response_buttons = [
                            {
                                "id": "view_tasks",
                                "text": "View tasks",
                                "icon": "✅",
                                "callback": lambda: self.nav_sidebar.set_active_section(NavigationSidebar.TASKS)
                            },
                            {
                                "id": "mark_today",
                                "text": "Mark as today",
                                "icon": "📌",
                                "callback": lambda: self._handle_mark_tasks_today(mood, energy, tasks_snapshot)
                            },
                            {
                                "id": "snooze",
                                "text": "Snooze suggested",
                                "icon": "🕒",
                                "callback": lambda: self._handle_snooze_tasks(mood, energy, tasks_snapshot)
                            },
                        ]

                        # Display via ViewModel OR direct panel as fallback
                        print(f"Attempting to display prioritization. msg_id2={msg_id2}")
                        if msg_id2 and hasattr(self, 'copilot_vm'):
                            print("Emitting prioritization via copilot_vm with buttons...")
                            # Store buttons for the message handler to use
                            if not hasattr(self, '_pending_response_buttons'):
                                self._pending_response_buttons = {}
                            self._pending_response_buttons[msg_id2] = response_buttons
                            self.copilot_vm.emit_message_ready(prioritization, msg_id2)
                            print("Prioritization emitted via VM")
                        else:
                            # Fallback: direct display if VM not available or storage failed
                            print("Using direct panel display for prioritization...")
                            try:
                                import uuid
                                display_id = msg_id2 or str(uuid.uuid4())
                                print(f"Displaying prioritization in action panel (ID: {display_id})...")
                                self.copilot_action_panel.display_message(
                                    message_text=prioritization,
                                    message_id=display_id,
                                    response_buttons=response_buttons
                                )
                                print("Prioritization displayed successfully")
                            except Exception as panel_err:
                                print(f"Warning: Could not display prioritization: {panel_err}")
                                import traceback
                                traceback.print_exc()
                        if not msg_id2:
                            print("Warning: Prioritization message was empty or could not be stored")
                    except Exception as e:
                        print(f"Warning: Could not generate prioritization: {e}")
                        import traceback
                        traceback.print_exc()
            except Exception as e:
                print(f"Warning: Could not generate co-pilot response: {e}")
                import traceback
                traceback.print_exc()
        print("=== MOOD CHECK-IN HANDLER COMPLETED ===\n")
    
    def _handle_mark_tasks_today(self, mood: str, energy: str, tasks_snapshot: list):
        """Use LLM to select tasks and mark them for today."""
        try:
            print(f"\n=== MARK AS TODAY: mood={mood}, energy={energy}, tasks={len(tasks_snapshot)} ===")
            if not hasattr(self, 'copilot_service') or not hasattr(self, 'task_view_model'):
                self._show_toast("Task management not available", "#f87171")
                return
            
            # Ask LLM to select tasks
            selection = self.copilot_service.select_tasks_for_action(
                action='mark_today',
                mood=mood,
                energy_level=energy,
                tasks_snapshot=tasks_snapshot
            )
            
            task_ids = selection.get('task_ids', [])
            reason = selection.get('reason', '')
            print(f"LLM selected tasks: {task_ids}, Reason: {reason}")
            
            if not task_ids:
                self._show_toast("No tasks selected for today", "#fbbf24")
                return
            
            # Update tasks to today's date
            from datetime import date
            today = date.today()
            updated_count = 0
            
            for task_id in task_ids:
                try:
                    # Load task to get current data
                    task = self.task_view_model._service.get_task(task_id)
                    if task:
                        # Update due date to today
                        success = self.task_view_model.update_task(
                            task_id=task_id,
                            title=task.title,
                            description=task.description or "",
                            due_date=today,
                            status=task.status,
                            priority=task.priority,
                            complexity=task.complexity,
                            project_id=task.project_id,
                        )
                        if success:
                            updated_count += 1
                            print(f"Marked task {task_id} for today")
                except Exception as e:
                    print(f"Warning: Could not update task {task_id}: {e}")
            
            if updated_count > 0:
                self.task_view_model.refresh_tasks()
                self._show_toast(f"✅ {updated_count} task{'s' if updated_count > 1 else ''} marked for today", "#4ade80")
                if reason:
                    # Show LLM's reasoning in copilot panel
                    try:
                        import uuid
                        self.copilot_action_panel.display_message(
                            message_text=f"📌 {reason}",
                            message_id=str(uuid.uuid4())
                        )
                    except:
                        pass
            else:
                self._show_toast("Could not update tasks", "#f87171")
                
        except Exception as e:
            print(f"Error in mark_tasks_today: {e}")
            import traceback
            traceback.print_exc()
            self._show_toast("Error marking tasks", "#f87171")
    
    def _handle_snooze_tasks(self, mood: str, energy: str, tasks_snapshot: list):
        """Use LLM to select tasks and snooze them to a later date."""
        try:
            print(f"\n=== SNOOZE TASKS: mood={mood}, energy={energy}, tasks={len(tasks_snapshot)} ===")
            if not hasattr(self, 'copilot_service') or not hasattr(self, 'task_view_model'):
                self._show_toast("Task management not available", "#f87171")
                return
            
            # Ask LLM to select tasks to defer
            selection = self.copilot_service.select_tasks_for_action(
                action='snooze',
                mood=mood,
                energy_level=energy,
                tasks_snapshot=tasks_snapshot
            )
            
            task_ids = selection.get('task_ids', [])
            defer_days = selection.get('defer_days', 2)
            reason = selection.get('reason', '')
            print(f"LLM selected tasks to snooze: {task_ids}, Defer: {defer_days} days, Reason: {reason}")
            
            if not task_ids:
                self._show_toast("No tasks to snooze", "#fbbf24")
                return
            
            # Defer tasks by pushing due dates forward
            from datetime import date, timedelta
            updated_count = 0
            
            for task_id in task_ids:
                try:
                    task = self.task_view_model._service.get_task(task_id)
                    if task:
                        # Calculate new due date
                        current_due = task.due_date if task.due_date else date.today()
                        new_due = current_due + timedelta(days=defer_days)
                        
                        success = self.task_view_model.update_task(
                            task_id=task_id,
                            title=task.title,
                            description=task.description or "",
                            due_date=new_due,
                            status=task.status,
                            priority=task.priority,
                            complexity=task.complexity,
                            project_id=task.project_id,
                        )
                        if success:
                            updated_count += 1
                            print(f"Snoozed task {task_id} to {new_due}")
                except Exception as e:
                    print(f"Warning: Could not snooze task {task_id}: {e}")
            
            if updated_count > 0:
                self.task_view_model.refresh_tasks()
                self._show_toast(f"🕒 {updated_count} task{'s' if updated_count > 1 else ''} snoozed", "#8b5cf6")
                if reason:
                    # Show LLM's reasoning
                    try:
                        import uuid
                        self.copilot_action_panel.display_message(
                            message_text=f"🕒 {reason}",
                            message_id=str(uuid.uuid4())
                        )
                    except:
                        pass
            else:
                self._show_toast("Could not snooze tasks", "#f87171")
                
        except Exception as e:
            print(f"Error in snooze_tasks: {e}")
            import traceback
            traceback.print_exc()
            self._show_toast("Error snoozing tasks", "#f87171")

    def _on_copilot_message_ready(self, message_id: str):
        """Handle when a co-pilot message is ready to display in action panel."""
        if hasattr(self, 'copilot_action_panel') and hasattr(self, 'copilot_vm'):
            # Get the current message from ViewModel
            message_text = self.copilot_vm.currentMessage
            if message_text:
                # Check if this is a greeting message (always ends with "How are you feeling?")
                response_buttons = None
                
                # Check if there are pending response buttons for this message
                if hasattr(self, '_pending_response_buttons') and message_id in self._pending_response_buttons:
                    response_buttons = self._pending_response_buttons.pop(message_id)
                elif "How are you feeling?" in message_text:
                    # Add interactive response buttons for greeting
                    response_buttons = [
                        {
                            "id": "check_mood",
                            "text": "Check my mood",
                            "icon": "🎭",
                            "callback": self._open_mood_checkin
                        },
                        {
                            "id": "view_tasks",
                            "text": "View tasks",
                            "icon": "✅",
                            "callback": lambda: self.nav_sidebar.set_active_section(NavigationSidebar.TASKS)
                        },
                        {
                            "id": "just_browsing",
                            "text": "Just browsing",
                            "icon": "💬",
                            "callback": lambda: None  # Just dismiss
                        }
                    ]
                
                # Display in the action panel's response area
                self.copilot_action_panel.display_message(
                    message_text=message_text,
                    message_id=message_id,
                    response_buttons=response_buttons
                )
                
                # Also ensure we're on the dashboard to see the message
                if hasattr(self, 'nav_sidebar'):
                    self.nav_sidebar.set_active_section(NavigationSidebar.DASHBOARD)
    
    def _show_startup_greeting(self):
        """Show personalized greeting from co-pilot on app startup."""
        try:
            if not hasattr(self, 'copilot_service') or not hasattr(self, 'copilot_vm'):
                return
            
            from datetime import datetime
            import uuid
            
            # Determine time of day
            hour = datetime.now().hour
            if hour < 12:
                time_of_day = "morning"
            elif hour < 17:
                time_of_day = "afternoon"
            else:
                time_of_day = "evening"
            
            # Get task count for greeting
            task_count = 0
            if hasattr(self, 'task_view_model'):
                try:
                    task_count = len(self.task_view_model.tasks)
                except:
                    pass
            
            # Check if API key is configured
            from app.modules.ai_copilot.gemini_integration import is_gemini_configured
            
            if not is_gemini_configured():
                # Show API key setup message with task count
                greeting_msg = f"Good {time_of_day}, sir! 👋\n\nYou have {task_count} task{'s' if task_count != 1 else ''} for today. How are you feeling?\n\n🔑 To unlock AI-powered assistance and personalized suggestions, please add your Google Generative AI (Gemini) API key in Settings → API Keys.\n\n👉 Go to Settings → API Keys to configure your Gemini API key.\n\nOnce configured, I'll be able to provide intelligent insights and guide you through your day with empathetic support!"
            else:
                # Generate personalized greeting with LLM
                greeting_msg = self.copilot_service.generate_personalized_greeting(time_of_day)
            
            # Store and display the greeting
            msg_id = str(uuid.uuid4())
            try:
                self.copilot_service.save_communication_event(
                    message_id=msg_id,
                    message_text=greeting_msg,
                    category="greeting",
                    tone_level="gentle"
                )
            except Exception as save_err:
                print(f"Warning: Could not save greeting: {save_err}")
            
            # IMPORTANT: Display startup greeting DIRECTLY, bypassing deferral logic
            # Startup greetings should NEVER be deferred - they're the first thing users see
            # We bypass the ViewModel's deferral checks by directly emitting the messageReady signal
            if self.copilot_vm:
                # Set the ViewModel's current message
                self.copilot_vm.currentMessage = greeting_msg
                self.copilot_vm._current_message_id = msg_id
                self.copilot_vm.isMessagePending = True
                # Emit signal directly - this will trigger _on_copilot_message_ready() handler
                # which will display the message in the action panel
                self.copilot_vm.messageReady.emit(msg_id)
                    
        except Exception as e:
            print(f"Error: Could not show startup greeting: {e}")
            import traceback
            traceback.print_exc()

    def _open_shortcut_help(self):
        """Open the keyboard shortcuts help dialog."""
        grouped = self.shortcut_manager.get_shortcuts_by_category()
        dialog = ShortcutHelpDialog(grouped, self)
        dialog.exec()

    def _toggle_suggestion_panel(self):
        """Show suggestions (navigate to dashboard with suggestions)."""
        # TODO: Phase 2 will implement action-based suggestions in co-pilot panel
        # For now, navigate to dashboard
        if hasattr(self, 'nav_sidebar'):
            self.nav_sidebar.set_active_section(NavigationSidebar.DASHBOARD)

    def _toggle_kanban_panel(self):
        """Switch to Kanban view."""
        if hasattr(self, 'task_view_container'):
            self.task_view_container.view_switcher.setCurrentIndex(self.task_view_container.KANBAN_VIEW)
            if hasattr(self, 'nav_sidebar'):
                self.nav_sidebar.set_active_section(NavigationSidebar.TASKS)
    
    def _toggle_task_panel(self):
        """Navigate to tasks view."""
        if hasattr(self, 'nav_sidebar'):
            self.nav_sidebar.set_active_section(NavigationSidebar.TASKS)

    def _refresh_suggestions(self):
        """Regenerate suggestions using the latest known mood context."""
        # If we have known mood/energy, trigger a refresh via view model.
        self.suggestion_view_model.generate_suggestions(
            mood=getattr(self, "_last_mood", "neutral"),
            energy_level=getattr(self, "_last_energy", "medium"),
            available_tasks=[],
        )
    
    # Project Management Methods
    
    def _open_create_project_dialog(self):
        """Open dialog to create a new project."""
        dialog = ProjectCreateDialog(self.project_view_model, self)
        if dialog.exec():
            QMessageBox.information(
                self,
                self.tr("Success"),
                self.tr("Project created successfully!")
            )
    
    def _on_project_double_clicked(self, item):
        """Handle double-click on project list item."""
        from PySide6.QtWidgets import QListWidgetItem
        
        # Get project ID from item data
        project_id = item.data(Qt.ItemDataRole.UserRole)
        if project_id:
            self._open_project_view(project_id)
    
    def _open_project_view(self, project_id: int):
        """Open project view widget in a dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Project Details"))
        dialog.setMinimumSize(700, 600)
        
        layout = QVBoxLayout()
        
        # Create and add project view widget
        project_view = ProjectViewWidget(self.project_view_model, dialog)
        project_view.set_project_id(project_id)
        layout.addWidget(project_view)
        
        # Add task list section for this project (Subtask 5.7)
        tasks_header = QLabel(self.tr("Tasks in this project:"))
        tasks_header.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(tasks_header)
        
        tasks_list = QListWidget()
        tasks_list.setObjectName("projectTasksList")
        
        # Load tasks for this project
        project_tasks = self.task_view_model.get_tasks_for_project(project_id)
        if project_tasks:
            for task in project_tasks:
                item = QListWidgetItem(f"{task.title} ({task.status})")
                item.setData(Qt.ItemDataRole.UserRole, task.id)
                tasks_list.addItem(item)
        else:
            placeholder = QListWidgetItem(self.tr("No tasks in this project"))
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)  # Not selectable
            tasks_list.addItem(placeholder)
        
        # Double-click opens task view
        def open_task_view(item):
            task_id = item.data(Qt.ItemDataRole.UserRole)
            if task_id:
                from app.modules.tasks.views import TaskViewWidget
                task_view = TaskViewWidget(view_model=self.task_view_model, parent=dialog)
                task_view.set_task_id(task_id)
                task_view.show()
        
        tasks_list.itemDoubleClicked.connect(open_task_view)
        layout.addWidget(tasks_list)
        
        # Add Edit button handler
        def open_edit_dialog():
            edit_dialog = ProjectEditDialog(self.project_view_model, dialog)
            edit_dialog.set_project_id(project_id)
            if edit_dialog.exec():
                # Refresh view after edit
                project_view.set_project_id(project_id)
                QMessageBox.information(
                    dialog,
                    self.tr("Success"),
                    self.tr("Project updated successfully!")
                )
        
        # Connect edit button
        project_view._edit_button.clicked.disconnect()
        project_view._edit_button.clicked.connect(open_edit_dialog)
        
        # Connect delete to close dialog
        original_delete = project_view._on_delete_clicked
        def delete_and_close():
            original_delete()
            if not self.project_view_model.load_project(project_id):
                # Project was deleted
                dialog.close()
        
        project_view._delete_button.clicked.disconnect()
        project_view._delete_button.clicked.connect(delete_and_close)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _on_project_created(self, project_id: int, name: str):
        """Handle project created signal."""
        # List will be refreshed by projectsListChanged signal
        pass
    
    def _on_project_updated(self, project_id: int, name: str):
        """Handle project updated signal."""
        # List will be refreshed by projectsListChanged signal
        pass
    
    def _on_project_deleted(self, project_id: int):
        """Handle project deleted signal."""
        # List will be refreshed by projectsListChanged signal
        pass
    
    def _refresh_project_list(self):
        """Refresh the project list widget from ViewModel."""
        from PySide6.QtWidgets import QListWidgetItem
        
        self.project_list.clear()
        projects = self.project_view_model.get_projects_list()
        
        for project in projects:
            item = QListWidgetItem(project['name'])
            item.setData(Qt.ItemDataRole.UserRole, project['id'])
            # Add tooltip with description
            if project['description']:
                item.setToolTip(project['description'])
            self.project_list.addItem(item)
    
    def _toggle_project_panel(self):
        """Navigate to projects view."""
        if hasattr(self, 'nav_sidebar'):
            self.nav_sidebar.set_active_section(NavigationSidebar.PROJECTS)



    async def async_init(self):
        # from app.builtin.github_updater import GithubUpdater
        from app.builtin.gitlab_updater import GitlabUpdater

        updater = GitlabUpdater()
        if os.getenv("DEBUG", "0") == "1":
            # Debug mode
            pass
        else:
            # Production mode
            await self.check_update(updater)

        # Start enrichment workers after updater check
        if hasattr(self, "enrichment_service"):
            await self.enrichment_service.start_workers(num_workers=2)

        # Start extraction workers
        if hasattr(self, "extraction_service"):
            await self.extraction_service.start_workers(num_workers=2)
        """Create enrichment service and set global TagService integration."""
        try:
            self.enrichment_service = EnrichmentService()
            integration = TagEnrichmentIntegration(tag_service=TagService(), enrichment_service=self.enrichment_service)
            TagService.set_global_enrichment_integration(integration)
        except Exception:
            # Non-fatal if enrichment setup fails
            pass

    def _open_api_keys_dialog(self):
        """Open dialog to configure API keys (Google Books, Gemini CLI)."""
        try:
            dialog = ApiKeysDialog(enrichment_service=getattr(self, "enrichment_service", None), parent=self)
            # Connect signal to refresh greeting when settings are saved
            dialog.settingsSaved.connect(self._on_api_settings_saved)
            dialog.exec()
        except Exception:
            QMessageBox.warning(self, self.tr("Warning"), self.tr("Failed to open API Keys dialog"))
    
    def _on_api_settings_saved(self):
        """Handle API settings saved - refresh co-pilot greeting with new capabilities."""
        if not hasattr(self, 'copilot_service') or not hasattr(self, 'copilot_vm'):
            return
        
        try:
            from datetime import datetime
            import uuid
            
            # Update service to use LLM now that API is configured
            from app.modules.ai_copilot.gemini_integration import is_gemini_configured
            self.copilot_service.use_llm = is_gemini_configured()
            
            # Determine time of day
            hour = datetime.now().hour
            if hour < 12:
                time_of_day = "morning"
            elif hour < 17:
                time_of_day = "afternoon"
            else:
                time_of_day = "evening"
            
            # Get task count
            task_count = 0
            if hasattr(self, 'task_view_model'):
                try:
                    task_count = len(self.task_view_model.tasks)
                except:
                    pass
            
            # Generate updated greeting
            if is_gemini_configured():
                # Generate personalized AI greeting
                greeting_msg = self.copilot_service.generate_personalized_greeting(time_of_day)
            else:
                # Fallback if key was deleted
                greeting_msg = self.copilot_service.get_api_key_status_message(time_of_day, task_count)
            
            # Store and display the updated greeting
            msg_id = str(uuid.uuid4())
            self.copilot_service.save_communication_event(
                message_id=msg_id,
                message_text=greeting_msg,
                category="greeting",
                tone_level="gentle"
            )
            
            # Display through ViewModel
            if self.copilot_vm:
                self.copilot_vm.emit_message_ready(greeting_msg, msg_id)
                
        except Exception as e:
            print(f"Warning: Could not refresh greeting: {e}")

    def _initialize_enrichment_system(self):
        """Initialize tag enrichment system (placeholder for future implementation)."""
        # This method is called during startup but enrichment workers
        # are started asynchronously in async_init()
        pass

    def _initialize_extraction_system(self):
        """Create extraction service for file ingestion."""
        try:
            self.extraction_service = ExtractionService()
            # Start workers in the event loop
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.create_task(self.extraction_service.start_workers(num_workers=2))
        except Exception as e:
            print(f"Failed to initialize extraction service: {e}")

    def _open_import_dialog(self):
        """Open the Import Document dialog."""
        try:
            dialog = ImportDialog(extraction_service=getattr(self, "extraction_service", None), parent=self)
            dialog.exec()
        except Exception:
            QMessageBox.warning(self, self.tr("Warning"), self.tr("Failed to open Import dialog"))

    async def check_update(self, updater):
        if not updater.is_enable:
            return
        if not updater.is_updated:
            try:
                await updater.fetch()
                if updater.check_for_update():
                    update_widget = UpdateWidget(self, updater)
                    await update_widget.async_show()
                    if update_widget.need_restart:
                        updater.apply_update()
                        self.close()
            except HTTPError:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("Failed to check for updates"),
                )
            except FileNotFoundError:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("No update files found"),
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("Excepted unknown error: {}").format(str(e)),
                )
        else:
            QMessageBox.information(
                self,
                self.tr("Info"),
                self.tr("Update completed"),
            )

    def _build_placeholder_view(self):
        container = QWidget(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(48, 64, 48, 64)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel(self.tr("Sageframe"))
        title.setObjectName("heroTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel(self.tr("Empathetic co-pilot for focus and calm."))
        subtitle.setObjectName("heroSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)

        status = QLabel(self.tr("Theming baseline loaded. Core views coming next."))
        status.setObjectName("heroStatus")
        status.setAlignment(Qt.AlignCenter)
        status.setWordWrap(True)

        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(status)
        layout.addStretch(2)

        container.setLayout(layout)
        self.setCentralWidget(container)

    def closeEvent(self, event):
        """Handle window close - cleanup resources explicitly.
        
        Ensures ProjectViewModel and TaskViewModel are properly closed before window destruction,
        which closes database connections and prevents resource leaks.
        """
        try:
            if hasattr(self, 'project_view_model') and self.project_view_model:
                self.project_view_model.close()
                super().closeEvent(event)
        except Exception:
            pass
        
        try:
            if hasattr(self, 'task_view_model') and self.task_view_model:
                self.task_view_model.close()
                super().closeEvent(event)
        except Exception:
            pass
    
    # Task Management Handlers (Story 2.2)
    
    def _open_create_task_dialog(self):
        """Open create task dialog (AC#1)."""
        # Get list of projects for dropdown
        projects = self.project_view_model.get_projects_list()
        
        dialog = TaskCreateDialog(view_model=self.task_view_model, parent=self, projects=projects)
        dialog.exec()
    
    def _on_task_double_clicked(self, item):
        """Handle task list item double-click (AC#2)."""
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            # Open task view widget
            view_widget = TaskViewWidget(view_model=self.task_view_model, parent=self)
            view_widget.set_task_id(task_id)
            view_widget.show()
    
    def _on_task_created(self, task_id: int, title: str):
        """Handle task created signal (AC#1)."""
        self._show_toast(f"✅ Task '{title}' created successfully", "#4CAF50", 3000)
    
    def _on_task_updated(self, task_id: int, title: str):
        """Handle task updated signal (AC#3)."""
        self._show_toast(f"💾 Task '{title}' updated successfully", "#4CAF50", 3000)
        self._check_level_up()

    def _on_task_clicked(self, item):
        """Open task details for editing on single click."""
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if not task_id:
            return
        view_widget = TaskViewWidget(view_model=self.task_view_model, parent=self)
        view_widget.set_task_id(task_id)
        view_widget.show()

    def _mark_task_done(self, task_id: int):
        """Mark a task as done and refresh views."""
        try:
            if self.task_view_model.update_task_status(task_id, TaskStatus.DONE):
                self._log_user_action(f"Task {task_id} marked as done via inline action")
                self.task_view_model.refresh_tasks()
                self._refresh_task_list()
                self._refresh_gantt_chart()
                self._refresh_progress()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Failed to update task: {e}"))

    def _on_task_deleted(self, task_id: int):
        """Handle task deleted signal (AC#4)."""
        QMessageBox.information(self, self.tr("Task Deleted"), self.tr("Task deleted successfully."))
    
    def _refresh_task_list(self):
        """Refresh the task list UI (AC#1-6)."""
        # Delegate to the list view's refresh method
        if hasattr(self, 'task_list_view'):
            self.task_list_view.refresh()

    def _refresh_progress(self, *args, **kwargs):
        """Refresh progress panel and cache level for notifications."""
        if hasattr(self, "progress_view_model"):
            stats = self.progress_view_model.refresh()
            if stats:
                self._last_known_level = stats.get("current_level", self._last_known_level)

    def _log_user_action(self, message: str):
        """Append a simple log entry for user actions."""
        try:
            log_dir = os.path.join(os.path.expanduser("~"), ".sageframe")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "user_logs.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.utcnow().isoformat()}] {message}\n")
        except Exception:
            pass

    def _task_item_size_hint(self) -> QSize:
        return QSize(0, 48)

    def _build_task_row_widget(self, task_dict):
        """Build a row widget with inline Done button."""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        title = task_dict.get('title', '')
        status = task_dict.get('status', '')
        label = QLabel(f"{title} ({status})")
        label.setObjectName("taskRowLabel")
        layout.addWidget(label, 1)

        done_btn = QPushButton("✓")
        done_btn.setObjectName("taskRowDoneButton")
        done_btn.setFixedSize(28, 28)
        done_btn.setToolTip(self.tr("Mark as done"))
        done_btn.setStyleSheet(
            "QPushButton { border-radius: 14px; background: #3b82f6; color: white; font-weight: bold; } "
            "QPushButton:hover { background: #2563eb; } "
            "QPushButton:pressed { background: #1d4ed8; }"
        )
        done_btn.clicked.connect(lambda _=None, tid=task_dict.get('id'): self._mark_task_done(tid))
        layout.addWidget(done_btn, 0, alignment=Qt.AlignRight)

        return row

    def _check_level_up(self):
        """Check for level-up and notify the user."""
        if not hasattr(self, "progress_view_model"):
            return
        stats = self.progress_view_model.refresh()
        self._last_known_level = stats.get("current_level", self._last_known_level)

    def _on_level_up(self, level: int):
        """Handle level-up events from the progress view model."""
        if hasattr(self, "progress_widget"):
            self.progress_widget.show_level_up(level)
        # Lightweight notification in the status bar
        if self.statusBar():
            self.statusBar().showMessage(self.tr(f"Level up! Reached level {level}."), 5000)

    def _toggle_gantt_panel(self):
        """Switch to Gantt view."""
        if hasattr(self, 'task_view_container'):
            self.task_view_container.view_switcher.setCurrentIndex(self.task_view_container.GANTT_VIEW)
            if hasattr(self, 'nav_sidebar'):
                self.nav_sidebar.set_active_section(NavigationSidebar.TASKS)

    def _refresh_gantt_chart(self):
        """Refresh Gantt chart data from the view model."""
        if hasattr(self, "gantt_chart"):
            self.gantt_chart.refresh()

    def _on_gantt_data_changed(self):
        """Reload task data after Gantt interactions persist changes."""
        if hasattr(self, "task_view_model"):
            self.task_view_model.refresh_tasks()
    
    def _on_task_filter_applied(self, tag_filter):
        """Apply tag filter to task list."""
        if not hasattr(self, "task_view_model"):
            return
        
        from app.modules.tag_management.services import TagService
        from app.modules.tasks.models import Task
        
        # Get filtered tasks
        tag_service = TagService()
        try:
            filtered_tasks = tag_service.filter_items(tag_filter, Task, "task")
            # Update task list with filtered results
            self.task_list.clear()
            for task in filtered_tasks:
                from PySide6.QtWidgets import QListWidgetItem
                task_dict = {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                }
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, task_dict["id"])
                item.setSizeHint(self._task_item_size_hint())
                self.task_list.addItem(item)
                self.task_list.setItemWidget(item, self._build_task_row_widget(task_dict))
        finally:
            tag_service.close()
    
    def _on_quick_add_task(self):
        """Handle quick add task from dashboard."""
        from app.ui.dialogs.quick_add_dialogs import QuickAddTaskDialog
        from datetime import datetime
        
        dialog = QuickAddTaskDialog(self)
        if dialog.exec():
            title = dialog.title_input.text()
            priority = dialog.priority_combo.currentText()
            # Convert QDate to datetime
            qdate = dialog.date_input.date()
            due_date = datetime(qdate.year(), qdate.month(), qdate.day())
            
            # Create task via view model
            try:
                from app.modules.tasks.view_models import TaskViewModel
                task_vm = TaskViewModel()
                task_vm.create_task(
                    title=title,
                    priority=priority.lower(),
                    status="todo",
                    due_date=due_date
                )
                # Refresh task list view to show new task
                if hasattr(self, 'task_list_view'):
                    self.task_list_view.refresh()
                # Refresh gantt view if visible
                if hasattr(self, 'gantt_chart'):
                    self.gantt_chart.refresh()
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", f"Task '{title}' created!")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Error", f"Failed to create task: {e}")
    
    def _on_quick_add_note(self):
        """Handle quick add note from dashboard."""
        from app.ui.dialogs.quick_add_dialogs import QuickAddNoteDialog
        from app.modules.notes.view_models import NotesViewModel
        
        dialog = QuickAddNoteDialog(self)
        if dialog.exec():
            title = dialog.title_input.text()
            content = dialog.content_input.toPlainText()
            
            # Create note via view model
            try:
                notes_vm = NotesViewModel()
                note_id = notes_vm.create_note(
                    title=title,
                    content=content,
                    color="default"
                )
                if note_id:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.information(self, "Success", f"Note created successfully!")
                else:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Warning", "Failed to create note")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to create note: {e}")
    
    def _on_quick_add_import(self):
        """Handle quick add import document from dashboard."""
        from app.modules.file_ingestion.views import ImportDialog
        dialog = ImportDialog(self)
        dialog.exec()
    def _on_task_filter_cleared(self):
        """Clear task filter and show all tasks."""
        self._refresh_task_list()



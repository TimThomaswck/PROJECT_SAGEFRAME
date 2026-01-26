import os

from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QVBoxLayout, QWidget, QHBoxLayout, QDockWidget, QMenu, QToolBar, QPushButton, QListWidget
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
from app.ui.kanban.kanban_board import KanbanBoardWidget
from app.core.shortcut_manager import ShortcutManager
from app.core.undo_manager import UndoManager
from app.ui.shortcut_help_dialog import ShortcutHelpDialog
from app.utils.shortcut_definitions import get_default_shortcuts


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("Sageframe"))
        self.setWindowIcon(QIcon(":/logo.png"))

        self.setMinimumSize(960, 640)
        
        # Initialize undo/redo manager
        self.undo_manager = UndoManager(self)
        
        # Initialize project management system
        self._initialize_project_system()
        
        # Initialize task management system
        self._initialize_task_system()
        
        # Initialize suggestion system
        self._initialize_suggestion_system()
    
    def _initialize_project_system(self):
        """Initialize the project management system with view model and UI."""
        from PySide6.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QSplitter
        
        # Create view model for projects with undo support
        self.project_view_model = ProjectViewModel(parent=self, undo_manager=self.undo_manager)
        
        # Create project list dock widget
        project_list_widget = QWidget()
        project_layout = QVBoxLayout(project_list_widget)
        project_layout.setContentsMargins(8, 8, 8, 8)
        
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
        
        # Create dock for project list
        project_dock = QDockWidget("Projects", self)
        project_dock.setObjectName("projectDock")
        project_dock.setWidget(project_list_widget)
        project_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, project_dock)
        self.project_dock = project_dock
        
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
        # Initialize keyboard shortcuts and menus
        self._initialize_shortcuts()
        self._create_menus_and_toolbars()
        
        self._build_placeholder_view()
        self._add_mood_checkin_button()

    def _initialize_task_system(self):
        """Initialize the task management system with view model and UI."""
        # Create view model for tasks with undo support
        self.task_view_model = TaskViewModel(parent=self, undo_manager=self.undo_manager)

        # Create task list dock widget
        task_list_widget = QWidget()
        task_layout = QVBoxLayout(task_list_widget)
        task_layout.setContentsMargins(8, 8, 8, 8)

        # Add "New Task" button
        new_task_btn = QPushButton("+ New Task")
        new_task_btn.setObjectName("newTaskButton")
        new_task_btn.clicked.connect(self._open_create_task_dialog)
        task_layout.addWidget(new_task_btn)

        # Add task list
        self.task_list = QListWidget()
        self.task_list.setObjectName("taskList")
        self.task_list.itemDoubleClicked.connect(self._on_task_double_clicked)
        task_layout.addWidget(self.task_list)

        # Create dock for task list
        task_dock = QDockWidget("Tasks", self)
        task_dock.setObjectName("taskDock")
        task_dock.setWidget(task_list_widget)
        task_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, task_dock)
        self.task_dock = task_dock

        # Create Kanban board dock
        self.kanban_board = KanbanBoardWidget(self.task_view_model, parent=self)
        kanban_dock = QDockWidget("Kanban", self)
        kanban_dock.setObjectName("kanbanDock")
        kanban_dock.setWidget(self.kanban_board)
        kanban_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, kanban_dock)
        self.kanban_dock = kanban_dock

        # Connect ViewModel signals
        self.task_view_model.taskCreated.connect(self._on_task_created)
        self.task_view_model.taskUpdated.connect(self._on_task_updated)
        self.task_view_model.taskDeleted.connect(self._on_task_deleted)
        self.task_view_model.tasksListChanged.connect(self._refresh_task_list)
        self.task_view_model.validationError.connect(
            lambda msg: QMessageBox.warning(self, self.tr("Validation Error"), msg)
        )
        self.task_view_model.operationError.connect(
            lambda msg: QMessageBox.critical(self, self.tr("Error"), msg)
        )

        # Load initial tasks
        self.task_view_model.refresh_tasks()
    
    def _initialize_suggestion_system(self):
        """Initialize the suggestion system with integration layer."""
        # Create view model for suggestions
        self.suggestion_view_model = SuggestionViewModel()
        
        # Create suggestion panel
        self.suggestion_panel = SuggestionPanel(self.suggestion_view_model, parent=self)
        
        # Create dock widget for suggestion panel
        dock = QDockWidget("AI Suggestions", self)
        dock.setObjectName("suggestionDock")
        dock.setWidget(self.suggestion_panel)
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        # Keep a reference for toggling via shortcuts
        self.suggestion_dock = dock
        
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
        
        # Create toolbar
        toolbar = self.addToolBar(self.tr("Edit"))
        toolbar.setObjectName("EditToolBar")
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        toolbar.addAction(new_project_action)
        toolbar.addAction(new_task_action)
    
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
        """Handle mood check-in completion and trigger suggestions.
        
        Args:
            dialog: The MoodCheckInDialog instance
        """
        if hasattr(dialog, 'view_model'):
            mood = dialog.view_model.moodLevel
            energy = dialog.view_model.energyLevel
            
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

    def _open_shortcut_help(self):
        """Open the keyboard shortcuts help dialog."""
        grouped = self.shortcut_manager.get_shortcuts_by_category()
        dialog = ShortcutHelpDialog(grouped, self)
        dialog.exec()

    def _toggle_suggestion_panel(self):
        """Show or hide the AI suggestion dock panel."""
        if hasattr(self, "suggestion_dock"):
            is_visible = self.suggestion_dock.isVisible()
            self.suggestion_dock.setVisible(not is_visible)

    def _toggle_kanban_panel(self):
        """Show or hide the Kanban dock panel."""
        if hasattr(self, "kanban_dock"):
            is_visible = self.kanban_dock.isVisible()
            self.kanban_dock.setVisible(not is_visible)

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
        """Show or hide the project dock panel."""
        if hasattr(self, "project_dock"):
            is_visible = self.project_dock.isVisible()
            self.project_dock.setVisible(not is_visible)



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
        QMessageBox.information(self, self.tr("Task Created"), self.tr(f"Task '{title}' created successfully."))
    
    def _on_task_updated(self, task_id: int, title: str):
        """Handle task updated signal (AC#3)."""
        QMessageBox.information(self, self.tr("Task Updated"), self.tr(f"Task '{title}' updated successfully."))
    
    def _on_task_deleted(self, task_id: int):
        """Handle task deleted signal (AC#4)."""
        QMessageBox.information(self, self.tr("Task Deleted"), self.tr("Task deleted successfully."))
    
    def _refresh_task_list(self):
        """Refresh the task list UI (AC#1-6)."""
        self.task_list.clear()
        
        tasks = self.task_view_model.get_tasks_list()
        for task_dict in tasks:
            from PySide6.QtWidgets import QListWidgetItem
            
            # Create list item
            item_text = f"{task_dict['title']} ({task_dict['status']})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, task_dict['id'])
            
            self.task_list.addItem(item)
    
    def _toggle_task_panel(self):
        """Toggle visibility of task panel."""
        if self.task_dock.isVisible():
            self.task_dock.hide()
        else:
            self.task_dock.show()
       



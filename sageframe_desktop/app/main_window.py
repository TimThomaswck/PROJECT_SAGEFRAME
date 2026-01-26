import os

from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QVBoxLayout, QWidget, QHBoxLayout, QDockWidget, QMenu, QToolBar
from httpx import HTTPError

import app.resources.resource  # type: ignore
from app.builtin.update_widget import UpdateWidget
from app.modules.suggestions.views import SuggestionPanel
from app.modules.suggestions.view_models import SuggestionViewModel
from app.modules.suggestions.integration import MoodSuggestionIntegration
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
        
        # Initialize suggestion system
        self._initialize_suggestion_system()
        # Initialize keyboard shortcuts and menus
        self._initialize_shortcuts()
        self._create_menus_and_toolbars()
        
        self._build_placeholder_view()
        self._add_mood_checkin_button()
    
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
        
        # Create toolbar
        toolbar = self.addToolBar(self.tr("Edit"))
        toolbar.setObjectName("EditToolBar")
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
    
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

    def _refresh_suggestions(self):
        """Regenerate suggestions using the latest known mood context."""
        # If we have known mood/energy, trigger a refresh via view model.
        self.suggestion_view_model.generate_suggestions(
            mood=getattr(self, "_last_mood", "neutral"),
            energy_level=getattr(self, "_last_energy", "medium"),
            available_tasks=[],
        )



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



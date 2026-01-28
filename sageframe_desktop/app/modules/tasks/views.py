"""UI views for task management.

This module implements PySide6 dialogs and widgets for task CRUD operations.
Follows Atomic Design principles and MVVM pattern (same as projects views).
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QMessageBox, QWidget, QListWidget,
    QListWidgetItem, QComboBox, QDateTimeEdit, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, Slot, QDateTime
from PySide6.QtGui import QIcon

from app.modules.tasks.view_models import TaskViewModel


class TaskCreateDialog(QDialog):
    """Dialog for creating a new task.
    
    Implements Atomic Design organism: complete dialog for task creation.
    Uses MVVM pattern with TaskViewModel.
    """
    
    def __init__(
        self,
        view_model: TaskViewModel,
        parent: Optional[QWidget] = None,
        projects: Optional[List[Dict[str, Any]]] = None,
        task_id: Optional[int] = None
    ):
        """Initialize create task dialog.
        
        Args:
            view_model: TaskViewModel instance for business logic
            parent: Parent widget
            projects: Optional list of projects for dropdown
        """
        super().__init__(parent)
        self._view_model = view_model
        self._projects = projects or []
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle(self.tr("Create New Task"))
        self.setAccessibleName(self.tr("Create Task Dialog"))
        self.setAccessibleDescription(self.tr("Dialog for creating a new task with title, description, due date, and project association"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Task title field (atom: label + input)
        title_label = QLabel(self.tr("Task Title:"))
        title_label.setObjectName("taskTitleLabel")
        self._title_input = QLineEdit()
        self._title_input.setObjectName("taskTitleInput")
        self._title_input.setAccessibleName(self.tr("Task Title Input"))
        self._title_input.setAccessibleDescription(self.tr("Text field for entering the task title (required, 1-255 characters)"))
        self._title_input.setPlaceholderText(self.tr("Enter task title..."))
        self._title_input.setMaxLength(255)
        
        # Task description field (atom: label + textarea)
        desc_label = QLabel(self.tr("Description (Optional):"))
        desc_label.setObjectName("taskDescriptionLabel")
        self._description_input = QTextEdit()
        self._description_input.setObjectName("taskDescriptionInput")
        self._description_input.setAccessibleName(self.tr("Task Description Input"))
        self._description_input.setAccessibleDescription(self.tr("Text area for entering an optional task description"))
        self._description_input.setPlaceholderText(self.tr("Enter task description..."))
        self._description_input.setMinimumHeight(100)
        
        # Date mode toggle
        from PySide6.QtWidgets import QCheckBox
        self._use_timeline_checkbox = QCheckBox(self.tr("Use Timeline Dates (for Gantt Chart)"))
        self._use_timeline_checkbox.setObjectName("useTimelineCheckbox")
        self._use_timeline_checkbox.setChecked(False)
        
        # Due date field (default mode)
        self._due_date_label = QLabel(self.tr("Due Date (Optional):"))
        self._due_date_label.setObjectName("taskDueDateLabel")
        self._due_date_input = QDateTimeEdit()
        self._due_date_input.setObjectName("taskDueDateInput")
        self._due_date_input.setAccessibleName(self.tr("Task Due Date Input"))
        self._due_date_input.setAccessibleDescription(self.tr("Date and time picker for optional due date"))
        self._due_date_input.setCalendarPopup(True)
        self._due_date_input.setDateTime(QDateTime.currentDateTime())
        self._due_date_input.setEnabled(False)
        self._due_date_checkbox = QPushButton(self.tr("Set Due Date"))
        self._due_date_checkbox.setObjectName("clearDueDateButton")
        self._has_due_date = False
        
        self._due_date_layout = QHBoxLayout()
        self._due_date_layout.addWidget(self._due_date_input)
        self._due_date_layout.addWidget(self._due_date_checkbox)
        
        # Start date field (timeline mode)
        self._start_date_label = QLabel(self.tr("Start Date:"))
        self._start_date_label.setObjectName("taskStartDateLabel")
        self._start_date_input = QDateTimeEdit()
        self._start_date_input.setObjectName("taskStartDateInput")
        self._start_date_input.setAccessibleName(self.tr("Task Start Date Input"))
        self._start_date_input.setAccessibleDescription(self.tr("Date and time picker for start date"))
        self._start_date_input.setCalendarPopup(True)
        self._start_date_input.setDateTime(QDateTime.currentDateTime())
        
        # End date field (timeline mode)
        self._end_date_label = QLabel(self.tr("End Date:"))
        self._end_date_label.setObjectName("taskEndDateLabel")
        self._end_date_input = QDateTimeEdit()
        self._end_date_input.setObjectName("taskEndDateInput")
        self._end_date_input.setAccessibleName(self.tr("Task End Date Input"))
        self._end_date_input.setAccessibleDescription(self.tr("Date and time picker for end date"))
        self._end_date_input.setCalendarPopup(True)
        self._end_date_input.setDateTime(QDateTime.currentDateTime().addDays(1))
        
        # Hide timeline fields by default
        self._start_date_label.setVisible(False)
        self._start_date_input.setVisible(False)
        self._end_date_label.setVisible(False)
        self._end_date_input.setVisible(False)
        
        # Status dropdown
        status_label = QLabel(self.tr("Status:"))
        status_label.setObjectName("taskStatusLabel")
        self._status_combo = QComboBox()
        self._status_combo.setObjectName("taskStatusCombo")
        self._status_combo.setAccessibleName(self.tr("Task Status Dropdown"))
        self._status_combo.setAccessibleDescription(self.tr("Dropdown to select task status"))
        self._status_combo.addItems(["todo", "in_progress", "done", "blocked"])
        
        # Project dropdown
        project_label = QLabel(self.tr("Project (Optional):"))
        project_label.setObjectName("taskProjectLabel")
        self._project_combo = QComboBox()
        self._project_combo.setObjectName("taskProjectCombo")
        self._project_combo.setAccessibleName(self.tr("Project Dropdown"))
        self._project_combo.setAccessibleDescription(self.tr("Dropdown to associate task with a project (optional)"))
        self._project_combo.addItem(self.tr("No Project (Standalone)"), None)
        for proj in self._projects:
            self._project_combo.addItem(proj.get('name', ''), proj.get('id'))
        
        # Buttons (atoms)
        button_layout = QHBoxLayout()
        self._create_button = QPushButton(self.tr("Create"))
        self._create_button.setObjectName("taskCreateButton")
        self._create_button.setAccessibleName(self.tr("Create Task Button"))
        self._create_button.setAccessibleDescription(self.tr("Button to save and create the new task"))
        self._cancel_button = QPushButton(self.tr("Cancel"))
        self._cancel_button.setObjectName("taskCancelButton")
        self._cancel_button.setAccessibleName(self.tr("Cancel Button"))
        self._cancel_button.setAccessibleDescription(self.tr("Button to cancel task creation and close the dialog"))
        
        button_layout.addStretch()
        button_layout.addWidget(self._create_button)
        button_layout.addWidget(self._cancel_button)
        
        # Assemble layout (molecule: form)
        layout.addWidget(title_label)
        layout.addWidget(self._title_input)
        layout.addWidget(desc_label)
        layout.addWidget(self._description_input)
        layout.addWidget(self._use_timeline_checkbox)
        layout.addWidget(self._due_date_label)
        layout.addLayout(self._due_date_layout)
        layout.addWidget(self._start_date_label)
        layout.addWidget(self._start_date_input)
        layout.addWidget(self._end_date_label)
        layout.addWidget(self._end_date_input)
        layout.addWidget(status_label)
        layout.addWidget(self._status_combo)
        layout.addWidget(project_label)
        layout.addWidget(self._project_combo)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self._title_input.setFocus(Qt.TabFocusReason)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self._create_button.clicked.connect(self._on_create_clicked)
        self._cancel_button.clicked.connect(self.reject)
        self._due_date_checkbox.clicked.connect(self._toggle_due_date)
        self._use_timeline_checkbox.stateChanged.connect(self._toggle_timeline_mode)
        
        # Connect ViewModel signals
        self._view_model.validationError.connect(self._on_validation_error)
        self._view_model.operationError.connect(self._on_operation_error)
        self._view_model.taskCreated.connect(self._on_task_created)
    
    def _toggle_due_date(self):
        """Toggle due date enabled state."""
        self._has_due_date = not self._has_due_date
        self._due_date_input.setEnabled(self._has_due_date)
        self._due_date_checkbox.setText(
            self.tr("Clear Due Date") if self._has_due_date else self.tr("Set Due Date")
        )
    
    def _toggle_timeline_mode(self, state):
        """Toggle between due date mode and timeline mode."""
        use_timeline = bool(state)
        
        # Show/hide due date fields
        self._due_date_label.setVisible(not use_timeline)
        self._due_date_input.setVisible(not use_timeline)
        self._due_date_checkbox.setVisible(not use_timeline)
        
        # Show/hide timeline fields
        self._start_date_label.setVisible(use_timeline)
        self._start_date_input.setVisible(use_timeline)
        self._end_date_label.setVisible(use_timeline)
        self._end_date_input.setVisible(use_timeline)
    
    @Slot()
    def _on_create_clicked(self):
        """Handle create button click."""
        title = self._title_input.text().strip()
        description = self._description_input.toPlainText().strip()
        status = self._status_combo.currentText()
        
        due_date = None
        start_date = None
        end_date = None
        
        # Use timeline mode or due date mode
        if self._use_timeline_checkbox.isChecked():
            # Timeline mode: use start and end dates
            start_date = self._start_date_input.dateTime().toPython()
            end_date = self._end_date_input.dateTime().toPython()
        else:
            # Due date mode: use due date if enabled
            if self._has_due_date:
                due_date = self._due_date_input.dateTime().toPython()
        
        # Get project ID
        project_id = self._project_combo.currentData()
        
        # Create via ViewModel
        if self._view_model.create_task(
            title=title,
            description=description or None,
            due_date=due_date,
            status=status,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date
        ):
            self.accept()
    
    @Slot(str)
    def _on_validation_error(self, message: str):
        """Handle validation error signal."""
        QMessageBox.warning(self, self.tr("Validation Error"), message)
    
    @Slot(str)
    def _on_operation_error(self, message: str):
        """Handle operation error signal."""
        QMessageBox.critical(self, self.tr("Operation Error"), message)
    
    @Slot(int, str)
    def _on_task_created(self, task_id: int, title: str):
        """Handle task created signal."""
        pass


class TaskViewWidget(QWidget):
    """Widget for viewing task details.
    
    Implements Atomic Design organism: complete view for task information.
    """
    
    def __init__(
        self,
        view_model: TaskViewModel,
        task_id: Optional[int] = None,
        parent: Optional[QWidget] = None,
        project_name: Optional[str] = None
    ):
        """Initialize task view widget.
        
        Args:
            view_model: TaskViewModel instance
            task_id: Optional initial task id to load
            parent: Parent widget
            project_name: Optional project name for display
        """
        super().__init__(parent)
        self._view_model = view_model
        self._current_task_id: Optional[int] = None
        self._current_project_name: Optional[str] = project_name
        self._init_ui()
        self._connect_signals()
        if task_id is not None:
            self.set_task_id(task_id, project_name=project_name)
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(self.tr("Task Details"))
        title_label.setObjectName("taskViewTitle")
        title_label.setAccessibleName(self.tr("Task Details Title"))
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Title display
        name_label = QLabel(self.tr("Title:"))
        name_label.setObjectName("taskTitleLabel")
        self._title_display = QLabel()
        self._title_display.setObjectName("taskTitleDisplay")
        self._title_display.setAccessibleName(self.tr("Task Title Display"))
        self._title_display.setAccessibleDescription(self.tr("Shows the title of the current task"))
        self._title_display.setWordWrap(True)
        # Alias used by UI tests
        self._title_label = self._title_display
        
        # Description display
        desc_label = QLabel(self.tr("Description:"))
        desc_label.setObjectName("taskDescriptionLabel")
        self._description_display = QTextEdit()
        self._description_display.setObjectName("taskDescriptionDisplay")
        self._description_display.setAccessibleName(self.tr("Task Description Display"))
        self._description_display.setAccessibleDescription(self.tr("Shows the description of the current task (read-only)"))
        self._description_display.setReadOnly(True)
        self._description_display.setMinimumHeight(80)
        
        # Status display
        status_label = QLabel(self.tr("Status:"))
        status_label.setObjectName("taskStatusLabel")
        self._status_display = QLabel()
        self._status_display.setObjectName("taskStatusDisplay")
        self._status_display.setAccessibleName(self.tr("Task Status Display"))
        
        # Due date display
        due_label = QLabel(self.tr("Due Date:"))
        due_label.setObjectName("taskDueDateLabel")
        self._due_date_display = QLabel()
        self._due_date_display.setObjectName("taskDueDateDisplay")
        self._due_date_display.setAccessibleName(self.tr("Task Due Date Display"))
        
        # Project display
        project_label = QLabel(self.tr("Project:"))
        project_label.setObjectName("taskProjectLabel")
        self._project_label = project_label
        self._project_display = QLabel()
        self._project_display.setObjectName("taskProjectDisplay")
        self._project_display.setAccessibleName(self.tr("Task Project Display"))
        
        # Buttons
        button_layout = QHBoxLayout()
        self._edit_button = QPushButton(self.tr("Edit"))
        self._edit_button.setObjectName("editTaskButton")
        self._edit_button.setAccessibleName(self.tr("Edit Task Button"))
        self._edit_button.setAccessibleDescription(self.tr("Button to open the edit dialog for this task"))
        self._delete_button = QPushButton(self.tr("Delete"))
        self._delete_button.setObjectName("deleteTaskButton")
        self._delete_button.setAccessibleName(self.tr("Delete Task Button"))
        self._delete_button.setAccessibleDescription(self.tr("Button to delete this task (requires confirmation)"))
        self._close_button = QPushButton(self.tr("Close"))
        self._close_button.setObjectName("closeButton")
        
        button_layout.addStretch()
        button_layout.addWidget(self._edit_button)
        button_layout.addWidget(self._delete_button)
        button_layout.addWidget(self._close_button)
        
        # Assemble
        layout.addWidget(title_label)
        layout.addWidget(name_label)
        layout.addWidget(self._title_display)
        layout.addWidget(desc_label)
        layout.addWidget(self._description_display)
        layout.addWidget(status_label)
        layout.addWidget(self._status_display)
        layout.addWidget(due_label)
        layout.addWidget(self._due_date_display)
        layout.addWidget(project_label)
        layout.addWidget(self._project_display)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self._edit_button.clicked.connect(self._on_edit_clicked)
        self._delete_button.clicked.connect(self._on_delete_clicked)
        self._close_button.clicked.connect(self.hide)
    
    def set_task_id(self, task_id: int, project_name: Optional[str] = None):
        """Set the task to display.
        
        Args:
            task_id: The task ID to display
            project_name: Optional project name to render alongside id
        """
        self._current_task_id = task_id
        if project_name is not None:
            self._current_project_name = project_name
        if self._view_model.load_task(task_id):
            self._update_display()
    
    def _update_display(self):
        """Update UI with current task data from ViewModel."""
        self._title_display.setText(self._view_model.taskTitle)
        self._description_display.setPlainText(self._view_model.taskDescription)
        self._status_display.setText(self._view_model.taskStatus)
        
        # Due date
        due_date = self._view_model.get_task_due_date()
        if due_date:
            self._due_date_display.setText(due_date.strftime("%Y-%m-%d %H:%M"))
        else:
            self._due_date_display.setText(self.tr("No due date"))
        
        # Project
        project_id = self._view_model.taskProjectId
        if self._current_project_name:
            self._project_display.setText(self._current_project_name)
        elif project_id:
            self._project_display.setText(f"Project #{project_id}")
        else:
            self._project_display.setText(self.tr("Standalone task"))
    
    @Slot()
    def _on_edit_clicked(self):
        """Handle edit button click."""
        if not self._current_task_id:
            return
        dialog = TaskEditDialog(
            view_model=self._view_model,
            parent=self,
            task_id=self._current_task_id
        )
        if dialog.exec():
            self.set_task_id(self._current_task_id, project_name=self._current_project_name)
    
    @Slot()
    def _on_delete_clicked(self):
        """Handle delete button click."""
        if not self._current_task_id:
            return
        
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            self.tr("Confirm Delete"),
            self.tr("Are you sure you want to delete this task?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self._view_model.delete_task(self._current_task_id):
                QMessageBox.information(self, self.tr("Success"), self.tr("Task deleted successfully"))
                self.hide()
            else:
                QMessageBox.warning(self, self.tr("Error"), self.tr("Failed to delete task"))


class TaskEditDialog(QDialog):
    """Dialog for editing an existing task.
    
    Implements Atomic Design organism: complete dialog for task editing.
    """
    
    def __init__(
        self,
        view_model: TaskViewModel,
        parent: Optional[QWidget] = None,
        projects: Optional[List[Dict[str, Any]]] = None,
        task_id: Optional[int] = None
    ):
        """Initialize edit task dialog.
        
        Args:
            view_model: TaskViewModel instance
            parent: Parent widget
            projects: Optional list of projects for dropdown
            task_id: Optional task id to load on init
        """
        super().__init__(parent)
        self._view_model = view_model
        self._projects = projects or []
        self._task_id: Optional[int] = task_id
        self._init_ui()
        self._connect_signals()
        if self._task_id is not None:
            self.set_task_id(self._task_id)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle(self.tr("Edit Task"))
        self.setAccessibleName(self.tr("Edit Task Dialog"))
        self.setAccessibleDescription(self.tr("Dialog for editing an existing task"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Task title field
        title_label = QLabel(self.tr("Task Title:"))
        title_label.setObjectName("taskTitleLabel")
        self._title_input = QLineEdit()
        self._title_input.setObjectName("taskTitleInput")
        self._title_input.setAccessibleName(self.tr("Task Title Input"))
        self._title_input.setAccessibleDescription(self.tr("Text field for editing the task title"))
        self._title_input.setMaxLength(255)
        
        # Task description field
        desc_label = QLabel(self.tr("Description (Optional):"))
        desc_label.setObjectName("taskDescriptionLabel")
        self._description_input = QTextEdit()
        self._description_input.setObjectName("taskDescriptionInput")
        self._description_input.setAccessibleName(self.tr("Task Description Input"))
        self._description_input.setMinimumHeight(100)
        
        # Due date field
        due_date_label = QLabel(self.tr("Due Date (Optional):"))
        self._due_date_input = QDateTimeEdit()
        self._due_date_input.setObjectName("taskDueDateInput")
        self._due_date_input.setCalendarPopup(True)
        self._due_date_checkbox = QPushButton(self.tr("Clear Due Date"))
        self._has_due_date = False
        self._due_date_input.setEnabled(False)
        self._due_date_checkbox.setText(self.tr("Set Due Date"))
        
        due_date_layout = QHBoxLayout()
        due_date_layout.addWidget(self._due_date_input)
        due_date_layout.addWidget(self._due_date_checkbox)
        
        # Status dropdown
        status_label = QLabel(self.tr("Status:"))
        self._status_combo = QComboBox()
        self._status_combo.setObjectName("taskStatusCombo")
        self._status_combo.addItems(["todo", "in_progress", "done", "blocked"])
        
        # Project dropdown
        project_label = QLabel(self.tr("Project (Optional):"))
        self._project_combo = QComboBox()
        self._project_combo.setObjectName("taskProjectCombo")
        self._project_combo.addItem(self.tr("No Project (Standalone)"), None)
        for proj in self._projects:
            self._project_combo.addItem(proj.get('name', ''), proj.get('id'))
        
        # Buttons
        button_layout = QHBoxLayout()
        self._save_button = QPushButton(self.tr("Save"))
        self._save_button.setObjectName("saveTaskButton")
        self._save_button.setAccessibleName(self.tr("Save Task Button"))
        self._cancel_button = QPushButton(self.tr("Cancel"))
        self._cancel_button.setObjectName("cancelButton")
        
        button_layout.addStretch()
        button_layout.addWidget(self._save_button)
        button_layout.addWidget(self._cancel_button)
        
        # Assemble layout
        layout.addWidget(title_label)
        layout.addWidget(self._title_input)
        layout.addWidget(desc_label)
        layout.addWidget(self._description_input)
        layout.addWidget(due_date_label)
        layout.addLayout(due_date_layout)
        layout.addWidget(status_label)
        layout.addWidget(self._status_combo)
        layout.addWidget(project_label)
        layout.addWidget(self._project_combo)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self._save_button.clicked.connect(self._on_save_clicked)
        self._cancel_button.clicked.connect(self.reject)
        self._due_date_checkbox.clicked.connect(self._toggle_due_date)
        
        # Connect ViewModel signals
        self._view_model.validationError.connect(self._on_validation_error)
        self._view_model.operationError.connect(self._on_operation_error)
        self._view_model.taskUpdated.connect(self._on_task_updated)
    
    def _toggle_due_date(self):
        """Toggle due date enabled state."""
        self._has_due_date = not self._has_due_date
        self._due_date_input.setEnabled(self._has_due_date)
        self._due_date_checkbox.setText(
            self.tr("Set Due Date") if not self._has_due_date else self.tr("Clear Due Date")
        )
    
    def set_task_id(self, task_id: int):
        """Set task to edit and load its data.
        
        Args:
            task_id: The task ID to edit
        """
        self._task_id = task_id
        if self._view_model.load_task(task_id):
            self._title_input.setText(self._view_model.taskTitle)
            self._description_input.setPlainText(self._view_model.taskDescription)
            
            # Set status
            status_idx = self._status_combo.findText(self._view_model.taskStatus)
            if status_idx >= 0:
                self._status_combo.setCurrentIndex(status_idx)
            
            # Set due date
            due_date = self._view_model.get_task_due_date()
            if due_date:
                self._has_due_date = True
                self._due_date_input.setEnabled(True)
                self._due_date_input.setDateTime(QDateTime(due_date))
                self._due_date_checkbox.setText(self.tr("Clear Due Date"))
            else:
                self._has_due_date = False
                self._due_date_input.setEnabled(False)
                self._due_date_checkbox.setText(self.tr("Set Due Date"))
            
            # Set project
            project_id = self._view_model.taskProjectId
            for i in range(self._project_combo.count()):
                if self._project_combo.itemData(i) == project_id:
                    self._project_combo.setCurrentIndex(i)
                    break
    
    @Slot()
    def _on_save_clicked(self):
        """Handle save button click."""
        if not self._task_id:
            return
        
        title = self._title_input.text().strip()
        description = self._description_input.toPlainText().strip()
        status = self._status_combo.currentText()
        
        # Get due date if enabled
        due_date = None
        if self._has_due_date:
            due_date = self._due_date_input.dateTime().toPython()
        
        # Get project ID
        project_id = self._project_combo.currentData()
        
        # Update via ViewModel
        if self._view_model.update_task(
            task_id=self._task_id,
            title=title,
            description=description or None,
            due_date=due_date,
            status=status,
            project_id=project_id
        ):
            self.accept()
    
    @Slot(str)
    def _on_validation_error(self, message: str):
        """Handle validation error signal."""
        QMessageBox.warning(self, self.tr("Validation Error"), message)
    
    @Slot(str)
    def _on_operation_error(self, message: str):
        """Handle operation error signal."""
        QMessageBox.critical(self, self.tr("Operation Error"), message)
    
    @Slot(int, str)
    def _on_task_updated(self, task_id: int, title: str):
        """Handle task updated signal."""
        pass

"""UI views for project management.

This module implements PySide6 dialogs and widgets for project CRUD operations.
Follows Atomic Design principles and MVVM pattern.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QMessageBox, QWidget, QListWidget,
    QListWidgetItem, QSplitter
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon

from app.modules.projects.view_models import ProjectViewModel


class ProjectCreateDialog(QDialog):
    """Dialog for creating a new project.
    
    Implements Atomic Design organism: complete dialog for project creation.
    Uses MVVM pattern with ProjectViewModel.
    """
    
    def __init__(self, view_model: ProjectViewModel, parent: Optional[QWidget] = None):
        """Initialize create project dialog.
        
        Args:
            view_model: ProjectViewModel instance for business logic
            parent: Parent widget
        """
        super().__init__(parent)
        self._view_model = view_model
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Create New Project")
        self.setAccessibleName("Create Project Dialog")
        self.setAccessibleDescription("Dialog for creating a new project with name and optional description")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout()
        
        # Project name field (atom: label + input)
        name_label = QLabel("Project Name:")
        name_label.setObjectName("projectNameLabel")
        self._name_input = QLineEdit()
        self._name_input.setObjectName("projectNameInput")
        self._name_input.setAccessibleName("Project Name Input")
        self._name_input.setAccessibleDescription("Text field for entering the project name (required, 1-255 characters)")
        self._name_input.setPlaceholderText("Enter project name...")
        self._name_input.setMaxLength(255)
        
        # Project description field (atom: label + textarea)
        desc_label = QLabel("Description (Optional):")
        desc_label.setObjectName("projectDescriptionLabel")
        self._description_input = QTextEdit()
        self._description_input.setObjectName("projectDescriptionInput")
        self._description_input.setAccessibleName("Project Description Input")
        self._description_input.setAccessibleDescription("Text area for entering an optional project description (max 5000 characters)")
        self._description_input.setPlaceholderText("Enter project description...")
        self._description_input.setMinimumHeight(150)
        
        # Buttons (atoms)
        button_layout = QHBoxLayout()
        self._create_button = QPushButton("Create")
        self._create_button.setObjectName("createProjectButton")
        self._create_button.setAccessibleName("Create Project Button")
        self._create_button.setAccessibleDescription("Button to save and create the new project")
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setObjectName("cancelButton")
        self._cancel_button.setAccessibleName("Cancel Button")
        self._cancel_button.setAccessibleDescription("Button to cancel project creation and close the dialog")
        
        button_layout.addStretch()
        button_layout.addWidget(self._create_button)
        button_layout.addWidget(self._cancel_button)
        
        # Assemble layout (molecule: form)
        layout.addWidget(name_label)
        layout.addWidget(self._name_input)
        layout.addWidget(desc_label)
        layout.addWidget(self._description_input)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self._create_button.clicked.connect(self._on_create_clicked)
        self._cancel_button.clicked.connect(self.reject)
        
        # Connect ViewModel signals
        self._view_model.validationError.connect(self._on_validation_error)
        self._view_model.operationError.connect(self._on_operation_error)
        self._view_model.projectCreated.connect(self._on_project_created)
    
    @Slot()
    def _on_create_clicked(self):
        """Handle create button click."""
        name = self._name_input.text().strip()
        description = self._description_input.toPlainText().strip()
        
        # Create via ViewModel
        if self._view_model.create_project(name, description or None):
            self.accept()
    
    @Slot(str)
    def _on_validation_error(self, message: str):
        """Handle validation error signal."""
        QMessageBox.warning(self, "Validation Error", message)
    
    @Slot(str)
    def _on_operation_error(self, message: str):
        """Handle operation error signal."""
        QMessageBox.critical(self, "Operation Error", message)
    
    @Slot(int, str)
    def _on_project_created(self, project_id: int, name: str):
        """Handle project created signal."""
        # Dialog will close after accept() is called
        pass


class ProjectViewWidget(QWidget):
    """Widget for viewing project details.
    
    Implements Atomic Design organism: complete view for project information.
    """
    
    def __init__(self, view_model: ProjectViewModel, parent: Optional[QWidget] = None):
        """Initialize project view widget.
        
        Args:
            view_model: ProjectViewModel instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._view_model = view_model
        self._current_project_id: Optional[int] = None
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Project Details")
        title_label.setObjectName("projectViewTitle")
        title_label.setAccessibleName("Project Details Title")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Name display
        name_label = QLabel("Name:")
        name_label.setObjectName("projectNameLabel")
        self._name_display = QLabel()
        self._name_display.setObjectName("projectNameDisplay")
        self._name_display.setAccessibleName("Project Name Display")
        self._name_display.setAccessibleDescription("Shows the name of the current project")
        self._name_display.setWordWrap(True)
        
        # Description display
        desc_label = QLabel("Description:")
        desc_label.setObjectName("projectDescriptionLabel")
        self._description_display = QTextEdit()
        self._description_display.setObjectName("projectDescriptionDisplay")
        self._description_display.setAccessibleName("Project Description Display")
        self._description_display.setAccessibleDescription("Shows the description of the current project (read-only)")
        self._description_display.setReadOnly(True)
        self._description_display.setMinimumHeight(100)
        
        # Buttons
        button_layout = QHBoxLayout()
        self._edit_button = QPushButton("Edit")
        self._edit_button.setObjectName("editProjectButton")
        self._edit_button.setAccessibleName("Edit Project Button")
        self._edit_button.setAccessibleDescription("Button to open the edit dialog for this project")
        self._delete_button = QPushButton("Delete")
        self._delete_button.setObjectName("deleteProjectButton")
        self._delete_button.setAccessibleName("Delete Project Button")
        self._delete_button.setAccessibleDescription("Button to delete this project (requires confirmation)")
        self._close_button = QPushButton("Close")
        self._close_button.setObjectName("closeButton")
        
        button_layout.addStretch()
        button_layout.addWidget(self._edit_button)
        button_layout.addWidget(self._delete_button)
        button_layout.addWidget(self._close_button)
        
        # Assemble
        layout.addWidget(title_label)
        layout.addWidget(name_label)
        layout.addWidget(self._name_display)
        layout.addWidget(desc_label)
        layout.addWidget(self._description_display)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self._edit_button.clicked.connect(self._on_edit_clicked)
        self._delete_button.clicked.connect(self._on_delete_clicked)
        self._close_button.clicked.connect(self.hide)
    
    def set_project_id(self, project_id: int):
        """Set the project to display.
        
        Args:
            project_id: The project ID to display
        """
        self._current_project_id = project_id
        if self._view_model.load_project(project_id):
            self._update_display()
    
    def _update_display(self):
        """Update UI with current project data from ViewModel."""
        self._name_display.setText(self._view_model.projectName)
        self._description_display.setPlainText(self._view_model.projectDescription)
    
    @Slot()
    def _on_edit_clicked(self):
        """Handle edit button click."""
        if self._current_project_id:
            # Emit signal to open edit dialog (will be connected by main window)
            # For now, just show a message
            QMessageBox.information(self, "Edit Project", "Edit dialog will open here")
    
    @Slot()
    def _on_delete_clicked(self):
        """Handle delete button click."""
        if not self._current_project_id:
            return
        
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this project?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self._view_model.delete_project(self._current_project_id):
                QMessageBox.information(self, "Success", "Project deleted successfully")
                self.hide()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete project")


class ProjectEditDialog(QDialog):
    """Dialog for editing an existing project.
    
    Implements Atomic Design organism: complete dialog for project editing.
    """
    
    def __init__(self, view_model: ProjectViewModel, parent: Optional[QWidget] = None):
        """Initialize edit project dialog.
        
        Args:
            view_model: ProjectViewModel instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._view_model = view_model
        self._project_id: Optional[int] = None
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Edit Project")
        self.setAccessibleName("Edit Project Dialog")
        self.setAccessibleDescription("Dialog for editing an existing project's name and description")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout()
        
        # Project name field
        name_label = QLabel("Project Name:")
        name_label.setObjectName("projectNameLabel")
        self._name_input = QLineEdit()
        self._name_input.setObjectName("projectNameInput")
        self._name_input.setAccessibleName("Project Name Input")
        self._name_input.setAccessibleDescription("Text field for editing the project name (1-255 characters)")
        self._name_input.setMaxLength(255)
        
        # Project description field
        desc_label = QLabel("Description (Optional):")
        desc_label.setObjectName("projectDescriptionLabel")
        self._description_input = QTextEdit()
        self._description_input.setObjectName("projectDescriptionInput")
        self._description_input.setAccessibleName("Project Description Input")
        self._description_input.setAccessibleDescription("Text area for editing the project description (max 5000 characters)")
        self._description_input.setMinimumHeight(150)
        
        # Buttons
        button_layout = QHBoxLayout()
        self._save_button = QPushButton("Save")
        self._save_button.setObjectName("saveProjectButton")
        self._save_button.setAccessibleName("Save Project Button")
        self._save_button.setAccessibleDescription("Button to save the project changes and close the dialog")
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setObjectName("cancelButton")
        self._cancel_button.setAccessibleName("Cancel Button")
        self._cancel_button.setAccessibleDescription("Button to cancel editing and close the dialog without saving")
        
        button_layout.addStretch()
        button_layout.addWidget(self._save_button)
        button_layout.addWidget(self._cancel_button)
        
        # Assemble layout
        layout.addWidget(name_label)
        layout.addWidget(self._name_input)
        layout.addWidget(desc_label)
        layout.addWidget(self._description_input)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self._save_button.clicked.connect(self._on_save_clicked)
        self._cancel_button.clicked.connect(self.reject)
        
        # Connect ViewModel signals
        self._view_model.validationError.connect(self._on_validation_error)
        self._view_model.operationError.connect(self._on_operation_error)
        self._view_model.projectUpdated.connect(self._on_project_updated)
    
    def set_project_id(self, project_id: int):
        """Set project to edit and load its data.
        
        Args:
            project_id: The project ID to edit
        """
        self._project_id = project_id
        if self._view_model.load_project(project_id):
            self._name_input.setText(self._view_model.projectName)
            self._description_input.setPlainText(self._view_model.projectDescription)
    
    @Slot()
    def _on_save_clicked(self):
        """Handle save button click."""
        if not self._project_id:
            return
        
        name = self._name_input.text().strip()
        description = self._description_input.toPlainText().strip()
        
        # Update via ViewModel
        if self._view_model.update_project(self._project_id, name, description or None):
            self.accept()
    
    @Slot(str)
    def _on_validation_error(self, message: str):
        """Handle validation error signal."""
        QMessageBox.warning(self, "Validation Error", message)
    
    @Slot(str)
    def _on_operation_error(self, message: str):
        """Handle operation error signal."""
        QMessageBox.critical(self, "Operation Error", message)
    
    @Slot(int, str)
    def _on_project_updated(self, project_id: int, name: str):
        """Handle project updated signal."""
        # Dialog will close after accept() is called
        pass

"""UI components for mood check-in functionality.

This module provides the View layer (QDialog) for mood check-in.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QButtonGroup,
    QRadioButton,
    QTextEdit,
    QMessageBox
)

from app.modules.mood_checkin.view_models import MoodCheckInViewModel


class MoodCheckInDialog(QDialog):
    """Dialog for mood and energy level check-in.
    
    Provides intuitive UI for users to log their current mood and energy level.
    Follows MVVM pattern - this is the View layer.
    """
    
    # Signal emitted when check-in is successfully completed (verbNoun naming)
    moodCheckInCompleted = Signal()
    
    def __init__(self, parent: Optional['QWidget'] = None):
        """Initialize mood check-in dialog.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        
        # Setup ViewModel
        self.view_model = MoodCheckInViewModel(self)
        
        # Connect ViewModel signals
        self.view_model.moodCheckInCompleted.connect(self._on_checkin_completed)
        self.view_model.validationError.connect(self._on_validation_error)
        
        # Setup UI
        self._setup_ui()
        
        # Set window properties
        self.setWindowTitle("Mood Check-in")
        self.setModal(True)
        self.setMinimumWidth(400)
    
    def _setup_ui(self):
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("How are you feeling?")
        header_label.setObjectName("moodCheckInHeader")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)
        
        # Mood level section
        mood_label = QLabel("Mood:")
        mood_label.setObjectName("moodLabel")
        layout.addWidget(mood_label)
        
        self.mood_button_group = QButtonGroup(self)
        mood_layout = QHBoxLayout()
        
        mood_options = [
            ("Happy", "😊"),
            ("Neutral", "😐"),
            ("Stressed", "😰"),
            ("Sad", "😔")
        ]
        
        for mood_name, emoji in mood_options:
            button = QRadioButton(f"{emoji} {mood_name}")
            button.setObjectName(f"mood{mood_name}Button")
            button.setProperty("moodValue", mood_name.lower())
            button.setAccessibleName(f"{mood_name} mood")
            button.setAccessibleDescription(f"Select if you are feeling {mood_name.lower()}")
            self.mood_button_group.addButton(button)
            mood_layout.addWidget(button)
        
        layout.addLayout(mood_layout)
        
        # Energy level section
        energy_label = QLabel("Energy Level:")
        energy_label.setObjectName("energyLabel")
        layout.addWidget(energy_label)
        
        self.energy_button_group = QButtonGroup(self)
        energy_layout = QHBoxLayout()
        
        energy_options = [
            ("High", "⚡"),
            ("Medium", "→"),
            ("Low", "🔋")
        ]
        
        for energy_name, icon in energy_options:
            button = QRadioButton(f"{icon} {energy_name}")
            button.setObjectName(f"energy{energy_name}Button")
            button.setProperty("energyValue", energy_name.lower())
            button.setAccessibleName(f"{energy_name} energy level")
            button.setAccessibleDescription(f"Select if your energy level is {energy_name.lower()}")
            self.energy_button_group.addButton(button)
            energy_layout.addWidget(button)
        
        layout.addLayout(energy_layout)
        
        # Notes section (optional)
        notes_label = QLabel("Notes (optional):")
        notes_label.setObjectName("notesLabel")
        layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setObjectName("notesEdit")
        self.notes_edit.setPlaceholderText("Add any additional notes about how you're feeling...")
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setTabChangesFocus(True)  # Tab moves to next field (accessibility)
        layout.addWidget(self.notes_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.submit_button = QPushButton("Submit")
        self.submit_button.setObjectName("submitButton")
        self.submit_button.setDefault(True)  # Enter key submits
        self.submit_button.clicked.connect(self._submit_checkin)
        button_layout.addWidget(self.submit_button)
        
        layout.addLayout(button_layout)
    
    def _submit_checkin(self):
        """Handle submit button click."""
        # Get selected mood
        mood_button = self.mood_button_group.checkedButton()
        if mood_button:
            self.view_model.moodLevel = mood_button.property("moodValue")
        
        # Get selected energy level
        energy_button = self.energy_button_group.checkedButton()
        if energy_button:
            self.view_model.energyLevel = energy_button.property("energyValue")
        
        # Get notes
        self.view_model.notes = self.notes_edit.toPlainText()
        
        # Submit via ViewModel
        self.view_model.submit_checkin()
    
    def _on_checkin_completed(self, success: bool, message: str):
        """Handle check-in completion.
        
        Args:
            success: Whether check-in was successful
            message: Result message
        """
        if success:
            # Show brief success feedback (could be replaced with status indicator)
            QMessageBox.information(self, "Success", message)
            self.moodCheckInCompleted.emit()
            self.accept()  # Close dialog
        else:
            # Error already shown via validation_error signal
            pass
    
    def _on_validation_error(self, error_message: str):
        """Handle validation error.
        
        Args:
            error_message: Error message to display
        """
        QMessageBox.warning(self, "Validation Error", error_message)
    
    def closeEvent(self, event):
        """Handle dialog close event - cleanup resources.
        
        Args:
            event: Close event
        """
        self.view_model.cleanup()
        super().closeEvent(event)

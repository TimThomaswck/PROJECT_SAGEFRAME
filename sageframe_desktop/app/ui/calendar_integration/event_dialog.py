"""
Event Creation/Edit Dialog for Calendar Integration
"""
from datetime import datetime, timedelta
from typing import Optional, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QDateTimeEdit,
    QCheckBox, QComboBox, QLabel, QMessageBox
)
from PySide6.QtCore import Signal, Qt


class EventDialog(QDialog):
    """Dialog for creating or editing calendar events."""
    
    eventCreated = Signal(dict)  # Emits event data
    eventUpdated = Signal(int, dict)  # Emits event_id and updated data
    
    def __init__(self, parent=None, event_data: Optional[dict] = None):
        """Initialize event dialog.
        
        Args:
            parent: Parent widget
            event_data: Existing event data for editing (optional)
        """
        super().__init__(parent)
        self.event_data = event_data
        self.is_edit_mode = event_data is not None
        
        self.setWindowTitle("Edit Event" if self.is_edit_mode else "Create Event")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self._init_ui()
        
        if self.is_edit_mode:
            self._load_event_data()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Form layout for event fields
        form_layout = QFormLayout()
        
        # Title field
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter event title...")
        form_layout.addRow("Title*:", self.title_input)
        
        # Start time
        self.start_time_input = QDateTimeEdit()
        self.start_time_input.setCalendarPopup(True)
        self.start_time_input.setDateTime(datetime.now())
        self.start_time_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        form_layout.addRow("Start Time*:", self.start_time_input)
        
        # End time
        self.end_time_input = QDateTimeEdit()
        self.end_time_input.setCalendarPopup(True)
        self.end_time_input.setDateTime(datetime.now() + timedelta(hours=1))
        self.end_time_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        form_layout.addRow("End Time*:", self.end_time_input)
        
        # All-day checkbox
        self.all_day_checkbox = QCheckBox("All-day event")
        self.all_day_checkbox.stateChanged.connect(self._on_all_day_changed)
        form_layout.addRow("", self.all_day_checkbox)
        
        # Location field
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Add location...")
        form_layout.addRow("Location:", self.location_input)
        
        # Description field
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Add description...")
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_input)
        
        # Attendees field
        self.attendees_input = QLineEdit()
        self.attendees_input.setPlaceholderText("Comma-separated email addresses...")
        form_layout.addRow("Attendees:", self.attendees_input)
        
        # Recurrence dropdown
        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItems([
            "Does not repeat",
            "Daily",
            "Weekly",
            "Monthly",
            "Yearly"
        ])
        form_layout.addRow("Repeat:", self.recurrence_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Update" if self.is_edit_mode else "Create")
        save_btn.clicked.connect(self._on_save)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _on_all_day_changed(self, state):
        """Handle all-day checkbox state change."""
        is_all_day = state == Qt.CheckState.Checked
        
        # For all-day events, disable time selection
        if is_all_day:
            self.start_time_input.setDisplayFormat("yyyy-MM-dd")
            self.end_time_input.setDisplayFormat("yyyy-MM-dd")
        else:
            self.start_time_input.setDisplayFormat("yyyy-MM-dd HH:mm")
            self.end_time_input.setDisplayFormat("yyyy-MM-dd HH:mm")
    
    def _load_event_data(self):
        """Load existing event data into form fields."""
        if not self.event_data:
            return
        
        self.title_input.setText(self.event_data.get('summary', ''))
        
        if 'start_time' in self.event_data:
            self.start_time_input.setDateTime(self.event_data['start_time'])
        
        if 'end_time' in self.event_data:
            self.end_time_input.setDateTime(self.event_data['end_time'])
        
        if 'location' in self.event_data:
            self.location_input.setText(self.event_data['location'] or '')
        
        if 'description' in self.event_data:
            self.description_input.setPlainText(self.event_data['description'] or '')
        
        if 'is_all_day' in self.event_data:
            self.all_day_checkbox.setChecked(bool(self.event_data['is_all_day']))
        
        if 'attendees' in self.event_data and self.event_data['attendees']:
            # attendees is JSON string, parse it
            import json
            try:
                attendees = json.loads(self.event_data['attendees']) if isinstance(self.event_data['attendees'], str) else self.event_data['attendees']
                self.attendees_input.setText(', '.join(attendees))
            except:
                pass
    
    def _validate_form(self) -> bool:
        """Validate form inputs.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Event title is required.")
            return False
        
        start = self.start_time_input.dateTime().toPython()
        end = self.end_time_input.dateTime().toPython()
        
        if end <= start:
            QMessageBox.warning(self, "Validation Error", "End time must be after start time.")
            return False
        
        return True
    
    def _on_save(self):
        """Handle save button click."""
        if not self._validate_form():
            return
        
        # Collect event data
        event_data = {
            'summary': self.title_input.text().strip(),
            'start_time': self.start_time_input.dateTime().toPython(),
            'end_time': self.end_time_input.dateTime().toPython(),
            'is_all_day': self.all_day_checkbox.isChecked(),
            'location': self.location_input.text().strip() or None,
            'description': self.description_input.toPlainText().strip() or None,
        }
        
        # Parse attendees
        attendees_text = self.attendees_input.text().strip()
        if attendees_text:
            attendees = [email.strip() for email in attendees_text.split(',')]
            event_data['attendees'] = attendees
        
        # Parse recurrence
        recurrence_text = self.recurrence_combo.currentText()
        if recurrence_text != "Does not repeat":
            # Simple RRULE generation
            freq_map = {
                'Daily': 'DAILY',
                'Weekly': 'WEEKLY',
                'Monthly': 'MONTHLY',
                'Yearly': 'YEARLY'
            }
            event_data['recurrence_rule'] = f"FREQ={freq_map[recurrence_text]}"
        
        # Emit appropriate signal
        if self.is_edit_mode:
            event_id = self.event_data.get('id')
            self.eventUpdated.emit(event_id, event_data)
        else:
            self.eventCreated.emit(event_data)
        
        self.accept()
    
    def get_event_data(self) -> dict:
        """Get collected event data.
        
        Returns:
            Dictionary with event data
        """
        return {
            'summary': self.title_input.text().strip(),
            'start_time': self.start_time_input.dateTime().toPython(),
            'end_time': self.end_time_input.dateTime().toPython(),
            'is_all_day': self.all_day_checkbox.isChecked(),
            'location': self.location_input.text().strip() or None,
            'description': self.description_input.toPlainText().strip() or None,
        }

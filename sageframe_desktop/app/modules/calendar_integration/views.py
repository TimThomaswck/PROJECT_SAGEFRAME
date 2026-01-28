"""Calendar settings UI components.

This module provides UI widgets for managing calendar connections,
OAuth authentication, and sync settings.
"""

import json
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QDialog,
    QDialogButtonBox, QTextEdit, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, Signal, Slot

from app.modules.calendar_integration.models import CalendarConnection
from app.modules.calendar_integration.services import CalendarSyncService
from app.modules.calendar_integration.oauth import GoogleOAuthClient, TokenManager
from app.database import SessionLocal


class CalendarConnectionDialog(QDialog):
    """Dialog for connecting a new Google Calendar."""
    
    connectionCreated = Signal(int)  # Emits connection_id
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Connect Google Calendar")
        self.setMinimumWidth(500)
        
        self.oauth_client = GoogleOAuthClient()
        self.token_manager = TokenManager()
        self.session = SessionLocal()
        self.creds = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "To connect your Google Calendar:\n"
            "1. Click 'Start OAuth Flow' below\n"
            "2. Sign in with your Google account in the browser\n"
            "3. Grant calendar access permissions\n"
            "4. Return to this dialog to complete setup"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # OAuth status
        self.status_label = QLabel("Status: Not connected")
        layout.addWidget(self.status_label)
        
        # OAuth button
        self.oauth_button = QPushButton("Start OAuth Flow")
        self.oauth_button.clicked.connect(self._on_oauth_clicked)
        layout.addWidget(self.oauth_button)
        
        # Info text (shown after OAuth success)
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        self.info_text.hide()
        layout.addWidget(self.info_text)
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        layout.addWidget(self.button_box)
    
    @Slot()
    def _on_oauth_clicked(self):
        """Handle OAuth button click."""
        try:
            if not self.oauth_client.has_client_secrets():
                QMessageBox.warning(
                    self,
                    "OAuth Setup Required",
                    "Please configure Google OAuth credentials first.\n\n"
                    "Go to Settings → API Keys and configure Google Calendar OAuth."
                )
                return
            
            self.status_label.setText("Status: Opening browser for authentication...")
            self.oauth_button.setEnabled(False)
            
            # Run OAuth flow (opens browser)
            self.creds = self.oauth_client.initiate_oauth_flow()
            
            # Show success
            self.status_label.setText("Status: ✅ Successfully authenticated!")
            self.info_text.setPlainText(
                f"Connected to: {self.creds.id_token.get('email', 'Unknown')}\n"
                f"Access granted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.info_text.show()
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            
        except FileNotFoundError as e:
            self.status_label.setText("Status: ❌ OAuth configuration missing")
            QMessageBox.critical(self, "Error", str(e))
            self.oauth_button.setEnabled(True)
        except Exception as e:
            self.status_label.setText("Status: ❌ Authentication failed")
            QMessageBox.critical(self, "Error", f"OAuth flow failed:\n{str(e)}")
            self.oauth_button.setEnabled(True)
    
    @Slot()
    def _on_accept(self):
        """Save connection and emit signal."""
        if not self.creds:
            QMessageBox.warning(self, "Warning", "Please complete OAuth flow first.")
            return
        
        try:
            # Extract user email from ID token
            user_email = self.creds.id_token.get('email', 'unknown@gmail.com')
            
            # Create calendar connection
            connection = CalendarConnection(
                provider="google_calendar",
                connection_name=f"Google Calendar ({user_email})",
                user_email=user_email,
                calendar_id="primary",  # Default to primary calendar
                sync_enabled=1,
                sync_status="connected"
            )
            self.session.add(connection)
            self.session.commit()
            
            # Store OAuth tokens in keyring
            expiry = self.creds.expiry if self.creds.expiry else datetime.now()
            self.token_manager.store_tokens(
                connection.id,
                self.creds.token,
                self.creds.refresh_token,
                expiry
            )
            
            # Emit signal
            self.connectionCreated.emit(connection.id)
            
            QMessageBox.information(
                self,
                "Success",
                f"Successfully connected calendar for {user_email}!"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save connection:\n{str(e)}")


class CalendarSettingsWidget(QWidget):
    """Widget for managing calendar connections and sync settings."""
    
    syncRequested = Signal(int)  # Emits connection_id for manual sync
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.session = SessionLocal()
        self.sync_service = CalendarSyncService()
        
        self._init_ui()
        self._refresh_connections()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Calendar Connections")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header_label)
        
        # Connection list
        list_group = QGroupBox("Connected Calendars")
        list_layout = QVBoxLayout(list_group)
        
        self.connection_list = QListWidget()
        self.connection_list.itemSelectionChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.connection_list)
        
        # Connection buttons
        conn_buttons = QHBoxLayout()
        
        self.add_button = QPushButton("➕ Connect Calendar")
        self.add_button.clicked.connect(self._on_add_connection)
        conn_buttons.addWidget(self.add_button)
        
        self.remove_button = QPushButton("🗑️ Remove")
        self.remove_button.clicked.connect(self._on_remove_connection)
        self.remove_button.setEnabled(False)
        conn_buttons.addWidget(self.remove_button)
        
        self.sync_button = QPushButton("🔄 Sync Now")
        self.sync_button.clicked.connect(self._on_sync_now)
        self.sync_button.setEnabled(False)
        conn_buttons.addWidget(self.sync_button)
        
        self.new_event_button = QPushButton("➕ New Event")
        self.new_event_button.clicked.connect(self._on_new_event)
        self.new_event_button.setEnabled(False)
        conn_buttons.addWidget(self.new_event_button)
        
        list_layout.addLayout(conn_buttons)
        layout.addWidget(list_group)
        
        # Events list
        events_group = QGroupBox("Upcoming Events")
        events_layout = QVBoxLayout(events_group)
        
        self.events_list = QListWidget()
        self.events_list.itemDoubleClicked.connect(self._on_edit_event)
        events_layout.addWidget(self.events_list)
        
        # Event buttons
        event_buttons = QHBoxLayout()
        
        self.edit_event_button = QPushButton("✏️ Edit")
        self.edit_event_button.clicked.connect(self._on_edit_event_clicked)
        self.edit_event_button.setEnabled(False)
        event_buttons.addWidget(self.edit_event_button)
        
        self.delete_event_button = QPushButton("🗑️ Delete")
        self.delete_event_button.clicked.connect(self._on_delete_event)
        self.delete_event_button.setEnabled(False)
        event_buttons.addWidget(self.delete_event_button)
        
        events_layout.addLayout(event_buttons)
        layout.addWidget(events_group)
        
        # Status group
        status_group = QGroupBox("Sync Status")
        status_layout = QFormLayout(status_group)
        
        self.status_label = QLabel("No calendar connected")
        status_layout.addRow("Status:", self.status_label)
        
        self.last_sync_label = QLabel("Never")
        status_layout.addRow("Last Sync:", self.last_sync_label)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
    
    def _refresh_connections(self):
        """Refresh connection list from database."""
        self.connection_list.clear()
        connections = self.session.query(CalendarConnection).all()
        
        for conn in connections:
            item_text = f"{conn.connection_name} - {conn.sync_status}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, conn.id)
            self.connection_list.addItem(item)
        
        if not connections:
            self.status_label.setText("No calendar connected")
            self.last_sync_label.setText("Never")
    
    @Slot()
    def _on_selection_changed(self):
        """Handle connection selection change."""
        selected = self.connection_list.selectedItems()
        has_selection = len(selected) > 0
        
        self.remove_button.setEnabled(has_selection)
        self.sync_button.setEnabled(has_selection)
        self.new_event_button.setEnabled(has_selection)
        
        if has_selection:
            connection_id = selected[0].data(Qt.ItemDataRole.UserRole)
            connection = self.session.query(CalendarConnection).get(connection_id)
            
            if connection:
                self.status_label.setText(connection.sync_status.capitalize())
                if connection.last_sync_at:
                    last_sync = connection.last_sync_at.strftime('%Y-%m-%d %H:%M:%S')
                    self.last_sync_label.setText(last_sync)
                else:
                    self.last_sync_label.setText("Never")
                
                # Load upcoming events
                self._refresh_events(connection_id)
        else:
            self.events_list.clear()
    
    @Slot()
    def _on_add_connection(self):
        """Open dialog to add new connection."""
        dialog = CalendarConnectionDialog(self)
        dialog.connectionCreated.connect(self._on_connection_created)
        dialog.exec()
    
    @Slot(int)
    def _on_connection_created(self, connection_id: int):
        """Handle new connection created.
        
        Args:
            connection_id: ID of newly created connection
        """
        self._refresh_connections()
        
        # Trigger initial sync
        self.syncRequested.emit(connection_id)
    
    @Slot()
    def _on_remove_connection(self):
        """Remove selected connection."""
        selected = self.connection_list.selectedItems()
        if not selected:
            return
        
        connection_id = selected[0].data(Qt.ItemDataRole.UserRole)
        connection = self.session.query(CalendarConnection).get(connection_id)
        
        if not connection:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove connection to {connection.connection_name}?\n\n"
            "This will delete all synced events and OAuth tokens.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Delete OAuth tokens from keyring
            token_manager = TokenManager()
            token_manager.delete_tokens(connection_id)
            
            # Delete connection (cascades to events and sync_logs)
            self.session.delete(connection)
            self.session.commit()
            
            self._refresh_connections()
            QMessageBox.information(self, "Success", "Calendar connection removed.")
    
    @Slot()
    def _on_sync_now(self):
        """Trigger manual sync for selected connection."""
        selected = self.connection_list.selectedItems()
        if not selected:
            return
        
        connection_id = selected[0].data(Qt.ItemDataRole.UserRole)
        self.syncRequested.emit(connection_id)
        
        QMessageBox.information(
            self,
            "Sync Started",
            "Calendar sync started. Check status in a moment."
        )
    
    def _refresh_events(self, connection_id: int):
        """Refresh events list for a connection.
        
        Args:
            connection_id: Calendar connection ID
        """
        from datetime import datetime, timezone, timedelta
        
        self.events_list.clear()
        
        # Get events for next 30 days
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(days=30)
        
        events = self.sync_service.get_events_in_range(
            connection_id,
            start_time,
            end_time
        )
        
        for event in events:
            event_time = event.start_time.strftime('%Y-%m-%d %H:%M')
            item_text = f"{event_time} - {event.summary}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, event.id)
            self.events_list.addItem(item)
        
        # Enable/disable event buttons
        self.events_list.itemSelectionChanged.connect(self._on_event_selection_changed)
    
    @Slot()
    def _on_event_selection_changed(self):
        """Handle event selection change."""
        has_selection = len(self.events_list.selectedItems()) > 0
        self.edit_event_button.setEnabled(has_selection)
        self.delete_event_button.setEnabled(has_selection)
    
    @Slot()
    def _on_new_event(self):
        """Open dialog to create new event."""
        from app.ui.calendar_integration.event_dialog import EventDialog
        
        selected = self.connection_list.selectedItems()
        if not selected:
            return
        
        connection_id = selected[0].data(Qt.ItemDataRole.UserRole)
        
        dialog = EventDialog(self)
        dialog.eventCreated.connect(lambda data: self._create_event(connection_id, data))
        dialog.exec()
    
    def _create_event(self, connection_id: int, event_data: dict):
        """Create new calendar event.
        
        Args:
            connection_id: Calendar connection ID
            event_data: Event data from dialog
        """
        try:
            event = self.sync_service.create_event(
                connection_id=connection_id,
                summary=event_data['summary'],
                start_time=event_data['start_time'],
                end_time=event_data['end_time'],
                description=event_data.get('description'),
                location=event_data.get('location'),
                attendees=event_data.get('attendees'),
                is_all_day=event_data.get('is_all_day', False),
                recurrence_rule=event_data.get('recurrence_rule')
            )
            
            QMessageBox.information(self, "Success", "Event created successfully!")
            self._refresh_events(connection_id)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create event: {str(e)}\n\nPlease try again."
            )
    
    @Slot()
    def _on_edit_event_clicked(self):
        """Handle edit event button click."""
        selected_events = self.events_list.selectedItems()
        if selected_events:
            self._on_edit_event(selected_events[0])
    
    @Slot(QListWidgetItem)
    def _on_edit_event(self, item: QListWidgetItem):
        """Open dialog to edit event.
        
        Args:
            item: List widget item for the event
        """
        from app.ui.calendar_integration.event_dialog import EventDialog
        from app.modules.calendar_integration.models import CalendarEvent
        import json
        
        event_id = item.data(Qt.ItemDataRole.UserRole)
        event = self.session.query(CalendarEvent).get(event_id)
        
        if not event:
            return
        
        # Prepare event data for dialog
        event_data = {
            'id': event.id,
            'summary': event.summary,
            'start_time': event.start_time,
            'end_time': event.end_time,
            'description': event.description,
            'location': event.location,
            'is_all_day': bool(event.is_all_day),
            'attendees': event.attendees
        }
        
        dialog = EventDialog(self, event_data=event_data)
        dialog.eventUpdated.connect(self._update_event)
        dialog.exec()
    
    def _update_event(self, event_id: int, event_data: dict):
        """Update existing calendar event.
        
        Args:
            event_id: Event ID
            event_data: Updated event data
        """
        try:
            event = self.sync_service.update_event(
                event_id=event_id,
                summary=event_data.get('summary'),
                start_time=event_data.get('start_time'),
                end_time=event_data.get('end_time'),
                description=event_data.get('description'),
                location=event_data.get('location'),
                attendees=event_data.get('attendees'),
                is_all_day=event_data.get('is_all_day')
            )
            
            QMessageBox.information(self, "Success", "Event updated successfully!")
            
            # Refresh events list
            selected = self.connection_list.selectedItems()
            if selected:
                connection_id = selected[0].data(Qt.ItemDataRole.UserRole)
                self._refresh_events(connection_id)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update event: {str(e)}\n\nPlease try again."
            )
    
    @Slot()
    def _on_delete_event(self):
        """Delete selected event."""
        selected_events = self.events_list.selectedItems()
        if not selected_events:
            return
        
        event_id = selected_events[0].data(Qt.ItemDataRole.UserRole)
        event = self.session.query(CalendarEvent).get(event_id)
        
        if not event:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete event '{event.summary}'?\n\n"
            "This will remove the event from both SageFrame and your calendar.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.sync_service.delete_event_by_id(event_id)
                
                QMessageBox.information(self, "Success", "Event deleted successfully!")
                
                # Refresh events list
                selected = self.connection_list.selectedItems()
                if selected:
                    connection_id = selected[0].data(Qt.ItemDataRole.UserRole)
                    self._refresh_events(connection_id)
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete event: {str(e)}\n\nPlease try again."
                )

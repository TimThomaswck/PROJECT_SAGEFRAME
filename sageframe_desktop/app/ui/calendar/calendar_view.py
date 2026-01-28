"""Calendar view with month display and Google Calendar integration."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCalendarWidget, QTextEdit, QFrame, QScrollArea, QMessageBox, 
    QDialog, QDialogButtonBox, QLineEdit, QTextBrowser
)
from PySide6.QtCore import Qt, QDate, Signal, QTimer, QUrl
from PySide6.QtGui import QTextCharFormat, QColor, QFont, QDesktopServices
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import os
import json
import pickle
from pathlib import Path

# Optional imports - loaded lazily when needed
GOOGLE_CALENDAR_AVAILABLE = False
ICALENDAR_AVAILABLE = False


class CalendarEventWidget(QFrame):
    """Individual event display widget."""
    
    clicked = Signal(dict)  # Emits event data
    
    def __init__(self, event_data: dict, parent=None):
        super().__init__(parent)
        self.event_data = event_data
        self._setup_ui()
    
    def _setup_ui(self):
        """Build event widget UI."""
        self.setObjectName("calendarEvent")
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        
        # Event title
        title_label = QLabel(self.event_data.get("summary", "Untitled Event"))
        title_label.setObjectName("eventTitle")
        title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Event time
        time_str = self._format_event_time()
        time_label = QLabel(time_str)
        time_label.setObjectName("eventTime")
        time_label.setStyleSheet("color: #888;")
        layout.addWidget(time_label)
        
        # Apply color coding
        color = self.event_data.get("color", "#3b82f6")
        self.setStyleSheet(f"""
            QFrame#calendarEvent {{
                background-color: {color}20;
                border-left: 3px solid {color};
                border-radius: 4px;
                padding: 4px;
            }}
            QFrame#calendarEvent:hover {{
                background-color: {color}40;
            }}
        """)
    
    def _format_event_time(self) -> str:
        """Format event start/end time."""
        start = self.event_data.get("start", {})
        end = self.event_data.get("end", {})
        
        # All-day event
        if "date" in start:
            return "All day"
        
        # Timed event
        start_time = start.get("dateTime", "")
        end_time = end.get("dateTime", "")
        
        if start_time and end_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                return f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
            except:
                pass
        
        return "Time TBD"
    
    def mousePressEvent(self, event):
        """Handle click on event."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.event_data)
        super().mousePressEvent(event)


class CalendarView(QWidget):
    """Calendar view with Google Calendar integration.
    
    Features:
    - Month calendar widget with event highlighting
    - Daily event list for selected date
    - OAuth connection wizard for Google Calendar
    - Auto-sync background worker
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.events_cache: Dict[str, List[dict]] = {}  # date_str -> [events]
        self.is_connected = False
        self.sync_timer = None
        self._setup_ui()
        self._check_connection_status()
    
    def _setup_ui(self):
        """Build calendar view UI."""
        self.setObjectName("calendarView")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Header with title and sync button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Calendar")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Connection status and button
        self.connection_status_label = QLabel("Not connected")
        self.connection_status_label.setStyleSheet("color: #888; padding-right: 8px;")
        header_layout.addWidget(self.connection_status_label)
        
        self.connect_btn = QPushButton("Connect via OAuth")
        self.connect_btn.setObjectName("connectCalendarBtn")
        self.connect_btn.clicked.connect(self._start_oauth_flow)
        header_layout.addWidget(self.connect_btn)
        
        self.ics_btn = QPushButton("Connect via ICS URL")
        self.ics_btn.setObjectName("icsCalendarBtn")
        self.ics_btn.clicked.connect(self._connect_via_ics)
        header_layout.addWidget(self.ics_btn)
        
        self.sync_btn = QPushButton("🔄 Sync")
        self.sync_btn.setObjectName("syncCalendarBtn")
        self.sync_btn.clicked.connect(self._manual_sync)
        self.sync_btn.setVisible(False)
        header_layout.addWidget(self.sync_btn)
        
        self.create_event_btn = QPushButton("+ Create Event")
        self.create_event_btn.setObjectName("createEventBtn")
        self.create_event_btn.clicked.connect(self._show_create_event_dialog)
        self.create_event_btn.setVisible(False)
        header_layout.addWidget(self.create_event_btn)
        
        main_layout.addLayout(header_layout)
        
        # Main content area - large calendar + right sidebar (events + AI)
        content_layout = QHBoxLayout()
        
        # Left: Calendar widget
        calendar_container = QFrame()
        calendar_container.setObjectName("calendarContainer")
        calendar_layout = QVBoxLayout(calendar_container)
        
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setObjectName("calendarWidget")
        self.calendar_widget.setGridVisible(True)
        self.calendar_widget.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar_widget.selectionChanged.connect(self._on_date_selected)
        self.calendar_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.calendar_widget.customContextMenuRequested.connect(self._show_calendar_context_menu)
        calendar_layout.addWidget(self.calendar_widget)
        
        content_layout.addWidget(calendar_container, stretch=5)
        
        # Right sidebar: Upcoming events + AI suggestions (stacked)
        right_sidebar = QFrame()
        right_sidebar.setObjectName("rightSidebarContainer")
        right_sidebar_layout = QVBoxLayout(right_sidebar)
        right_sidebar_layout.setContentsMargins(0, 0, 0, 0)
        right_sidebar_layout.setSpacing(12)

        # Upcoming events (smaller)
        events_container = QFrame()
        events_container.setObjectName("eventsContainer")
        events_layout = QVBoxLayout(events_container)
        events_layout.setContentsMargins(12, 12, 12, 12)
        
        self.selected_date_label = QLabel()
        self.selected_date_label.setObjectName("selectedDateLabel")
        date_font = QFont()
        date_font.setPointSize(14)
        date_font.setBold(True)
        self.selected_date_label.setFont(date_font)
        events_layout.addWidget(self.selected_date_label)
        
        # Scrollable events area
        events_scroll = QScrollArea()
        events_scroll.setObjectName("eventsScroll")
        events_scroll.setWidgetResizable(True)
        events_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.events_list_widget = QWidget()
        self.events_list_layout = QVBoxLayout(self.events_list_widget)
        self.events_list_layout.setContentsMargins(0, 0, 0, 0)
        self.events_list_layout.setSpacing(8)
        self.events_list_layout.addStretch()
        
        events_scroll.setWidget(self.events_list_widget)
        events_layout.addWidget(events_scroll)
        
        right_sidebar_layout.addWidget(events_container, stretch=1)
        
        # AI Suggestions Panel (below upcoming events)
        ai_container = QFrame()
        ai_container.setObjectName("aiSuggestionsContainer")
        ai_layout = QVBoxLayout(ai_container)
        ai_layout.setContentsMargins(12, 12, 12, 12)
        ai_layout.setSpacing(10)
        
        ai_title = QLabel("🤖 AI Assistant")
        ai_title_font = QFont()
        ai_title_font.setPointSize(12)
        ai_title_font.setBold(True)
        ai_title.setFont(ai_title_font)
        ai_layout.addWidget(ai_title)
        
        # AI suggestions scroll area
        ai_scroll = QScrollArea()
        ai_scroll.setWidgetResizable(True)
        ai_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.ai_content_widget = QWidget()
        self.ai_content_layout = QVBoxLayout(self.ai_content_widget)
        self.ai_content_layout.setContentsMargins(0, 0, 0, 0)
        self.ai_content_layout.setSpacing(12)
        
        # Placeholder message
        self.ai_loading_label = QLabel("Analyzing your schedule...")
        self.ai_loading_label.setWordWrap(True)
        self.ai_loading_label.setStyleSheet("color: #888; font-style: italic;")
        self.ai_content_layout.addWidget(self.ai_loading_label)
        
        self.ai_content_layout.addStretch()
        ai_scroll.setWidget(self.ai_content_widget)
        ai_layout.addWidget(ai_scroll)
        
        # Refresh AI button
        refresh_ai_btn = QPushButton("🔄 Refresh Suggestions")
        refresh_ai_btn.setObjectName("refreshAIBtn")
        refresh_ai_btn.clicked.connect(self._refresh_ai_suggestions)
        ai_layout.addWidget(refresh_ai_btn)
        
        right_sidebar_layout.addWidget(ai_container, stretch=2)

        content_layout.addWidget(right_sidebar, stretch=2)
        
        main_layout.addLayout(content_layout)
        
        # Apply initial styling
        self.setStyleSheet("""
            QFrame#calendarContainer, QFrame#eventsContainer, QFrame#aiSuggestionsContainer {
                background-color: #2d2d2d;
                border-radius: 8px;
                border: 1px solid #3d3d3d;
            }
            QCalendarWidget {
                background-color: #2d2d2d;
            }
            QPushButton#connectCalendarBtn, QPushButton#icsCalendarBtn {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton#connectCalendarBtn:hover, QPushButton#icsCalendarBtn:hover {
                background-color: #2563eb;
            }
            QPushButton#icsCalendarBtn {
                background-color: #10b981;
            }
            QPushButton#icsCalendarBtn:hover {
                background-color: #059669;
            }
            QPushButton#syncCalendarBtn {
                background-color: #8b5cf6;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
            }
            QPushButton#syncCalendarBtn:hover {
                background-color: #7c3aed;
            }
            QPushButton#createEventBtn {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton#createEventBtn:hover {
                background-color: #059669;
            }
            QPushButton#refreshAIBtn {
                background-color: #6366f1;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton#refreshAIBtn:hover {
                background-color: #4f46e5;
            }
            QPushButton#createEventBtn:hover {
                background-color: #059669;
            }
        """)
        
        # Update selected date label
        self._update_selected_date_label()
    
    def _check_icalendar_dependency(self) -> bool:
        """Check if icalendar is installed, offer to install if not."""
        global ICALENDAR_AVAILABLE
        try:
            import requests
            from icalendar import Calendar as ICalendar
            ICALENDAR_AVAILABLE = True
            return True
        except ImportError:
            reply = QMessageBox.question(
                self,
                "Install Dependencies?",
                "The ICS calendar feature requires additional packages:\n\n"
                "• icalendar\n"
                "• requests\n\n"
                "Would you like to install them now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                return self._install_packages(['icalendar', 'requests'])
            return False
    
    def _check_google_auth_dependency(self) -> bool:
        """Check if Google auth packages are installed, offer to install if not."""
        global GOOGLE_CALENDAR_AVAILABLE
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            GOOGLE_CALENDAR_AVAILABLE = True
            return True
        except ImportError:
            reply = QMessageBox.question(
                self,
                "Install Dependencies?",
                "The Google Calendar OAuth feature requires additional packages:\n\n"
                "• google-auth\n"
                "• google-auth-oauthlib\n"
                "• google-auth-httplib2\n"
                "• google-api-python-client\n\n"
                "Would you like to install them now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                return self._install_packages([
                    'google-auth',
                    'google-auth-oauthlib',
                    'google-auth-httplib2',
                    'google-api-python-client'
                ])
            return False
    
    def _install_packages(self, packages: List[str]) -> bool:
        """Install Python packages using pip."""
        import subprocess
        import sys
        
        try:
            QMessageBox.information(
                self,
                "Installing...",
                f"Installing packages: {', '.join(packages)}\n\n"
                "This may take a minute..."
            )
            
            for package in packages:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            
            QMessageBox.information(
                self,
                "Success!",
                "✓ Dependencies installed successfully.\n\n"
                "Please try your action again."
            )
            return True
            
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(
                self,
                "Installation Failed",
                f"Failed to install dependencies:\n\n{str(e)}\n\n"
                "Please install manually using:\n"
                f"pip install {' '.join(packages)}"
            )
            return False
    
    def _check_connection_status(self):
        """Check if Google Calendar is connected."""
        try:
            # First check for ICS URL connection
            creds_dir = Path.home() / '.sageframe'
            ics_path = creds_dir / 'calendar_ics.json'
            
            if ics_path.exists():
                try:
                    with open(ics_path, 'r') as f:
                        data = json.load(f)
                        self.ics_url = data.get('ics_url')
                        if self.ics_url:
                            self._update_connection_status(True)
                            self._load_events()
                            return
                except Exception as e:
                    print(f"Error loading ICS config: {e}")
            
            # Check for stored OAuth credentials
            token_path = creds_dir / 'calendar_token.pickle'
            
            if token_path.exists():
                # Try to load and validate credentials
                try:
                    from google.auth.transport.requests import Request
                    from googleapiclient.discovery import build
                    import pickle
                    
                    with open(token_path, 'rb') as token:
                        creds = pickle.load(token)
                    
                    # Check if credentials are valid
                    if creds and creds.valid:
                        # Build service
                        self.calendar_creds = creds
                        self.calendar_service = build('calendar', 'v3', credentials=creds)
                        self._update_connection_status(True)
                        # Load events
                        self._load_events()
                        return
                    elif creds and creds.expired and creds.refresh_token:
                        # Try to refresh
                        creds.refresh(Request())
                        self.calendar_creds = creds
                        self.calendar_service = build('calendar', 'v3', credentials=creds)
                        
                        # Save refreshed token
                        with open(token_path, 'wb') as token:
                            pickle.dump(creds, token)
                        
                        self._update_connection_status(True)
                        # Load events
                        self._load_events()
                        return
                except Exception as e:
                    print(f"Error loading stored credentials: {e}")
            
            # No valid credentials found
            self._update_connection_status(False)
            
        except Exception as e:
            print(f"Error checking connection status: {e}")
            self._update_connection_status(False)
    
    def _update_connection_status(self, connected: bool):
        """Update UI based on connection status."""
        self.is_connected = connected
        
        if connected:
            self.connection_status_label.setText("✓ Connected")
            self.connection_status_label.setStyleSheet("color: #4ade80;")
            self.connect_btn.setVisible(False)
            self.ics_btn.setVisible(False)
            self.sync_btn.setVisible(True)
            self.create_event_btn.setVisible(True)
            self._start_auto_sync()
            # Initialize AI suggestions
            QTimer.singleShot(1000, self._refresh_ai_suggestions)
        else:
            self.connection_status_label.setText("Not connected")
            self.connection_status_label.setStyleSheet("color: #888;")
            self.connect_btn.setVisible(True)
            self.ics_btn.setVisible(True)
            self.sync_btn.setVisible(False)
            self.create_event_btn.setVisible(False)
            if self.sync_timer:
                self.sync_timer.stop()
    
    def _connect_via_ics(self):
        """Connect using ICS URL (simpler, read-only)."""
        # Check if dependencies are installed
        if not self._check_icalendar_dependency():
            return
        
        # Import now that we know they're available
        import requests
        from icalendar import Calendar as ICalendar
        
        # Show instructions dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Connect via ICS URL")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Instructions
        instructions = QTextBrowser()
        instructions.setOpenExternalLinks(True)
        instructions.setHtml("""
            <h3>How to get your Google Calendar ICS URL:</h3>
            <ol>
                <li>Open <a href="https://calendar.google.com">Google Calendar</a> in your browser</li>
                <li>Click the <b>⚙ Settings</b> icon (top right)</li>
                <li>Click <b>Settings</b> from the menu</li>
                <li>In the left sidebar, select your calendar under <b>"Settings for my calendars"</b></li>
                <li>Scroll down to <b>"Integrate calendar"</b></li>
                <li>Copy the <b>"Secret address in iCal format"</b> URL</li>
                <li>Paste it below:</li>
            </ol>
            <p><b>Note:</b> This provides read-only access to your calendar.</p>
        """)
        instructions.setMaximumHeight(300)
        layout.addWidget(instructions)
        
        # URL input
        url_label = QLabel("ICS URL:")
        layout.addWidget(url_label)
        
        url_input = QLineEdit()
        url_input.setPlaceholderText("https://calendar.google.com/calendar/ical/.../basic.ics")
        layout.addWidget(url_input)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            ics_url = url_input.text().strip()
            if ics_url:
                self._setup_ics_connection(ics_url)
    
    def _setup_ics_connection(self, ics_url: str):
        """Set up ICS URL connection."""
        import requests
        from icalendar import Calendar as ICalendar
        
        try:
            # Test the URL by fetching calendar
            response = requests.get(ics_url, timeout=10)
            response.raise_for_status()
            
            # Parse ICS to verify it's valid
            cal = ICalendar.from_ical(response.content)
            
            # Store URL
            creds_dir = Path.home() / '.sageframe'
            creds_dir.mkdir(exist_ok=True)
            ics_path = creds_dir / 'calendar_ics.json'
            
            with open(ics_path, 'w') as f:
                json.dump({'ics_url': ics_url}, f)
            
            # Store URL in instance
            self.ics_url = ics_url
            
            # Update status
            self._update_connection_status(True)
            
            QMessageBox.information(
                self,
                "Connected!",
                "✓ Successfully connected via ICS URL.\n\n"
                "Your calendar events will now sync automatically (read-only)."
            )
            
            # Load events
            self._load_events()
            
        except requests.RequestException as e:
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"Failed to fetch calendar from ICS URL:\n\n{str(e)}\n\n"
                "Please check the URL and try again."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to parse calendar:\n\n{str(e)}\n\n"
                "Make sure you copied the correct ICS URL."
            )
    
    def _start_oauth_flow(self):
        """Start OAuth connection wizard for Google Calendar."""
        # Check if dependencies are installed
        if not self._check_google_auth_dependency():
            return
        
        # Import now that we know they're available
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            # OAuth 2.0 scopes for Google Calendar (full access for read/write)
            SCOPES = ['https://www.googleapis.com/auth/calendar']
            
            # Path to store credentials
            creds_dir = Path.home() / '.sageframe'
            creds_dir.mkdir(exist_ok=True)
            token_path = creds_dir / 'calendar_token.pickle'
            client_secret_path = creds_dir / 'client_secret.json'
            
            # Check if client_secret.json exists
            if not client_secret_path.exists():
                # Show instructions to get client_secret.json
                self._show_oauth_setup_instructions()
                return
            
            creds = None
            
            # Load existing token if available
            if token_path.exists():
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, let user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        print(f"Error refreshing token: {e}")
                        creds = None
                
                if not creds:
                    # Start OAuth flow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(client_secret_path), SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Store credentials
            self.calendar_creds = creds
            
            # Build Google Calendar service
            self.calendar_service = build('calendar', 'v3', credentials=creds)
            
            # Update connection status
            self._update_connection_status(True)
            
            # Show success message
            QMessageBox.information(
                self,
                "Connected!",
                "✓ Successfully connected to Google Calendar.\n\n"
                "Your calendar events will now sync automatically."
            )
            
            # Load events immediately
            self._load_events()
            
        except ImportError:
            # Google Calendar API libraries not installed
            self._show_install_dependencies_dialog()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"Failed to connect to Google Calendar:\n\n{str(e)}\n\n"
                "Please check your credentials and try again."
            )
            print(f"OAuth error: {e}")
            import traceback
            traceback.print_exc()
    
    def _show_oauth_setup_instructions(self):
        """Show instructions for setting up Google Calendar OAuth."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Google Calendar Setup Required")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(
            "To connect Google Calendar, you need to set up OAuth credentials.\n\n"
            "Click 'Open Instructions' to view the setup guide."
        )
        
        open_btn = msg.addButton("Open Instructions", QMessageBox.ButtonRole.AcceptRole)
        close_btn = msg.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == open_btn:
            # Open setup instructions
            instructions_url = "https://developers.google.com/calendar/api/quickstart/python"
            QDesktopServices.openUrl(QUrl(instructions_url))
            
            # Show detailed local instructions
            self._show_detailed_instructions()
    
    def _show_detailed_instructions(self):
        """Show detailed step-by-step instructions."""
        creds_dir = Path.home() / '.sageframe'
        
        QMessageBox.information(
            self,
            "Setup Instructions",
            "Google Calendar OAuth Setup:\n\n"
            "1. Go to Google Cloud Console:\n"
            "   https://console.cloud.google.com/\n\n"
            "2. Create a new project (or select existing)\n\n"
            "3. Enable Google Calendar API:\n"
            "   - APIs & Services → Library\n"
            "   - Search 'Google Calendar API'\n"
            "   - Click 'Enable'\n\n"
            "4. Create OAuth 2.0 Credentials:\n"
            "   - APIs & Services → Credentials\n"
            "   - Create Credentials → OAuth client ID\n"
            "   - Application type: Desktop app\n"
            "   - Download JSON file\n\n"
            f"5. Save the downloaded file as:\n"
            f"   {creds_dir / 'client_secret.json'}\n\n"
            "6. Click 'Connect Google Calendar' again"
        )
    
    def _show_install_dependencies_dialog(self):
        """Show dialog to install Google Calendar dependencies."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Install Dependencies")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(
            "Google Calendar integration requires additional packages.\n\n"
            "Required packages:\n"
            "• google-auth\n"
            "• google-auth-oauthlib\n"
            "• google-auth-httplib2\n"
            "• google-api-python-client\n\n"
            "Would you like to install them now?"
        )
        
        install_btn = msg.addButton("Install", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == install_btn:
            self._install_google_dependencies()
    
    def _install_google_dependencies(self):
        """Install Google Calendar API dependencies."""
        import subprocess
        import sys
        
        packages = [
            'google-auth',
            'google-auth-oauthlib',
            'google-auth-httplib2',
            'google-api-python-client'
        ]
        
        try:
            # Show progress message
            self.connect_btn.setEnabled(False)
            self.connect_btn.setText("Installing...")
            
            # Install packages
            for package in packages:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            
            # Success
            QMessageBox.information(
                self,
                "Installation Complete",
                "✓ Google Calendar dependencies installed successfully!\n\n"
                "Please click 'Connect Google Calendar' again."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Installation Failed",
                f"Failed to install dependencies:\n\n{str(e)}\n\n"
                "Please install manually using:\n"
                f"pip install {' '.join(packages)}"
            )
        finally:
            self.connect_btn.setEnabled(True)
            self.connect_btn.setText("Connect Google Calendar")
        
        # Simulate connection for testing
        # self._update_connection_status(True)
        # self._load_events()
    
    def _start_auto_sync(self):
        """Start background auto-sync timer (every 10 minutes)."""
        if not self.sync_timer:
            self.sync_timer = QTimer()
            self.sync_timer.timeout.connect(self._background_sync)
        
        # Sync every 10 minutes
        self.sync_timer.start(10 * 60 * 1000)
        
        # Do initial sync
        self._background_sync()
    
    def _background_sync(self):
        """Background sync worker."""
        print("Background calendar sync triggered...")
        # TODO: Implement actual sync with Google Calendar API
        self._load_events()
    
    def _manual_sync(self):
        """Manual sync triggered by user."""
        print("Manual calendar sync...")
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("Syncing...")
        
        # TODO: Implement actual sync
        self._load_events()
        
        # Re-enable after 2 seconds
        QTimer.singleShot(2000, lambda: (
            self.sync_btn.setEnabled(True),
            self.sync_btn.setText("🔄 Sync")
        ))
    
    def _load_events(self):
        """Load events from Google Calendar."""
        if hasattr(self, 'ics_url') and self.ics_url:
            # Fetch from ICS URL
            self._fetch_ics_events()
        elif hasattr(self, 'calendar_service') and self.calendar_service:
            # Fetch from Google Calendar API
            self._fetch_google_calendar_events()
        else:
            # Use mock data when not connected
            self._load_mock_events()
    
    def _fetch_ics_events(self):
        """Fetch events from ICS URL."""
        import requests
        from icalendar import Calendar as ICalendar
        
        try:
            response = requests.get(self.ics_url, timeout=10)
            response.raise_for_status()
            
            cal = ICalendar.from_ical(response.content)
            
            # Clear cache
            self.events_cache.clear()
            
            # Parse events
            for component in cal.walk():
                if component.name == "VEVENT":
                    try:
                        summary = str(component.get('summary', 'Untitled Event'))
                        
                        # Get start/end times
                        dtstart = component.get('dtstart')
                        dtend = component.get('dtend')
                        
                        if not dtstart:
                            continue
                        
                        # Convert to datetime
                        start_dt = dtstart.dt
                        end_dt = dtend.dt if dtend else start_dt
                        
                        # Handle all-day events and timed events
                        if isinstance(start_dt, date) and not isinstance(start_dt, datetime):
                            # All-day event
                            date_str = start_dt.isoformat()
                            event_data = {
                                'summary': summary,
                                'start': {'date': date_str},
                                'end': {'date': end_dt.isoformat() if end_dt else date_str},
                                'color': '#3b82f6',
                                'description': str(component.get('description', '')),
                                'location': str(component.get('location', ''))
                            }
                        else:
                            # Timed event
                            date_str = start_dt.date().isoformat()
                            event_data = {
                                'summary': summary,
                                'start': {'dateTime': start_dt.isoformat()},
                                'end': {'dateTime': end_dt.isoformat() if end_dt else start_dt.isoformat()},
                                'color': '#8b5cf6',
                                'description': str(component.get('description', '')),
                                'location': str(component.get('location', ''))
                            }
                        
                        # Add to cache
                        if date_str not in self.events_cache:
                            self.events_cache[date_str] = []
                        self.events_cache[date_str].append(event_data)
                        
                    except Exception as e:
                        print(f"Error parsing event: {e}")
                        continue
            
            # Highlight dates with events
            self._highlight_event_dates()
            
            # Refresh current date's events
            self._display_events_for_date(self.calendar_widget.selectedDate())
            
            print(f"Loaded {sum(len(events) for events in self.events_cache.values())} events from ICS")
            
        except Exception as e:
            print(f"Error fetching ICS events: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to mock data
            self._load_mock_events()
    
    def _fetch_google_calendar_events(self):
        """Fetch events from Google Calendar API."""
        try:
            # Get events for the next 30 days
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=30)).isoformat() + 'Z'
            
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Clear cache and organize by date
            self.events_cache.clear()
            
            for event in events:
                start = event.get('start', {})
                
                # Get date string
                if 'date' in start:
                    # All-day event
                    date_str = start['date']
                elif 'dateTime' in start:
                    # Timed event
                    start_dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    date_str = start_dt.date().isoformat()
                else:
                    continue
                
                # Add to cache
                if date_str not in self.events_cache:
                    self.events_cache[date_str] = []
                
                # Get event color (use default if not specified)
                color = event.get('colorId', '#3b82f6')
                color_map = {
                    '1': '#7986cb',  # Lavender
                    '2': '#33b679',  # Sage
                    '3': '#8e24aa',  # Grape
                    '4': '#e67c73',  # Flamingo
                    '5': '#f6c026',  # Banana
                    '6': '#f5511d',  # Tangerine
                    '7': '#039be5',  # Peacock
                    '8': '#616161',  # Graphite
                    '9': '#3f51b5',  # Blueberry
                    '10': '#0b8043', # Basil
                    '11': '#d60000', # Tomato
                }
                event_color = color_map.get(color, '#3b82f6')
                
                self.events_cache[date_str].append({
                    'summary': event.get('summary', 'Untitled Event'),
                    'start': start,
                    'end': event.get('end', {}),
                    'color': event_color,
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'id': event.get('id', '')
                })
            
            # Highlight dates with events
            self._highlight_event_dates()
            
            # Refresh current date's events
            self._display_events_for_date(self.calendar_widget.selectedDate())
            
            print(f"Loaded {len(events)} events from Google Calendar")
            
        except Exception as e:
            print(f"Error fetching Google Calendar events: {e}")
            import traceback
            traceback.print_exc()
            
            # Fall back to mock data
            self._load_mock_events()
    
    def _load_mock_events(self):
        """Load mock events for testing (when not connected)."""
        today = date.today()
        
        # Mock events
        self.events_cache.clear()
        
        # Add some sample events
        for i in range(7):
            event_date = today + timedelta(days=i)
            date_str = event_date.isoformat()
            
            self.events_cache[date_str] = [
                {
                    "summary": f"Meeting {i+1}",
                    "start": {"dateTime": f"{date_str}T10:00:00"},
                    "end": {"dateTime": f"{date_str}T11:00:00"},
                    "color": "#3b82f6"
                },
                {
                    "summary": f"Task Review {i+1}",
                    "start": {"dateTime": f"{date_str}T14:00:00"},
                    "end": {"dateTime": f"{date_str}T15:00:00"},
                    "color": "#8b5cf6"
                }
            ]
        
        # Highlight dates with events
        self._highlight_event_dates()
        
        # Refresh current date's events
        self._display_events_for_date(self.calendar_widget.selectedDate())
    
    def _highlight_event_dates(self):
        """Highlight dates that have events on the calendar."""
        # Create format for dates with events
        event_format = QTextCharFormat()
        event_format.setBackground(QColor("#3b82f6"))
        event_format.setForeground(QColor("#ffffff"))
        
        # Apply format to dates with events
        for date_str in self.events_cache.keys():
            try:
                event_date = date.fromisoformat(date_str)
                qdate = QDate(event_date.year, event_date.month, event_date.day)
                self.calendar_widget.setDateTextFormat(qdate, event_format)
            except:
                pass
    
    def _on_date_selected(self):
        """Handle calendar date selection."""
        selected_date = self.calendar_widget.selectedDate()
        self._update_selected_date_label()
        self._display_events_for_date(selected_date)
    
    def _update_selected_date_label(self):
        """Update the selected date label."""
        selected_date = self.calendar_widget.selectedDate()
        date_str = selected_date.toString("dddd, MMMM d, yyyy")
        self.selected_date_label.setText(date_str)
    
    def _display_events_for_date(self, qdate: QDate):
        """Display events for the selected date."""
        # Clear existing events
        while self.events_list_layout.count() > 1:  # Keep the stretch
            item = self.events_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get events for this date
        date_str = qdate.toString("yyyy-MM-dd")
        events = self.events_cache.get(date_str, [])
        
        if not events:
            # Show "no events" message
            no_events_label = QLabel("No events scheduled")
            no_events_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_events_label.setStyleSheet("color: #888; padding: 20px;")
            self.events_list_layout.insertWidget(0, no_events_label)
        else:
            # Display events
            for event_data in events:
                event_widget = CalendarEventWidget(event_data)
                event_widget.clicked.connect(self._on_event_clicked)
                self.events_list_layout.insertWidget(
                    self.events_list_layout.count() - 1, 
                    event_widget
                )
    
    def _on_event_clicked(self, event_data: dict):
        """Handle click on an event - show edit/delete dialog."""
        self._show_event_details_dialog(event_data)
    
    def _create_event(self):
        """Deprecated: Old method, redirects to new one."""
        self._show_create_event_dialog()
    
    # ==================== Event CRUD Methods ====================
    
    def _show_calendar_context_menu(self, position):
        """Show context menu when right-clicking on calendar."""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        menu = QMenu(self)
        create_action = QAction("Create Event", self)
        create_action.triggered.connect(self._show_create_event_dialog)
        menu.addAction(create_action)
        
        # Show menu at cursor position
        menu.exec(self.calendar_widget.mapToGlobal(position))
    
    def _show_create_event_dialog(self, suggested_event: dict = None):
        """Show dialog to create a new event."""
        dialog = EventDialog(self, suggested_event=suggested_event)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event_data = dialog.get_event_data()
            self._create_google_calendar_event(event_data)
    
    def _show_event_details_dialog(self, event_data: dict):
        """Show dialog with event details and edit/delete options."""
        dialog = EventDialog(self, event_data=event_data, edit_mode=True)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # User clicked Save - update event
            updated_data = dialog.get_event_data()
            self._update_google_calendar_event(event_data.get('id'), updated_data)
        elif dialog.delete_requested:
            # User clicked Delete
            self._delete_google_calendar_event(event_data.get('id'))
    
    def _create_google_calendar_event(self, event_data: dict):
        """Create event in Google Calendar."""
        if not self.is_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to Google Calendar first.")
            return
        
        try:
            # For OAuth connection
            if hasattr(self, 'calendar_service') and self.calendar_service:
                from googleapiclient.discovery import build
                
                # Build event object for Google Calendar API
                event = {
                    'summary': event_data['title'],
                    'description': event_data.get('description', ''),
                    'location': event_data.get('location', ''),
                    'start': {
                        'dateTime': event_data['start_datetime'].isoformat(),
                        'timeZone': 'UTC',
                    },
                    'end': {
                        'dateTime': event_data['end_datetime'].isoformat(),
                        'timeZone': 'UTC',
                    },
                    'colorId': self._get_color_id_for_type(event_data.get('event_type', 'Other')),
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': event_data.get('reminder_minutes', 15)},
                        ],
                    } if event_data.get('reminder_minutes') else {'useDefault': True},
                }
                
                # Create event
                created_event = self.calendar_service.events().insert(
                    calendarId='primary', 
                    body=event
                ).execute()
                
                QMessageBox.information(
                    self,
                    "Event Created",
                    f"✓ Event '{event_data['title']}' created successfully!"
                )
                
                # Refresh calendar
                self._load_events()
                
            else:
                # ICS connection is read-only
                QMessageBox.warning(
                    self,
                    "Read-Only Connection",
                    "ICS URL connection is read-only. Please use OAuth for creating events."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Failed to Create Event",
                f"Error creating event:\n\n{str(e)}"
            )
    
    def _update_google_calendar_event(self, event_id: str, event_data: dict):
        """Update existing event in Google Calendar."""
        if not hasattr(self, 'calendar_service') or not self.calendar_service:
            QMessageBox.warning(self, "Read-Only", "Cannot edit events with ICS connection.")
            return
        
        try:
            # Build updated event object
            event = {
                'summary': event_data['title'],
                'description': event_data.get('description', ''),
                'location': event_data.get('location', ''),
                'start': {
                    'dateTime': event_data['start_datetime'].isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': event_data['end_datetime'].isoformat(),
                    'timeZone': 'UTC',
                },
                'colorId': self._get_color_id_for_type(event_data.get('event_type', 'Other')),
            }
            
            # Update event
            self.calendar_service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            QMessageBox.information(self, "Updated", "✓ Event updated successfully!")
            self._load_events()
            
        except Exception as e:
            QMessageBox.critical(self, "Update Failed", f"Error updating event:\n\n{str(e)}")
    
    def _delete_google_calendar_event(self, event_id: str):
        """Delete event from Google Calendar."""
        if not hasattr(self, 'calendar_service') or not self.calendar_service:
            QMessageBox.warning(self, "Read-Only", "Cannot delete events with ICS connection.")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Event",
            "Are you sure you want to delete this event?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.calendar_service.events().delete(
                    calendarId='primary',
                    eventId=event_id
                ).execute()
                
                QMessageBox.information(self, "Deleted", "✓ Event deleted successfully!")
                self._load_events()
                
            except Exception as e:
                QMessageBox.critical(self, "Delete Failed", f"Error deleting event:\n\n{str(e)}")
    
    def _get_color_id_for_type(self, event_type: str) -> str:
        """Map event type to Google Calendar color ID."""
        color_map = {
            'Meeting': '9',      # Blue
            'Task/Deadline': '11',  # Red
            'Reminder': '5',     # Yellow
            'Personal': '10',    # Green
            'Work': '8',         # Gray
            'Other': '7',        # Cyan
        }
        return color_map.get(event_type, '7')
    
    # ==================== AI Suggestions ====================
    
    def _refresh_ai_suggestions(self):
        """Refresh AI suggestions based on current calendar."""
        if not self.is_connected:
            return
        
        # Clear current suggestions
        while self.ai_content_layout.count() > 0:
            item = self.ai_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Show loading
        loading_label = QLabel("🤖 Analyzing your schedule...")
        loading_label.setWordWrap(True)
        loading_label.setStyleSheet("color: #888; font-style: italic; padding: 8px;")
        self.ai_content_layout.addWidget(loading_label)
        
        # Get AI suggestions in background
        QTimer.singleShot(500, self._generate_ai_suggestions)
    
    def _generate_ai_suggestions(self):
        """Generate AI suggestions using Gemini."""
        try:
            from app.modules.ai_copilot.gemini_integration import generate_with_gemini
            
            # Get upcoming events (today + next 3 days)
            today = date.today()
            upcoming_events = []
            
            for day_offset in range(4):  # Today + 3 days
                check_date = today + timedelta(days=day_offset)
                date_key = check_date.strftime('%Y-%m-%d')
                if date_key in self.events_cache:
                    for event in self.events_cache[date_key]:
                        event['date'] = check_date.strftime('%B %d, %Y')
                        upcoming_events.append(event)
            
            # Build prompt for AI
            events_text = "\n".join([
                f"- {e['date']}: {e.get('summary', 'Untitled')} at {e.get('start_time', 'TBD')}"
                for e in upcoming_events[:10]  # Limit to 10 events
            ])
            
            if not events_text:
                events_text = "No upcoming events in the next 3 days."
            
            prompt = f"""You are a productivity assistant analyzing the user's calendar.

**Upcoming Events (Today + Next 3 Days):**
{events_text}

**Task:**
1. Provide a brief summary of their schedule (2-3 sentences)
2. Suggest 2-3 time blocks for deep work or important tasks
3. For each suggestion, provide:
   - Recommended date and time
   - Duration (default 1 hour)
   - Activity type (Deep Work, Task Focus, Break, etc.)
   - Brief reason why this time is good

Format your response as:
SUMMARY: [brief schedule summary]

SUGGESTIONS:
1. [Date] at [Time] - [Activity] ([Duration])
   Reason: [why this is a good time]
2. [Date] at [Time] - [Activity] ([Duration])
   Reason: [why this is a good time]
"""
            
            # Get AI response
            response = generate_with_gemini(prompt)
            
            if response:
                # Parse and display suggestions
                self._display_ai_suggestions(response, upcoming_events)
            else:
                self._show_ai_error()
            
        except Exception as e:
            print(f"Error generating AI suggestions: {e}")
            self._show_ai_error()
    
    def _display_ai_suggestions(self, ai_response: str, upcoming_events: list):
        """Display AI suggestions in the panel."""
        # Clear loading message
        while self.ai_content_layout.count() > 0:
            item = self.ai_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Parse AI response
        parts = ai_response.split('SUGGESTIONS:')
        summary = parts[0].replace('SUMMARY:', '').strip()
        suggestions_text = parts[1].strip() if len(parts) > 1 else ""
        
        # Display summary
        summary_label = QLabel(f"📊 **Schedule Overview:**\n{summary}")
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("""
            background-color: #1e293b;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #3b82f6;
            color: #e2e8f0;
        """)
        self.ai_content_layout.addWidget(summary_label)
        
        # Parse and display suggestions
        suggestion_lines = [line.strip() for line in suggestions_text.split('\n') if line.strip() and line.strip()[0].isdigit()]
        
        for suggestion_line in suggestion_lines[:3]:  # Max 3 suggestions
            self._create_suggestion_card(suggestion_line)
        
        self.ai_content_layout.addStretch()
    
    def _create_suggestion_card(self, suggestion_text: str):
        """Create a suggestion card with Yes/No buttons."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 6px;
                border-left: 4px solid #10b981;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        # Parse suggestion
        suggestion_label = QLabel(suggestion_text)
        suggestion_label.setWordWrap(True)
        suggestion_label.setStyleSheet("color: #e2e8f0; font-size: 13px;")
        layout.addWidget(suggestion_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        yes_btn = QPushButton("✓ Create Event")
        yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        yes_btn.clicked.connect(lambda: self._approve_ai_suggestion(suggestion_text, card))
        
        no_btn = QPushButton("✗ Dismiss")
        no_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        no_btn.clicked.connect(lambda: card.deleteLater())
        
        button_layout.addWidget(yes_btn)
        button_layout.addWidget(no_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.ai_content_layout.addWidget(card)
    
    def _approve_ai_suggestion(self, suggestion_text: str, card_widget):
        """User approved AI suggestion - create the event."""
        # Parse suggestion to extract event details
        event_data = self._parse_ai_suggestion(suggestion_text)
        
        if event_data:
            # Show create dialog pre-filled with AI suggestion
            self._show_create_event_dialog(suggested_event=event_data)
            card_widget.deleteLater()
        else:
            QMessageBox.warning(self, "Parse Error", "Could not parse AI suggestion. Please create event manually.")
    
    def _parse_ai_suggestion(self, suggestion_text: str) -> dict:
        """Parse AI suggestion text into event data."""
        import re
        from datetime import datetime, timedelta
        
        # Try to extract date, time, activity, duration
        # Format: "Date at Time - Activity (Duration)"
        try:
            # This is a simple parser - AI should format consistently
            # Example: "January 28 at 2:00 PM - Deep Work (1 hour)"
            
            match = re.search(r'(\w+ \d+) at ([\d:]+\s*[AP]M)\s*-\s*(.+?)\s*\((.+?)\)', suggestion_text)
            if match:
                date_str, time_str, activity, duration_str = match.groups()
                
                # Parse date and time
                current_year = datetime.now().year
                dt_str = f"{date_str}, {current_year} {time_str}"
                start_dt = datetime.strptime(dt_str, "%B %d, %Y %I:%M %p")
                
                # Parse duration
                duration_hours = 1  # default
                if 'hour' in duration_str:
                    duration_match = re.search(r'(\d+)', duration_str)
                    if duration_match:
                        duration_hours = int(duration_match.group(1))
                
                end_dt = start_dt + timedelta(hours=duration_hours)
                
                return {
                    'title': activity,
                    'start_datetime': start_dt,
                    'end_datetime': end_dt,
                    'event_type': 'Work' if 'work' in activity.lower() else 'Other',
                    'description': f"AI-suggested: {suggestion_text}",
                }
        except Exception as e:
            print(f"Error parsing AI suggestion: {e}")
        
        return None
    
    def _show_ai_error(self):
        """Show error message in AI panel."""
        while self.ai_content_layout.count() > 0:
            item = self.ai_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        error_label = QLabel("⚠️ Could not generate suggestions.\nPlease try again later.")
        error_label.setWordWrap(True)
        error_label.setStyleSheet("color: #ef4444; padding: 8px;")
        self.ai_content_layout.addWidget(error_label)
        self.ai_content_layout.addStretch()


# ==================== Event Dialog ====================

class EventDialog(QDialog):
    """Dialog for creating/editing calendar events."""
    
    def __init__(self, parent=None, event_data: dict = None, edit_mode: bool = False, suggested_event: dict = None):
        super().__init__(parent)
        self.event_data = event_data or suggested_event
        self.edit_mode = edit_mode
        self.delete_requested = False
        
        self.setWindowTitle("Edit Event" if edit_mode else "Create Event")
        self.setMinimumWidth(500)
        self._setup_ui()
        
        if self.event_data:
            self._populate_fields()
    
    def _setup_ui(self):
        """Build dialog UI."""
        from PySide6.QtWidgets import QFormLayout, QComboBox, QDateTimeEdit, QTextEdit, QCheckBox
        from PySide6.QtCore import QDateTime
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Event Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter event title...")
        form_layout.addRow("Title *", self.title_input)
        
        # Event Type
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            '🔵 Meeting',
            '🟢 Task/Deadline',
            '🟡 Reminder',
            '🟣 Personal',
            '🔴 Work',
            '⚫ Other'
        ])
        form_layout.addRow("Type", self.type_combo)
        
        # Start Date & Time
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setCalendarPopup(True)
        self.start_datetime.setDateTime(QDateTime.currentDateTime())
        form_layout.addRow("Start", self.start_datetime)
        
        # End Date & Time
        self.end_datetime = QDateTimeEdit()
        self.end_datetime.setCalendarPopup(True)
        self.end_datetime.setDateTime(QDateTime.currentDateTime().addSecs(3600))  # +1 hour
        form_layout.addRow("End", self.end_datetime)
        
        # Location
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Optional")
        form_layout.addRow("Location", self.location_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Optional")
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Description", self.description_input)
        
        # Reminder
        self.reminder_combo = QComboBox()
        self.reminder_combo.addItems([
            'None',
            '5 minutes before',
            '15 minutes before',
            '30 minutes before',
            '1 hour before',
            '1 day before'
        ])
        self.reminder_combo.setCurrentIndex(2)  # Default: 15 min
        form_layout.addRow("Reminder", self.reminder_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        if self.edit_mode:
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #dc2626; }
            """)
            delete_btn.clicked.connect(self._on_delete_clicked)
            button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save" if self.edit_mode else "Create")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _populate_fields(self):
        """Populate fields with existing event data."""
        if not self.event_data:
            return
        
        # Title
        self.title_input.setText(self.event_data.get('title', self.event_data.get('summary', '')))
        
        # Type
        event_type = self.event_data.get('event_type', 'Other')
        type_map = {
            'Meeting': 0, 'Task/Deadline': 1, 'Reminder': 2,
            'Personal': 3, 'Work': 4, 'Other': 5
        }
        self.type_combo.setCurrentIndex(type_map.get(event_type, 5))
        
        # DateTime
        if 'start_datetime' in self.event_data:
            from PySide6.QtCore import QDateTime
            start_dt = self.event_data['start_datetime']
            self.start_datetime.setDateTime(QDateTime(start_dt.year, start_dt.month, start_dt.day,
                                                       start_dt.hour, start_dt.minute))
            end_dt = self.event_data.get('end_datetime', start_dt)
            self.end_datetime.setDateTime(QDateTime(end_dt.year, end_dt.month, end_dt.day,
                                                     end_dt.hour, end_dt.minute))
        
        # Location & Description
        self.location_input.setText(self.event_data.get('location', ''))
        self.description_input.setPlainText(self.event_data.get('description', ''))
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        self.delete_requested = True
        self.accept()
    
    def get_event_data(self) -> dict:
        """Get event data from form."""
        # Parse type
        type_text = self.type_combo.currentText()
        event_type = type_text.split(' ', 1)[1] if ' ' in type_text else 'Other'
        
        # Parse reminder
        reminder_text = self.reminder_combo.currentText()
        reminder_map = {
            'None': None,
            '5 minutes before': 5,
            '15 minutes before': 15,
            '30 minutes before': 30,
            '1 hour before': 60,
            '1 day before': 1440
        }
        
        return {
            'title': self.title_input.text(),
            'event_type': event_type,
            'start_datetime': self.start_datetime.dateTime().toPython(),
            'end_datetime': self.end_datetime.dateTime().toPython(),
            'location': self.location_input.text(),
            'description': self.description_input.toPlainText(),
            'reminder_minutes': reminder_map.get(reminder_text),
        }


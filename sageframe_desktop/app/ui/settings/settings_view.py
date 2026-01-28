"""Settings view for SageFrame desktop application.

Provides centralized settings management including:
- API Keys configuration (Gemini CLI, Gemini Vision, Google Books, Google Vision)
- Application preferences
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QFormLayout, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal

import keyring

# Keyring service names
GEMINI_KEYRING_SERVICE = "sageframe_gemini_cli"
GEMINI_KEY_NAME = "api_key"
GEMINI_VISION_KEYRING_SERVICE = "sageframe_gemini_vision"
GEMINI_VISION_KEY_NAME = "api_key"


class SettingsView(QWidget):
    """Main settings view with API keys and preferences.
    
    Signals:
        settingsSaved: Emitted when settings are saved
    """
    
    settingsSaved = Signal()
    
    def __init__(self, enrichment_service=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._enrichment_service = enrichment_service
        self._setup_ui()
        self._load_existing_keys()
    
    def _setup_ui(self):
        """Build the settings view UI."""
        self.setObjectName("settingsView")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # Title
        title = QLabel("⚙️ Settings")
        title.setObjectName("settingsTitle")
        title.setStyleSheet("""
            QLabel#settingsTitle {
                font-size: 24px;
                font-weight: bold;
                color: #c69749;
                padding: 0 0 12px 0;
            }
        """)
        main_layout.addWidget(title)
        
        # Scrollable area for settings content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # API Keys Section
        api_keys_group = self._create_api_keys_section()
        content_layout.addWidget(api_keys_group)
        
        # Add spacer to push content to top
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Save button at bottom
        save_button = QPushButton("💾 Save Settings")
        save_button.setMinimumHeight(40)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #c69749;
                color: #1e1e1e;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d4a84e;
            }
            QPushButton:pressed {
                background-color: #b58738;
            }
        """)
        save_button.clicked.connect(self._save_settings)
        main_layout.addWidget(save_button)
    
    def _create_api_keys_section(self) -> QGroupBox:
        """Create the API Keys configuration section."""
        group_box = QGroupBox("🔑 API Keys")
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #d4d4d4;
                border: 2px solid #3e3e3e;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        
        layout = QVBoxLayout(group_box)
        layout.setSpacing(16)
        
        # Info label
        info_label = QLabel("API keys are stored securely using your system's keyring.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-size: 12px; font-weight: normal; padding: 0 8px;")
        layout.addWidget(info_label)
        
        # Form for API keys
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # Style for form labels
        label_style = "color: #d4d4d4; font-weight: normal; font-size: 13px;"
        
        # Gemini CLI API Key
        self.gemini_cli_field = QLineEdit()
        self.gemini_cli_field.setPlaceholderText("Enter Gemini CLI API key")
        self.gemini_cli_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_cli_field.setMinimumWidth(400)
        self.gemini_cli_field.setStyleSheet(self._get_field_style())
        
        gemini_cli_label = QLabel("Gemini CLI:")
        gemini_cli_label.setStyleSheet(label_style)
        form.addRow(gemini_cli_label, self.gemini_cli_field)
        
        # Show/Hide button for Gemini CLI
        gemini_cli_layout = QHBoxLayout()
        gemini_cli_layout.addWidget(self.gemini_cli_field)
        gemini_cli_toggle = QPushButton("👁️")
        gemini_cli_toggle.setFixedSize(32, 32)
        gemini_cli_toggle.setStyleSheet(self._get_toggle_button_style())
        gemini_cli_toggle.clicked.connect(lambda: self._toggle_password_visibility(self.gemini_cli_field))
        gemini_cli_layout.addWidget(gemini_cli_toggle)
        form.addRow(gemini_cli_label, gemini_cli_layout)
        
        # Gemini Vision API Key
        self.gemini_vision_field = QLineEdit()
        self.gemini_vision_field.setPlaceholderText("Enter Gemini Vision API key")
        self.gemini_vision_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_vision_field.setMinimumWidth(400)
        self.gemini_vision_field.setStyleSheet(self._get_field_style())
        
        gemini_vision_label = QLabel("Gemini Vision:")
        gemini_vision_label.setStyleSheet(label_style)
        
        # Show/Hide button for Gemini Vision
        gemini_vision_layout = QHBoxLayout()
        gemini_vision_layout.addWidget(self.gemini_vision_field)
        gemini_vision_toggle = QPushButton("👁️")
        gemini_vision_toggle.setFixedSize(32, 32)
        gemini_vision_toggle.setStyleSheet(self._get_toggle_button_style())
        gemini_vision_toggle.clicked.connect(lambda: self._toggle_password_visibility(self.gemini_vision_field))
        gemini_vision_layout.addWidget(gemini_vision_toggle)
        form.addRow(gemini_vision_label, gemini_vision_layout)
        
        # Google Books API Key
        self.google_books_field = QLineEdit()
        self.google_books_field.setPlaceholderText("Enter Google Books API key")
        self.google_books_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.google_books_field.setMinimumWidth(400)
        self.google_books_field.setStyleSheet(self._get_field_style())
        
        google_books_label = QLabel("Google Books:")
        google_books_label.setStyleSheet(label_style)
        
        # Show/Hide button for Google Books
        google_books_layout = QHBoxLayout()
        google_books_layout.addWidget(self.google_books_field)
        google_books_toggle = QPushButton("👁️")
        google_books_toggle.setFixedSize(32, 32)
        google_books_toggle.setStyleSheet(self._get_toggle_button_style())
        google_books_toggle.clicked.connect(lambda: self._toggle_password_visibility(self.google_books_field))
        google_books_layout.addWidget(google_books_toggle)
        form.addRow(google_books_label, google_books_layout)
        
        # Google Vision API Key
        self.google_vision_field = QLineEdit()
        self.google_vision_field.setPlaceholderText("Enter Google Vision API key")
        self.google_vision_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.google_vision_field.setMinimumWidth(400)
        self.google_vision_field.setStyleSheet(self._get_field_style())
        
        google_vision_label = QLabel("Google Vision:")
        google_vision_label.setStyleSheet(label_style)
        
        # Show/Hide button for Google Vision
        google_vision_layout = QHBoxLayout()
        google_vision_layout.addWidget(self.google_vision_field)
        google_vision_toggle = QPushButton("👁️")
        google_vision_toggle.setFixedSize(32, 32)
        google_vision_toggle.setStyleSheet(self._get_toggle_button_style())
        google_vision_toggle.clicked.connect(lambda: self._toggle_password_visibility(self.google_vision_field))
        google_vision_layout.addWidget(google_vision_toggle)
        form.addRow(google_vision_label, google_vision_layout)
        
        layout.addLayout(form)
        
        # Help text
        help_text = QLabel(
            "💡 <b>Getting API Keys:</b><br>"
            "• Gemini CLI & Vision: <a href='https://makersuite.google.com/app/apikey' style='color: #c69749;'>Get from Google AI Studio</a><br>"
            "• Google Books: <a href='https://console.cloud.google.com/apis/credentials' style='color: #c69749;'>Get from Google Cloud Console</a><br>"
            "• Google Vision: <a href='https://console.cloud.google.com/apis/credentials' style='color: #c69749;'>Get from Google Cloud Console</a>"
        )
        help_text.setOpenExternalLinks(True)
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #888; font-size: 12px; font-weight: normal; padding: 8px; background: rgba(198, 151, 73, 0.1); border-radius: 4px;")
        layout.addWidget(help_text)
        
        return group_box
    
    def _get_field_style(self) -> str:
        """Get stylesheet for input fields."""
        return """
            QLineEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 2px solid #3e3e3e;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #c69749;
            }
            QLineEdit::placeholder {
                color: #666;
            }
        """
    
    def _get_toggle_button_style(self) -> str:
        """Get stylesheet for show/hide toggle buttons."""
        return """
            QPushButton {
                background-color: #3e3e3e;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4e4e4e;
            }
            QPushButton:pressed {
                background-color: #2e2e2e;
            }
        """
    
    def _toggle_password_visibility(self, field: QLineEdit):
        """Toggle password visibility for a field."""
        if field.echoMode() == QLineEdit.EchoMode.Password:
            field.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            field.setEchoMode(QLineEdit.EchoMode.Password)
    
    def _load_existing_keys(self):
        """Load existing API keys from keyring."""
        try:
            # Gemini CLI
            gemini_cli_key = keyring.get_password(GEMINI_KEYRING_SERVICE, GEMINI_KEY_NAME)
            if gemini_cli_key:
                self.gemini_cli_field.setText(gemini_cli_key)
        except Exception:
            pass
        
        try:
            # Gemini Vision
            gemini_vision_key = keyring.get_password(GEMINI_VISION_KEYRING_SERVICE, GEMINI_VISION_KEY_NAME)
            if gemini_vision_key:
                self.gemini_vision_field.setText(gemini_vision_key)
        except Exception:
            pass
        
        try:
            # Google Books
            if self._enrichment_service:
                google_books_key = self._enrichment_service.get_api_key("google_books")
                if google_books_key:
                    self.google_books_field.setText(google_books_key)
        except Exception:
            pass
        
        try:
            # Google Vision
            google_vision_key = keyring.get_password("sageframe_file_ingestion", "google_vision")
            if google_vision_key:
                self.google_vision_field.setText(google_vision_key)
        except Exception:
            pass
    
    def _save_settings(self):
        """Save all settings to keyring."""
        try:
            # Save Gemini CLI API key
            gemini_cli_key = self.gemini_cli_field.text().strip()
            if gemini_cli_key:
                keyring.set_password(GEMINI_KEYRING_SERVICE, GEMINI_KEY_NAME, gemini_cli_key)
            
            # Save Gemini Vision API key
            gemini_vision_key = self.gemini_vision_field.text().strip()
            if gemini_vision_key:
                keyring.set_password(GEMINI_VISION_KEYRING_SERVICE, GEMINI_VISION_KEY_NAME, gemini_vision_key)
            
            # Save Google Books API key via enrichment service
            google_books_key = self.google_books_field.text().strip()
            if google_books_key and self._enrichment_service:
                self._enrichment_service.set_api_key("google_books", google_books_key)
            
            # Save Google Vision API key
            google_vision_key = self.google_vision_field.text().strip()
            if google_vision_key:
                keyring.set_password("sageframe_file_ingestion", "google_vision", google_vision_key)
            
            # Show success message
            QMessageBox.information(
                self,
                "Settings Saved",
                "✅ API keys have been saved successfully!"
            )
            
            # Emit signal
            self.settingsSaved.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Settings",
                f"❌ Failed to save settings:\n{str(e)}"
            )

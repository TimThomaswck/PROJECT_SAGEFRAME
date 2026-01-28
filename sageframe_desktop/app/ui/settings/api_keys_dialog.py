"""Dialog for configuring API keys for integrations.

Provides fields for:
- Google Books API key (used by tag enrichment)
- Gemini CLI API key (Epic 1.4; stored for later use)
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QLabel
)
from PySide6.QtCore import Qt, Signal

import keyring

# Separate keyring service for Gemini CLI
GEMINI_KEYRING_SERVICE = "sageframe_gemini_cli"
GEMINI_KEY_NAME = "api_key"


class ApiKeysDialog(QDialog):
    # Signal emitted when API keys are saved
    settingsSaved = Signal()
    
    def __init__(self, enrichment_service=None, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.setWindowTitle("API Keys")
        self.setMinimumWidth(420)

        self._enrichment_service = enrichment_service

        layout = QVBoxLayout(self)
        info = QLabel("Keys are stored securely using the system keyring.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #666;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Google Books API key
        self.google_books_field = QLineEdit()
        self.google_books_field.setPlaceholderText("Enter Google Books API key")
        form.addRow("Google Books:", self.google_books_field)

        # Google Vision API key
        self.gvision_field = QLineEdit()
        self.gvision_field.setPlaceholderText("Enter Google Vision API key")
        form.addRow("Google Vision:", self.gvision_field)

        # Gemini CLI API key
        self.gemini_field = QLineEdit()
        self.gemini_field.setPlaceholderText("Enter Gemini CLI API key")
        self.gemini_field.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Gemini CLI:", self.gemini_field)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Prefill existing values when available
        self._prefill()

    def _prefill(self):
        # Google Books
        try:
            if self._enrichment_service:
                existing_gb = self._enrichment_service.get_api_key("google_books")
                if existing_gb:
                    self.google_books_field.setText(existing_gb)
        except Exception:
            pass

        # Google Vision
        try:
            existing_gv = keyring.get_password("sageframe_file_ingestion", "google_vision")
            if existing_gv:
                self.gvision_field.setText(existing_gv)
        except Exception:
            pass

        # Gemini CLI
        try:
            existing_gemini = keyring.get_password(GEMINI_KEYRING_SERVICE, GEMINI_KEY_NAME)
            if existing_gemini:
                self.gemini_field.setText(existing_gemini)
        except Exception:
            pass

    def _on_save(self):
        # Save Google Books API key via enrichment service
        gb_key = self.google_books_field.text().strip()
        if gb_key and self._enrichment_service:
            try:
                self._enrichment_service.set_api_key("google_books", gb_key)
            except Exception:
                # Ignore errors but keep dialog flow clean
                pass

        # Save Google Vision API key via keyring
        gv_key = self.gvision_field.text().strip()
        if gv_key:
            try:
                keyring.set_password("sageframe_file_ingestion", "google_vision", gv_key)
            except Exception:
                pass

        # Save Gemini CLI API key via keyring
        gemini_key = self.gemini_field.text().strip()
        if gemini_key:
            try:
                keyring.set_password(GEMINI_KEYRING_SERVICE, GEMINI_KEY_NAME, gemini_key)
            except Exception:
                pass

        # Emit signal to notify that settings have been saved
        self.settingsSaved.emit()
        self.accept()

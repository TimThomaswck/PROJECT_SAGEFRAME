"""UI views for notes management with Google Keep-style tile layout."""

from typing import Optional, List
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QDialog, QScrollArea, QFrame,
    QGridLayout, QComboBox, QMessageBox, QMenu, QToolButton
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor

from app.modules.notes.view_models import NotesViewModel
from app.modules.notes.models import Note, NoteColor


class NoteCard(QFrame):
    """Individual note card in tile layout (Google Keep style).
    
    Signals:
        clicked: Emitted when card is clicked
        pin_toggled: Emitted when pin button is clicked
        color_changed: Emitted when color is changed
        delete_requested: Emitted when delete is requested
    """
    
    clicked = Signal(int)  # note_id
    pin_toggled = Signal(int)  # note_id
    color_changed = Signal(int, str)  # note_id, color
    delete_requested = Signal(int)  # note_id
    
    def __init__(self, note: Note, parent=None):
        super().__init__(parent)
        self.note = note
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the card UI."""
        self.setObjectName("noteCard")
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(200)
        self.setMaximumWidth(300)
        self.setMinimumHeight(150)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header with title and pin button
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.note.title)
        title_label.setObjectName("noteCardTitle")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(60)
        header_layout.addWidget(title_label, stretch=1)
        
        # Pin button
        self.pin_btn = QPushButton("📌" if self.note.is_pinned else "📍")
        self.pin_btn.setObjectName("notePinButton")
        self.pin_btn.setFixedSize(24, 24)
        self.pin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pin_btn.clicked.connect(lambda: self.pin_toggled.emit(self.note.id))
        header_layout.addWidget(self.pin_btn)
        
        layout.addLayout(header_layout)
        
        # Content preview (markdown rendered as plain text for now)
        if self.note.content:
            content_label = QLabel(self._get_preview_text())
            content_label.setObjectName("noteCardContent")
            content_label.setWordWrap(True)
            content_label.setMaximumHeight(100)
            content_label.setStyleSheet("color: #888;")
            layout.addWidget(content_label)
        
        layout.addStretch()
        
        # Color indicator at bottom
        color_indicator = QFrame()
        color_indicator.setFixedHeight(4)
        color_indicator.setStyleSheet(f"background-color: {self._get_color_hex()};")
        layout.addWidget(color_indicator)
        
        # Apply color to card background
        self._apply_card_color()
    
    def _get_preview_text(self) -> str:
        """Get preview text from content (first 150 chars)."""
        if not self.note.content:
            return ""
        # Remove markdown syntax for preview
        text = re.sub(r'[#*`\[\]()]', '', self.note.content)
        return text[:150] + "..." if len(text) > 150 else text
    
    def _get_color_hex(self) -> str:
        """Get hex color code for note color."""
        color_map = {
            "default": "#ffffff",
            "red": "#f28b82",
            "orange": "#fbbc04",
            "yellow": "#fff475",
            "green": "#ccff90",
            "teal": "#a7ffeb",
            "blue": "#cbf0f8",
            "purple": "#d7aefb",
            "pink": "#fdcfe8",
            "brown": "#e6c9a8",
            "gray": "#e8eaed"
        }
        return color_map.get(self.note.color, "#ffffff")
    
    def _apply_card_color(self):
        """Apply background color to card."""
        bg_color = self._get_color_hex()
        # Determine text color based on background brightness
        text_color = "#000000" if self.note.color in ["yellow", "default"] else "#1a1a1a"
        
        self.setStyleSheet(f"""
            QFrame#noteCard {{
                background-color: {bg_color};
                border: 1px solid #d0d0d0;
                border-radius: 8px;
            }}
            QFrame#noteCard:hover {{
                border: 1px solid #999;
            }}
            QLabel#noteCardTitle {{
                color: {text_color};
            }}
            QPushButton#notePinButton {{
                background: transparent;
                border: none;
                font-size: 16px;
            }}
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse click on card."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.note.id)
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
        """Show context menu on right-click."""
        menu = QMenu(self)
        
        # Color submenu
        color_menu = menu.addMenu("🎨 Change Color")
        for color in NoteColor:
            action = color_menu.addAction(color.value.title())
            action.triggered.connect(lambda checked, c=color.value: self.color_changed.emit(self.note.id, c))
        
        menu.addSeparator()
        
        # Archive action
        archive_action = menu.addAction("📦 Archive" if not self.note.is_archived else "📤 Unarchive")
        archive_action.triggered.connect(lambda: self.color_changed.emit(self.note.id, "archive"))
        
        # Delete action
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.note.id))
        
        menu.exec(event.globalPos())


class NoteEditorDialog(QDialog):
    """Dialog for creating or editing a note with markdown support."""
    
    def __init__(self, view_model: NotesViewModel, note_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.view_model = view_model
        self.note_id = note_id
        self.note = view_model.get_note(note_id) if note_id else None
        self._setup_ui()
        if self.note:
            self._load_note_data()
    
    def _setup_ui(self):
        """Build the editor dialog UI."""
        self.setWindowTitle("Edit Note" if self.note else "New Note")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Title input
        title_label = QLabel("Title:")
        title_label.setObjectName("noteTitleLabel")
        self.title_input = QLineEdit()
        self.title_input.setObjectName("noteTitleInput")
        self.title_input.setPlaceholderText("Note title...")
        layout.addWidget(title_label)
        layout.addWidget(self.title_input)
        
        # Toolbar for markdown helpers
        toolbar_layout = QHBoxLayout()
        
        # Markdown formatting buttons
        bold_btn = QPushButton("**B**")
        bold_btn.setToolTip("Bold")
        bold_btn.clicked.connect(lambda: self._insert_markdown("**", "**"))
        toolbar_layout.addWidget(bold_btn)
        
        italic_btn = QPushButton("*I*")
        italic_btn.setToolTip("Italic")
        italic_btn.clicked.connect(lambda: self._insert_markdown("*", "*"))
        toolbar_layout.addWidget(italic_btn)
        
        link_btn = QPushButton("🔗")
        link_btn.setToolTip("Insert Link [[Note Title]]")
        link_btn.clicked.connect(lambda: self._insert_markdown("[[", "]]"))
        toolbar_layout.addWidget(link_btn)
        
        code_btn = QPushButton("`<>`")
        code_btn.setToolTip("Code")
        code_btn.clicked.connect(lambda: self._insert_markdown("`", "`"))
        toolbar_layout.addWidget(code_btn)
        
        heading_btn = QPushButton("H")
        heading_btn.setToolTip("Heading")
        heading_btn.clicked.connect(lambda: self._insert_markdown("## ", ""))
        toolbar_layout.addWidget(heading_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Content editor
        content_label = QLabel("Content (Markdown):")
        content_label.setObjectName("noteContentLabel")
        self.content_input = QTextEdit()
        self.content_input.setObjectName("noteContentInput")
        self.content_input.setPlaceholderText("Write your note in markdown...\n\nUse [[Note Title]] to create backlinks to other notes.")
        layout.addWidget(content_label)
        layout.addWidget(self.content_input, stretch=1)
        
        # Color picker
        color_layout = QHBoxLayout()
        color_label = QLabel("Color:")
        self.color_combo = QComboBox()
        self.color_combo.setObjectName("noteColorCombo")
        for color in NoteColor:
            self.color_combo.addItem(color.value.title(), color.value)
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_combo)
        color_layout.addStretch()
        
        # Pin checkbox button
        self.pin_btn = QPushButton("📌 Pin")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setObjectName("notePinToggle")
        color_layout.addWidget(self.pin_btn)
        
        layout.addLayout(color_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("saveNoteButton")
        self.save_btn.clicked.connect(self._on_save)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _load_note_data(self):
        """Load existing note data into fields."""
        if not self.note:
            return
        
        self.title_input.setText(self.note.title)
        self.content_input.setPlainText(self.note.content or "")
        
        # Set color
        color_index = self.color_combo.findData(self.note.color)
        if color_index >= 0:
            self.color_combo.setCurrentIndex(color_index)
        
        self.pin_btn.setChecked(bool(self.note.is_pinned))
    
    def _insert_markdown(self, prefix: str, suffix: str):
        """Insert markdown syntax around selected text."""
        cursor = self.content_input.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"{prefix}{selected_text}{suffix}")
        else:
            cursor.insertText(f"{prefix}{suffix}")
            # Move cursor between prefix and suffix
            for _ in suffix:
                cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.content_input.setTextCursor(cursor)
    
    def _on_save(self):
        """Handle save button click."""
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Invalid Input", "Please enter a note title.")
            return
        
        content = self.content_input.toPlainText()
        color = self.color_combo.currentData()
        is_pinned = self.pin_btn.isChecked()
        
        if self.note_id:
            # Update existing note
            success = self.view_model.update_note(
                self.note_id,
                title=title,
                content=content,
                color=color,
                is_pinned=is_pinned
            )
        else:
            # Create new note
            note_id = self.view_model.create_note(
                title=title,
                content=content,
                color=color,
                is_pinned=is_pinned
            )
            success = note_id is not None
        
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save note.")


class NotesView(QWidget):
    """Main notes view with Google Keep-style tile layout."""
    
    def __init__(self, view_model: NotesViewModel, parent=None):
        super().__init__(parent)
        self.view_model = view_model
        self._setup_ui()
        self._connect_signals()
        self._load_notes()
    
    def _setup_ui(self):
        """Build the notes view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header with search and new note button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Notes")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setObjectName("notesSearchInput")
        self.search_input.setPlaceholderText("🔍 Search notes...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)
        
        header_layout.addStretch()
        
        # New note button
        new_note_btn = QPushButton("➕ New Note")
        new_note_btn.setObjectName("newNoteButton")
        new_note_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_note_btn.clicked.connect(self._on_create_note)
        header_layout.addWidget(new_note_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Refresh")
        refresh_btn.clicked.connect(self._load_notes)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Scroll area for notes tiles
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("notesScrollArea")
        
        # Container for note cards
        self.notes_container = QWidget()
        self.notes_layout = QGridLayout(self.notes_container)
        self.notes_layout.setSpacing(16)
        self.notes_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll_area.setWidget(self.notes_container)
        layout.addWidget(scroll_area)
    
    def _connect_signals(self):
        """Connect view model signals."""
        self.view_model.note_created.connect(lambda: self._load_notes())
        self.view_model.note_updated.connect(lambda: self._load_notes())
        self.view_model.note_deleted.connect(lambda: self._load_notes())
        self.view_model.error_occurred.connect(self._on_error)
    
    def _load_notes(self):
        """Load and display notes in tile layout."""
        # Clear existing cards
        while self.notes_layout.count():
            item = self.notes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get notes
        notes = self.view_model.list_notes()
        
        if not notes:
            # Show empty state
            empty_label = QLabel("No notes yet. Click '➕ New Note' to create one!")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #888; font-size: 16px; padding: 40px;")
            self.notes_layout.addWidget(empty_label, 0, 0)
            return
        
        # Add note cards in grid layout (3 columns)
        columns = 3
        for index, note in enumerate(notes):
            row = index // columns
            col = index % columns
            
            card = NoteCard(note, self)
            card.clicked.connect(self._on_note_clicked)
            card.pin_toggled.connect(self._on_pin_toggled)
            card.color_changed.connect(self._on_color_changed)
            card.delete_requested.connect(self._on_delete_requested)
            
            self.notes_layout.addWidget(card, row, col)
    
    @Slot()
    def _on_create_note(self):
        """Open dialog to create a new note."""
        dialog = NoteEditorDialog(self.view_model, parent=self)
        dialog.exec()
    
    @Slot(int)
    def _on_note_clicked(self, note_id: int):
        """Open note editor when card is clicked."""
        dialog = NoteEditorDialog(self.view_model, note_id, parent=self)
        dialog.exec()
    
    @Slot(int)
    def _on_pin_toggled(self, note_id: int):
        """Toggle pin status of a note."""
        self.view_model.toggle_pin(note_id)
    
    @Slot(int, str)
    def _on_color_changed(self, note_id: int, color: str):
        """Handle color change or archive."""
        if color == "archive":
            self.view_model.toggle_archive(note_id)
        else:
            self.view_model.update_note(note_id, color=color)
    
    @Slot(int)
    def _on_delete_requested(self, note_id: int):
        """Handle delete request with confirmation."""
        reply = QMessageBox.question(
            self,
            "Delete Note",
            "Are you sure you want to delete this note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.view_model.delete_note(note_id)
    
    @Slot()
    def _on_search(self):
        """Handle search input change."""
        query = self.search_input.text().strip()
        
        # Clear existing cards
        while self.notes_layout.count():
            item = self.notes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get filtered notes
        if query:
            notes = self.view_model.search_notes(query)
        else:
            notes = self.view_model.list_notes()
        
        if not notes:
            empty_label = QLabel("No notes found." if query else "No notes yet.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #888; font-size: 16px; padding: 40px;")
            self.notes_layout.addWidget(empty_label, 0, 0)
            return
        
        # Display filtered notes
        columns = 3
        for index, note in enumerate(notes):
            row = index // columns
            col = index % columns
            
            card = NoteCard(note, self)
            card.clicked.connect(self._on_note_clicked)
            card.pin_toggled.connect(self._on_pin_toggled)
            card.color_changed.connect(self._on_color_changed)
            card.delete_requested.connect(self._on_delete_requested)
            
            self.notes_layout.addWidget(card, row, col)
    
    @Slot(str)
    def _on_error(self, error_message: str):
        """Handle error from view model."""
        QMessageBox.critical(self, "Error", error_message)

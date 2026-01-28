"""Quick add dialogs for tasks and notes from dashboard."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
    QPushButton, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont


class QuickAddTaskDialog(QDialog):
    """Quick add task dialog."""
    
    task_created = Signal(str, str, QDate)  # title, priority, due_date
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Add Task")
        self.setFixedSize(400, 320)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title_label = QLabel("Task Title")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter task title...")
        self.title_input.setMinimumHeight(36)
        layout.addWidget(self.title_input)
        
        # Priority
        priority_label = QLabel("Priority")
        priority_label.setFont(title_font)
        layout.addWidget(priority_label)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        self.priority_combo.setMinimumHeight(36)
        layout.addWidget(self.priority_combo)
        
        # Due Date
        date_label = QLabel("Due Date")
        date_label.setFont(title_font)
        layout.addWidget(date_label)
        
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setMinimumHeight(36)
        layout.addWidget(self.date_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Task")
        create_btn.setFixedWidth(120)
        create_btn.setStyleSheet("""
            QPushButton {
                background: #c69749;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #d4a870;
            }
        """)
        create_btn.clicked.connect(self._create_task)
        button_layout.addWidget(create_btn)
        
        layout.addStretch()
        layout.addLayout(button_layout)
        
        # Focus on title input
        self.title_input.setFocus()
    
    def _create_task(self):
        """Create task and close dialog."""
        title = self.title_input.text().strip()
        if not title:
            return
        
        priority = self.priority_combo.currentText()
        due_date = self.date_input.date()
        self.task_created.emit(title, priority, due_date)
        self.accept()


class QuickAddNoteDialog(QDialog):
    """Quick add note dialog."""
    
    note_created = Signal(str, str)  # title, content
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Add Note")
        self.setFixedSize(450, 350)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title_label = QLabel("Note Title")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter note title...")
        self.title_input.setMinimumHeight(36)
        layout.addWidget(self.title_input)
        
        # Content
        content_label = QLabel("Content")
        content_label.setFont(title_font)
        layout.addWidget(content_label)
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Enter note content (supports markdown)...")
        layout.addWidget(self.content_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Note")
        create_btn.setFixedWidth(120)
        create_btn.setStyleSheet("""
            QPushButton {
                background: #c69749;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #d4a870;
            }
        """)
        create_btn.clicked.connect(self._create_note)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
        # Focus on title input
        self.title_input.setFocus()
    
    def _create_note(self):
        """Create note and close dialog."""
        title = self.title_input.text().strip()
        if not title:
            return
        
        content = self.content_input.toPlainText().strip()
        self.note_created.emit(title, content)
        self.accept()

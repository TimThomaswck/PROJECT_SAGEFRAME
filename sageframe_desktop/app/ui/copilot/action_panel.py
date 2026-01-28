"""Co-pilot action panel with 6 action buttons and response area."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import Optional, List, Callable


class CopilotActionPanel(QWidget):
    """Central co-pilot panel with action buttons and response display area.
    
    Signals:
        actionTriggered: Emitted when user clicks an action button.
                        Payload: action_name (str)
    """
    
    # Action names
    ACTION_CALENDAR = "calendar"
    ACTION_NOTES = "notes"
    ACTION_SUGGESTIONS = "suggestions"
    ACTION_PROGRESS = "progress"
    ACTION_HABITS = "habits"
    ACTION_MOOD = "mood"
    
    actionTriggered = Signal(str)
    responseButtonClicked = Signal(str, str)  # message_id, button_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the action panel layout."""
        self.setObjectName("copilotActionPanel")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("SageFrame Assistant")
        header_font = QFont("Arial", 14, QFont.Weight.Bold)
        header.setFont(header_font)
        header.setStyleSheet("color: #c69749;")
        layout.addWidget(header)
        
        # Action buttons area
        buttons_widget = self._create_action_buttons()
        layout.addWidget(buttons_widget)
        
        # Response area (scrollable)
        self.response_area = self._create_response_area()
        layout.addWidget(self.response_area, stretch=1)
    
    def _create_action_buttons(self) -> QWidget:
        """Create grid of 6 action buttons."""
        container = QWidget()
        container.setObjectName("actionButtonsContainer")
        
        grid_layout = QHBoxLayout(container)
        grid_layout.setSpacing(8)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        actions = [
            (self.ACTION_CALENDAR, "📅 Calendar", "#60a5fa"),
            (self.ACTION_NOTES, "📝 Notes", "#4ade80"),
            (self.ACTION_SUGGESTIONS, "💡 Suggest", "#fbbf24"),
            (self.ACTION_PROGRESS, "📊 Progress", "#c69749"),
            (self.ACTION_HABITS, "🎯 Habits", "#f87171"),
            (self.ACTION_MOOD, "😊 Mood", "#8b5cf6"),
        ]
        
        for action_id, label, color in actions:
            btn = self._create_action_button(action_id, label, color)
            grid_layout.addWidget(btn)
        
        return container
    
    def _create_action_button(self, action_id: str, label: str, color: str) -> QPushButton:
        """Create a single action button."""
        btn = QPushButton(label)
        btn.setObjectName(f"actionButton_{action_id}")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(50)
        btn.clicked.connect(lambda: self._on_action_clicked(action_id))
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(45, 45, 45, 0.8);
                color: {color};
                border: 2px solid {color};
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 12px 16px;
            }}
            QPushButton:hover {{
                background: rgba({self._hex_to_rgb(color)[0]}, {self._hex_to_rgb(color)[1]}, {self._hex_to_rgb(color)[2]}, 0.15);
                border: 2px solid {color};
            }}
            QPushButton:pressed {{
                background: rgba({self._hex_to_rgb(color)[0]}, {self._hex_to_rgb(color)[1]}, {self._hex_to_rgb(color)[2]}, 0.25);
            }}
        """)
        
        return btn
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _on_action_clicked(self, action_id: str):
        """Handle action button click."""
        self.actionTriggered.emit(action_id)
    
    def _create_response_area(self) -> QWidget:
        """Create the response display area."""
        container = QFrame()
        container.setObjectName("responseAreaFrame")
        container.setStyleSheet("""
            QFrame#responseAreaFrame {
                background: #1e1e1e;
                border: 1px solid #3e3e3e;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)
        
        # Scroll area for messages
        scroll = QScrollArea()
        scroll.setObjectName("responseScroll")
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
        """)
        
        # Content widget for scroll area
        content = QWidget()
        content.setObjectName("responseContent")
        self.response_layout = QVBoxLayout(content)
        self.response_layout.setSpacing(12)
        self.response_layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder text
        self.placeholder_label = QLabel("Select an action above to get started...")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 14px;
                padding: 40px 20px;
            }
        """)
        self.response_layout.addWidget(self.placeholder_label)
        self.response_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return container
    
    def display_message(self, message_text: str, message_id: str = None, auto_dismiss: bool = False, 
                       response_buttons: Optional[List[dict]] = None):
        """Display a message in the response area with optional response buttons.
        
        Args:
            message_text: The message text to display
            message_id: Unique ID for the message
            auto_dismiss: Whether to auto-dismiss the message
            response_buttons: List of button configs [{"id": str, "text": str, "icon": str, "callback": callable}]
        """
        # Remove placeholder if present and still valid
        try:
            if self.placeholder_label and self.placeholder_label.parent():
                self.response_layout.removeWidget(self.placeholder_label)
                self.placeholder_label.setParent(None)
        except RuntimeError:
            # Label already deleted; ignore
            pass
        
        # Create message widget with response buttons
        message_widget = self._create_message_widget(message_text, message_id, response_buttons)
        self.response_layout.insertWidget(0, message_widget)
        
        # Add stretch at end to keep messages at top
        if self.response_layout.itemAt(self.response_layout.count() - 1).widget() is None:
            self.response_layout.removeItem(self.response_layout.itemAt(self.response_layout.count() - 1))
        self.response_layout.addStretch()
    
    def _create_message_widget(self, message_text: str, message_id: str, 
                               response_buttons: Optional[List[dict]] = None) -> QFrame:
        """Create a message display widget with optional response buttons."""
        widget = QFrame()
        widget.setObjectName(f"messageWidget_{message_id}")
        widget.setStyleSheet("""
            QFrame {
                background: rgba(198, 151, 73, 0.1);
                border-left: 3px solid #c69749;
                border-radius: 4px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Message text
        text_label = QLabel(message_text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #d4d4d4; font-size: 13px; line-height: 1.5;")
        layout.addWidget(text_label)
        
        # Response buttons (if provided) - show inside the message box
        if response_buttons and len(response_buttons) > 0:
            buttons_layout = QHBoxLayout()
            buttons_layout.setSpacing(8)
            buttons_layout.setContentsMargins(0, 8, 0, 0)
            
            for i, btn_config in enumerate(response_buttons):
                btn = QPushButton(f"{btn_config.get('icon', '')} {btn_config['text']}")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setMinimumHeight(32)
                btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(198, 151, 73, 0.3);
                        color: #e8d4a0;
                        border: 1px solid rgba(198, 151, 73, 0.5);
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-size: 12px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background: rgba(198, 151, 73, 0.4);
                        border-color: #c69749;
                        color: #ffffff;
                    }
                    QPushButton:pressed {
                        background: rgba(198, 151, 73, 0.5);
                    }
                """)
                
                # Connect to callback with proper closure capture
                callback = btn_config.get('callback')
                button_id = btn_config.get('id', btn_config['text'].lower().replace(' ', '_'))
                
                # Create proper closure function
                def make_handler(cb, w, mid):
                    def handler():
                        if cb:
                            cb()
                        self._dismiss_message(w, mid)
                    return handler
                
                btn.clicked.connect(make_handler(callback, widget, message_id))
                buttons_layout.addWidget(btn)
            
            buttons_layout.addStretch()
            layout.addLayout(buttons_layout)
        
        # Simple dismiss link at bottom
        dismiss_btn = QPushButton("✕ Dismiss")
        dismiss_btn.setMaximumWidth(100)
        dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                border: none;
                font-size: 11px;
                padding: 4px 8px;
                text-align: left;
            }
            QPushButton:hover {
                color: #aaa;
            }
        """)
        dismiss_btn.clicked.connect(lambda: self._dismiss_message(widget, message_id))
        layout.addWidget(dismiss_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        return widget
    
    def _dismiss_message(self, widget: QFrame, message_id: str):
        """Remove a message widget."""
        widget.deleteLater()
        
        # If no more messages, show placeholder again
        if self.response_layout.count() <= 1:  # Only stretch left
            self.placeholder_label = QLabel("Select an action above to get started...")
            self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.placeholder_label.setStyleSheet("""
                QLabel {
                    color: #888;
                    font-size: 14px;
                    padding: 40px 20px;
                }
            """)
            self.response_layout.insertWidget(0, self.placeholder_label)
    
    def clear_messages(self):
        """Clear all messages from the response area."""
        while self.response_layout.count() > 1:  # Keep the stretch
            item = self.response_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

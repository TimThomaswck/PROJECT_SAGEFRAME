"""UI components for suggestion presentation and interaction.

Implements View layer for suggestion display with accessibility support.
"""

from typing import Optional, Callable

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
)
from PySide6.QtGui import QFont

from app.modules.suggestions.view_models import SuggestionViewModel


class SuggestionNotificationWidget(QWidget):
    """Non-intrusive notification widget for suggestions.
    
    Displays suggestions as a compact, dismissible notification.
    Follows QSS styling conventions for Sageframe aesthetic.
    """
    
    def __init__(
        self,
        suggestion: dict,
        on_dismiss: Optional[Callable[[str], None]] = None,
        on_action: Optional[Callable[[str, str], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        """Initialize suggestion notification.
        
        Args:
            suggestion: Suggestion dictionary with task info
            on_dismiss: Callback for dismiss action
            on_action: Callback for action (e.g., "add_to_schedule")
            parent: Optional parent widget
        """
        super().__init__(parent)
        
        self.suggestion = suggestion
        self.on_dismiss = on_dismiss
        self.on_action = on_action
        
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Set up the notification UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        
        # Content section
        content_layout = QVBoxLayout()
        
        task_name = self.suggestion.get("task_name", "Suggestion")
        reasoning = self.suggestion.get("reasoning", "")
        
        # Title
        title_label = QLabel(task_name)
        title_label.setObjectName("suggestionTitle")
        font = title_label.font()
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAccessibleName(f"Suggestion: {task_name}")
        content_layout.addWidget(title_label)
        
        # Reasoning/description
        if reasoning:
            reason_label = QLabel(reasoning)
            reason_label.setObjectName("suggestionReason")
            reason_label.setWordWrap(True)
            reason_label.setAccessibleDescription(reasoning)
            content_layout.addWidget(reason_label)
        
        layout.addLayout(content_layout, 1)  # Takes up available space
        
        # Action buttons
        button_layout = QVBoxLayout()
        
        # Dismiss button
        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.setObjectName("dismissButton")
        dismiss_btn.setMaximumWidth(80)
        dismiss_btn.setAccessibleName("Dismiss suggestion")
        dismiss_btn.clicked.connect(self._on_dismiss)
        button_layout.addWidget(dismiss_btn)
        
        # Act upon button
        act_btn = QPushButton("Add")
        act_btn.setObjectName("actButton")
        act_btn.setMaximumWidth(80)
        act_btn.setAccessibleName("Add task to schedule")
        act_btn.clicked.connect(self._on_action)
        button_layout.addWidget(act_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _apply_styling(self):
        """Apply QSS styling."""
        self.setObjectName("suggestionNotification")
        self.setStyleSheet("""
            #suggestionNotification {
                background-color: #f0f4f8;
                border: 1px solid #d0d7e0;
                border-radius: 6px;
            }
            #suggestionTitle {
                color: #1a1a1a;
                font-size: 12pt;
            }
            #suggestionReason {
                color: #555555;
                font-size: 10pt;
            }
            #dismissButton, #actButton {
                background-color: #ffffff;
                border: 1px solid #d0d7e0;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10pt;
            }
            #dismissButton:hover, #actButton:hover {
                background-color: #f5f5f5;
            }
        """)
    
    def _on_dismiss(self):
        """Handle dismiss action."""
        if self.on_dismiss:
            task_id = self.suggestion.get("task_id")
            self.on_dismiss(task_id)
    
    def _on_action(self):
        """Handle act upon action."""
        if self.on_action:
            task_id = self.suggestion.get("task_id")
            self.on_action(task_id, "add_to_schedule")


class SuggestionPanel(QWidget):
    """Dedicated panel for suggestion display and management.
    
    Less intrusive than notifications, shows suggestions in a dedicated area.
    """
    
    def __init__(
        self,
        view_model: SuggestionViewModel,
        parent: Optional[QWidget] = None,
    ):
        """Initialize suggestion panel.
        
        Args:
            view_model: SuggestionViewModel instance
            parent: Optional parent widget
        """
        super().__init__(parent)
        
        self.view_model = view_model
        self._suggestion_widgets: dict = {}
        
        self._setup_ui()
        self._connect_signals()
        self._apply_styling()
    
    def _setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header
        header = QLabel("Suggestions")
        header.setObjectName("panelHeader")
        font = header.font()
        font.setBold(True)
        font.setPointSize(11)
        header.setFont(font)
        header.setAccessibleName("Suggestions panel")
        layout.addWidget(header)
        
        # Scroll area for suggestions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("suggestionScroll")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(6)
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll, 1)
    
    def _connect_signals(self):
        """Connect ViewModel signals."""
        self.view_model.suggestionsGenerated.connect(self._on_suggestions_generated)
        self.view_model.suggestionDismissed.connect(self._on_suggestion_dismissed)
    
    def _on_suggestions_generated(self, suggestions: list):
        """Handle new suggestions.
        
        Args:
            suggestions: List of suggestion dictionaries
        """
        # Clear existing
        for widget in self._suggestion_widgets.values():
            widget.deleteLater()
        self._suggestion_widgets.clear()
        
        # Add new suggestion widgets
        for suggestion in suggestions:
            notification = SuggestionNotificationWidget(
                suggestion,
                on_dismiss=self.view_model.dismiss_suggestion,
                on_action=self.view_model.act_on_suggestion,
                parent=self.content_widget,
            )
            
            task_id = suggestion.get("task_id")
            self._suggestion_widgets[task_id] = notification
            self.content_layout.addWidget(notification)
        
        # Add stretch if no suggestions
        if not suggestions:
            empty_label = QLabel("No suggestions at this time")
            empty_label.setObjectName("emptyLabel")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addStretch()
    
    def _on_suggestion_dismissed(self, suggestion_id: str):
        """Handle suggestion dismissal.
        
        Args:
            suggestion_id: ID of dismissed suggestion
        """
        if suggestion_id in self._suggestion_widgets:
            widget = self._suggestion_widgets.pop(suggestion_id)
            widget.deleteLater()
    
    def _apply_styling(self):
        """Apply QSS styling."""
        self.setObjectName("suggestionPanel")
        self.setStyleSheet("""
            #suggestionPanel {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            #panelHeader {
                color: #1a1a1a;
                font-size: 11pt;
                padding: 4px 0px;
            }
            #suggestionScroll {
                background-color: #ffffff;
                border: none;
            }
            #emptyLabel {
                color: #999999;
                font-size: 10pt;
            }
        """)
    
    def sizeHint(self) -> QSize:
        """Suggest optimal size."""
        return QSize(300, 400)

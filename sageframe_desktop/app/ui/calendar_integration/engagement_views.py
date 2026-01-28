"""UI components for engagement suggestions.

Displays proactive engagement suggestions with accept/decline/dismiss actions.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from app.modules.calendar_integration.engagement_service import EngagementSuggestion


class EngagementSuggestionCard(QFrame):
    """Card widget for displaying a single engagement suggestion."""
    
    # Signals
    accepted = Signal(str)  # suggestion_id
    declined = Signal(str, str)  # suggestion_id, reason
    dismissed = Signal(str)  # suggestion_id
    
    def __init__(self, suggestion: EngagementSuggestion, parent: Optional[QWidget] = None):
        """Initialize suggestion card.
        
        Args:
            suggestion: EngagementSuggestion to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.suggestion = suggestion
        
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f7ff;
                border: 1px solid #90caf9;
                border-radius: 8px;
                padding: 12px;
                margin: 4px;
            }
        """)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Type indicator
        type_emoji = {
            'social': '👥',
            'professional': '💼',
            'task-related': '✅'
        }
        emoji = type_emoji.get(self.suggestion.suggestion_type, '💡')
        
        # Header
        header_layout = QHBoxLayout()
        
        type_label = QLabel(f"{emoji} {self.suggestion.suggestion_type.replace('-', ' ').title()}")
        type_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #1976d2;")
        header_layout.addWidget(type_label)
        
        header_layout.addStretch()
        
        # Confidence indicator
        confidence_pct = int(self.suggestion.confidence_score * 100)
        confidence_label = QLabel(f"{confidence_pct}% match")
        confidence_label.setStyleSheet("font-size: 11px; color: #666;")
        header_layout.addWidget(confidence_label)
        
        layout.addLayout(header_layout)
        
        # Title
        title_label = QLabel(self.suggestion.title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #212121;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Time slot
        start_time = self.suggestion.suggested_time_slot['start']
        time_str = start_time.strftime('%A, %B %d at %I:%M %p')
        duration_str = f"{self.suggestion.duration_minutes} minutes"
        
        time_label = QLabel(f"⏰ {time_str} ({duration_str})")
        time_label.setStyleSheet("font-size: 13px; color: #424242; margin-top: 4px;")
        layout.addWidget(time_label)
        
        # Description
        description_label = QLabel(self.suggestion.description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 13px; color: #616161; margin-top: 8px;")
        layout.addWidget(description_label)
        
        # Reasoning
        reasoning_label = QLabel(f"Why: {self.suggestion.reasoning}")
        reasoning_label.setWordWrap(True)
        reasoning_label.setStyleSheet("font-size: 11px; color: #757575; font-style: italic; margin-top: 4px;")
        layout.addWidget(reasoning_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        dismiss_btn = QPushButton("Not Now")
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #bdbdbd;
            }
        """)
        dismiss_btn.clicked.connect(self._on_dismiss)
        button_layout.addWidget(dismiss_btn)
        
        decline_btn = QPushButton("Not Interested")
        decline_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffcdd2;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                color: #c62828;
            }
            QPushButton:hover {
                background-color: #ef9a9a;
            }
        """)
        decline_btn.clicked.connect(self._on_decline)
        button_layout.addWidget(decline_btn)
        
        accept_btn = QPushButton("Schedule It!")
        accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        accept_btn.clicked.connect(self._on_accept)
        button_layout.addWidget(accept_btn)
        
        layout.addLayout(button_layout)
    
    def _on_accept(self):
        """Handle accept button click."""
        self.accepted.emit(self.suggestion.suggestion_id)
        self.hide()
    
    def _on_decline(self):
        """Handle decline button click."""
        # Could add a dialog to ask for reason
        reason = "User declined"
        self.declined.emit(self.suggestion.suggestion_id, reason)
        self.hide()
    
    def _on_dismiss(self):
        """Handle dismiss button click."""
        self.dismissed.emit(self.suggestion.suggestion_id)
        self.hide()


class EngagementSuggestionPanel(QWidget):
    """Panel for displaying multiple engagement suggestions."""
    
    # Signals
    suggestionAccepted = Signal(str)  # suggestion_id
    suggestionDeclined = Signal(str, str)  # suggestion_id, reason
    suggestionDismissed = Signal(str)  # suggestion_id
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize suggestion panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._suggestion_cards = []
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_label = QLabel("💡 Suggested Engagements")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976d2; padding: 8px;")
        layout.addWidget(header_label)
        
        # Scroll area for suggestions
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        self.suggestions_layout = QVBoxLayout(scroll_content)
        self.suggestions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # Empty state message
        self.empty_label = QLabel("No suggestions at the moment. Check back later!")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #757575; font-style: italic; padding: 20px;")
        self.suggestions_layout.addWidget(self.empty_label)
    
    def add_suggestion(self, suggestion: EngagementSuggestion):
        """Add a suggestion to the panel.
        
        Args:
            suggestion: EngagementSuggestion to add
        """
        # Hide empty message
        self.empty_label.hide()
        
        # Create card
        card = EngagementSuggestionCard(suggestion)
        card.accepted.connect(self._on_card_accepted)
        card.declined.connect(self._on_card_declined)
        card.dismissed.connect(self._on_card_dismissed)
        
        self.suggestions_layout.addWidget(card)
        self._suggestion_cards.append(card)
    
    def clear_suggestions(self):
        """Clear all suggestions from panel."""
        for card in self._suggestion_cards:
            card.deleteLater()
        
        self._suggestion_cards.clear()
        self.empty_label.show()
    
    def _on_card_accepted(self, suggestion_id: str):
        """Handle card acceptance.
        
        Args:
            suggestion_id: ID of accepted suggestion
        """
        self.suggestionAccepted.emit(suggestion_id)
        
        # Show success message
        QMessageBox.information(
            self,
            "Suggestion Accepted",
            "Great! I've added this to your calendar. 📅"
        )
    
    def _on_card_declined(self, suggestion_id: str, reason: str):
        """Handle card decline.
        
        Args:
            suggestion_id: ID of declined suggestion
            reason: Decline reason
        """
        self.suggestionDeclined.emit(suggestion_id, reason)
    
    def _on_card_dismissed(self, suggestion_id: str):
        """Handle card dismissal.
        
        Args:
            suggestion_id: ID of dismissed suggestion
        """
        self.suggestionDismissed.emit(suggestion_id)

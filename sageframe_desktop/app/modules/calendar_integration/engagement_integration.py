"""Integration layer for proactive engagement suggestions.

This module connects calendar availability, task management, and AI co-pilot
to provide intelligent, empathetic engagement suggestions.
"""

from typing import List, Optional, Dict
from datetime import datetime, timezone

from PySide6.QtCore import QObject, Signal

from app.modules.calendar_integration.engagement_service import (
    EngagementSuggestionService,
    EngagementSuggestion
)
from app.modules.calendar_integration.services import CalendarSyncService
from app.modules.ai_copilot.services import CopilotCommunicationService
from app.modules.ai_copilot.persona import ToneLevel


class EngagementSuggestionIntegration(QObject):
    """Integration coordinator for proactive engagement suggestions.
    
    Connects Story 4.1 (calendar), Story 4.2 (availability), Story 4.3 (events),
    and Story 1.4 (AI co-pilot) to suggest engagements proactively.
    """
    
    # Signals
    suggestionGenerated = Signal(object)  # EngagementSuggestion
    suggestionAccepted = Signal(str, object)  # suggestion_id, event_data
    suggestionDeclined = Signal(str, str)  # suggestion_id, reason
    suggestionDismissed = Signal(str)  # suggestion_id
    
    def __init__(
        self,
        engagement_service: Optional[EngagementSuggestionService] = None,
        calendar_service: Optional[CalendarSyncService] = None,
        copilot_service: Optional[CopilotCommunicationService] = None,
        parent: Optional[QObject] = None
    ):
        """Initialize integration.
        
        Args:
            engagement_service: EngagementSuggestionService instance
            calendar_service: CalendarSyncService instance
            copilot_service: CopilotCommunicationService instance
            parent: Optional parent QObject
        """
        super().__init__(parent)
        
        self.engagement_service = engagement_service or EngagementSuggestionService()
        self.calendar_service = calendar_service or CalendarSyncService()
        self.copilot_service = copilot_service
        
        self._pending_suggestions = {}  # suggestion_id -> EngagementSuggestion
        self._last_suggestion_time = None
    
    def generate_suggestions_for_context(
        self,
        connection_id: int,
        user_tasks: List[Dict],
        mood: Optional[str] = None,
        energy_level: Optional[str] = None
    ) -> List[EngagementSuggestion]:
        """Generate engagement suggestions based on current context.
        
        Args:
            connection_id: Calendar connection ID
            user_tasks: List of user tasks
            mood: User's current mood
            energy_level: User's current energy level
        
        Returns:
            List of EngagementSuggestion objects
        """
        # Don't over-suggest - minimum 4 hours between suggestion batches
        if self._last_suggestion_time:
            time_since_last = datetime.now(timezone.utc) - self._last_suggestion_time
            if time_since_last.total_seconds() < 4 * 3600:
                return []
        
        # Generate suggestions
        suggestions = self.engagement_service.generate_engagement_suggestions(
            connection_id=connection_id,
            user_tasks=user_tasks,
            mood=mood,
            energy_level=energy_level,
            lookback_days=7,
            max_suggestions=2
        )
        
        if suggestions:
            self._last_suggestion_time = datetime.now(timezone.utc)
            
            # Store pending suggestions
            for suggestion in suggestions:
                self._pending_suggestions[suggestion.suggestion_id] = suggestion
            
            # Emit each suggestion for display
            for suggestion in suggestions:
                self.suggestionGenerated.emit(suggestion)
        
        return suggestions
    
    def format_suggestion_message(
        self,
        suggestion: EngagementSuggestion,
        mood: Optional[str] = None
    ) -> str:
        """Format suggestion as empathetic co-pilot message.
        
        Args:
            suggestion: EngagementSuggestion to format
            mood: User's current mood for tone adjustment
        
        Returns:
            Formatted message string
        """
        # Determine tone based on suggestion type and mood
        tone = self._determine_tone(suggestion.suggestion_type, mood)
        
        # Build message with empathetic framing
        time_str = suggestion.suggested_time_slot['start'].strftime('%A, %B %d at %I:%M %p')
        
        if suggestion.suggestion_type == 'task-related':
            message = (
                f"💡 I noticed you have '{suggestion.title}' on your task list. "
                f"You have a {suggestion.duration_minutes}-minute free block on {time_str}. "
                f"Would you like me to schedule it for you?"
            )
        
        elif suggestion.suggestion_type == 'social':
            if mood in ['happy', 'energized']:
                message = (
                    f"🌟 You're in a great mood! You have some free time on {time_str}. "
                    f"This could be a perfect opportunity to connect with someone you care about. "
                    f"Would you like to schedule a social catch-up?"
                )
            else:
                message = (
                    f"💭 You have a nice free block on {time_str}. "
                    f"Connecting with friends or colleagues could be refreshing. "
                    f"Would you like to schedule some social time?"
                )
        
        elif suggestion.suggestion_type == 'professional':
            message = (
                f"📚 You have a productive {suggestion.duration_minutes}-minute slot on {time_str}. "
                f"This could be great for professional development or a mentor meeting. "
                f"Interested in blocking this time?"
            )
        
        else:
            message = f"{suggestion.description} (on {time_str})"
        
        return message
    
    def _determine_tone(self, suggestion_type: str, mood: Optional[str]) -> ToneLevel:
        """Determine appropriate tone for suggestion.
        
        Args:
            suggestion_type: Type of suggestion
            mood: User's current mood
        
        Returns:
            ToneLevel enum value
        """
        # Gentle tone for stressed/anxious moods
        if mood in ['stressed', 'anxious', 'sad']:
            return ToneLevel.GENTLE
        
        # Encouraging tone for energized/happy moods
        if mood in ['happy', 'energized', 'excited']:
            return ToneLevel.ENCOURAGING
        
        # Normal tone otherwise
        return ToneLevel.NORMAL
    
    def accept_suggestion(self, suggestion_id: str) -> Optional[object]:
        """Handle user accepting a suggestion.
        
        Creates calendar event from the suggestion.
        
        Args:
            suggestion_id: ID of accepted suggestion
        
        Returns:
            Created CalendarEvent or None if failed
        """
        suggestion = self._pending_suggestions.get(suggestion_id)
        if not suggestion:
            return None
        
        try:
            # Get connection ID from first available connection
            # TODO: Should be passed as parameter or stored in suggestion
            from app.modules.calendar_integration.models import CalendarConnection
            connection = self.calendar_service.session.query(CalendarConnection).first()
            if not connection:
                return None
            
            # Create event using Story 4.3 capabilities
            event = self.calendar_service.create_event(
                connection_id=connection.id,
                summary=suggestion.title,
                start_time=suggestion.suggested_time_slot['start'],
                end_time=suggestion.suggested_time_slot['end'],
                description=suggestion.description,
                is_all_day=False
            )
            
            # Record acceptance for learning
            self.engagement_service.record_suggestion_response(
                suggestion_id,
                'accepted'
            )
            
            # Emit signal
            self.suggestionAccepted.emit(suggestion_id, event)
            
            # Remove from pending
            del self._pending_suggestions[suggestion_id]
            
            return event
        
        except Exception as e:
            print(f"Failed to accept suggestion: {e}")
            return None
    
    def decline_suggestion(self, suggestion_id: str, reason: Optional[str] = None):
        """Handle user declining a suggestion.
        
        Learns from the decline to improve future suggestions.
        
        Args:
            suggestion_id: ID of declined suggestion
            reason: Optional reason for decline
        """
        suggestion = self._pending_suggestions.get(suggestion_id)
        if not suggestion:
            return
        
        # Record decline for learning
        self.engagement_service.record_suggestion_response(
            suggestion_id,
            'declined',
            reason
        )
        
        # Emit signal
        self.suggestionDeclined.emit(suggestion_id, reason or "No reason provided")
        
        # Remove from pending
        del self._pending_suggestions[suggestion_id]
    
    def dismiss_suggestion(self, suggestion_id: str):
        """Handle user dismissing a suggestion.
        
        Reduces frequency of similar suggestions but doesn't learn strong preference.
        
        Args:
            suggestion_id: ID of dismissed suggestion
        """
        suggestion = self._pending_suggestions.get(suggestion_id)
        if not suggestion:
            return
        
        # Record dismissal
        self.engagement_service.record_suggestion_response(
            suggestion_id,
            'dismissed'
        )
        
        # Emit signal
        self.suggestionDismissed.emit(suggestion_id)
        
        # Remove from pending
        del self._pending_suggestions[suggestion_id]
    
    def check_and_generate_suggestions(
        self,
        connection_id: int,
        user_tasks: List[Dict],
        mood: Optional[str] = None,
        energy_level: Optional[str] = None
    ):
        """Check if conditions are right and generate suggestions.
        
        This is the main entry point for proactive suggestion generation.
        
        Args:
            connection_id: Calendar connection ID
            user_tasks: List of user tasks
            mood: User's current mood
            energy_level: User's current energy level
        """
        # Generate suggestions
        suggestions = self.generate_suggestions_for_context(
            connection_id,
            user_tasks,
            mood,
            energy_level
        )
        
        # If we have a copilot service, send formatted messages
        if self.copilot_service and suggestions:
            for suggestion in suggestions:
                message = self.format_suggestion_message(suggestion, mood)
                
                # Send via copilot with appropriate tone
                tone = self._determine_tone(suggestion.suggestion_type, mood)
                
                # TODO: Send message via copilot service
                # self.copilot_service.send_message(message, tone)

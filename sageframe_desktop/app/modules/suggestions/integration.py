"""Integration layer connecting mood check-in to suggestion generation.

This module coordinates between mood check-in events and suggestion generation,
ensuring suggestions are delivered with proper empathetic tone through the
CopilotCommunicationService.
"""

from typing import Optional, List, Dict

from PySide6.QtCore import QObject, Signal

from app.modules.suggestions.services import SuggestionService
from app.modules.ai_copilot.services import CopilotCommunicationService
from app.modules.ai_copilot.persona import ToneLevel


class MoodSuggestionIntegration(QObject):
    """Integrates mood check-in with suggestion generation.
    
    Responsibilities:
    - Listen for mood check-in completion events
    - Generate contextual suggestions based on mood/energy
    - Deliver suggestions through CopilotCommunicationService
    - Ensure empathetic tone is maintained
    """
    
    # Signals
    suggestionsReady = Signal(list)  # List of suggestion dicts with messages
    
    def __init__(
        self,
        suggestion_service: Optional[SuggestionService] = None,
        copilot_service: Optional[CopilotCommunicationService] = None,
        parent: Optional[QObject] = None,
    ):
        """Initialize integration.
        
        Args:
            suggestion_service: SuggestionService instance
            copilot_service: CopilotCommunicationService instance
            parent: Optional parent QObject
        """
        super().__init__(parent)
        
        self.suggestion_service = suggestion_service or SuggestionService()
        self.copilot_service = copilot_service
        self._available_tasks: List[Dict] = []
    
    def set_available_tasks(self, tasks: List[Dict]):
        """Set the list of available tasks for suggestions.
        
        Args:
            tasks: List of task dictionaries with 'id', 'name', 'difficulty'
        """
        self._available_tasks = tasks
    
    def on_mood_checkin_completed(
        self,
        mood: str,
        energy_level: str,
        user_activity_state: Optional[str] = None,
    ):
        """Handle mood check-in completion event.
        
        Generates suggestions and delivers them through communication service.
        
        Args:
            mood: User's current mood
            energy_level: User's current energy level
            user_activity_state: Current user activity state
        """
        if not self._available_tasks:
            # No tasks available for suggestions
            return
        
        try:
            # Generate suggestions
            response = self.suggestion_service.generate_suggestions(
                mood=mood,
                energy_level=energy_level,
                available_tasks=self._available_tasks,
                user_activity_state=user_activity_state,
                max_suggestions=3,
            )
            
            if not response.suggestions or not response.should_display:
                return
            
            # Enhance suggestions with empathetic messages via copilot service
            suggestions_with_messages = self._enhance_suggestions_with_messages(
                suggestions=response.suggestions,
                mood=mood,
                energy_level=energy_level,
            )
            
            # Emit ready signal
            self.suggestionsReady.emit(suggestions_with_messages)
            
        except Exception as e:
            # Log error but don't crash
            print(f"Error generating suggestions: {e}")
    
    def _enhance_suggestions_with_messages(
        self,
        suggestions: List[Dict],
        mood: str,
        energy_level: str,
    ) -> List[Dict]:
        """Enhance suggestions with empathetic messages.
        
        Adds copilot-generated messages that maintain empathetic tone.
        
        Args:
            suggestions: List of raw suggestion dicts
            mood: User's current mood
            energy_level: User's current energy level
            
        Returns:
            List of suggestions with enhanced messages
        """
        enhanced = []
        
        for suggestion in suggestions:
            enhanced_suggestion = suggestion.copy()
            
            # Generate empathetic task suggestion message
            if self.copilot_service:
                try:
                    message = self.copilot_service.generate_task_suggestion(
                        task_name=suggestion.get("task_name", "Task"),
                        tone_level=ToneLevel.GENTLE,
                    )
                    
                    # Validate tone compliance
                    is_valid, _ = self.copilot_service.validate_message_tone(message)
                    if is_valid:
                        enhanced_suggestion["copilot_message"] = message
                        
                        # Save communication event for tracking
                        self.copilot_service.save_communication_event(
                            message_text=message,
                            category="task_suggestion",
                            tone_level="gentle",
                            user_mood=mood,
                            user_energy_level=self._energy_to_level(energy_level),
                        )
                    else:
                        # Fallback to original reasoning
                        enhanced_suggestion["copilot_message"] = suggestion.get(
                            "reasoning", "This task is suggested for you."
                        )
                except Exception as e:
                    # Fallback to original reasoning if message generation fails
                    print(f"Error generating copilot message: {e}")
                    enhanced_suggestion["copilot_message"] = suggestion.get(
                        "reasoning", "This task is suggested for you."
                    )
            else:
                # No copilot service, use original reasoning
                enhanced_suggestion["copilot_message"] = suggestion.get(
                    "reasoning", "This task is suggested for you."
                )
            
            enhanced.append(enhanced_suggestion)
        
        return enhanced
    
    @staticmethod
    def _energy_to_level(energy_level: str) -> int:
        """Convert energy level string to 1-10 scale.
        
        Args:
            energy_level: "high", "medium", or "low"
            
        Returns:
            Energy level as 1-10 scale
        """
        level_map = {
            "high": 8,
            "medium": 5,
            "low": 2,
        }
        return level_map.get(energy_level, 5)

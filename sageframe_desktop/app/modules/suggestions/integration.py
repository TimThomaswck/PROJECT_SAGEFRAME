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
        # If no tasks available, emit fallback suggestions directly
        if not self._available_tasks:
            fallback_suggestions = self._get_fallback_suggestions(mood, energy_level)
            self.suggestionsReady.emit(fallback_suggestions)
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
                # Emit fallback suggestions if no valid suggestions
                fallback_suggestions = self._get_fallback_suggestions(mood, energy_level)
                self.suggestionsReady.emit(fallback_suggestions)
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
            # Log error and emit fallback generic suggestions
            print(f"Error generating suggestions: {e}")
            fallback_suggestions = self._get_fallback_suggestions(mood, energy_level)
            self.suggestionsReady.emit(fallback_suggestions)
    
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
    
    def _get_fallback_suggestions(self, mood: str, energy_level: str) -> List[Dict]:
        """Generate generic fallback suggestions when AI fails.
        
        Provides motivational tips and productivity advice.
        
        Args:
            mood: User's current mood
            energy_level: User's current energy level
            
        Returns:
            List of fallback suggestion dictionaries
        """
        # Generic productivity tips by energy level
        tips_by_energy = {
            "high": [
                "🚀 **Tackle Your Most Challenging Task** - Your energy is high! This is the perfect time to work on complex or creative tasks that require deep focus.",
                "💪 **Break Through That Roadblock** - High energy is ideal for problem-solving. Pick a task you've been avoiding and power through it.",
                "🎯 **Start a Big Project** - Use this momentum to make significant progress on important long-term goals.",
            ],
            "medium": [
                "📋 **Work Through Your List** - You're in a balanced state. Focus on steady progress through medium-priority tasks.",
                "🔄 **Review and Organize** - Great time to organize your workspace, review notes, or plan tomorrow's tasks.",
                "💼 **Handle Administrative Tasks** - Moderate energy is perfect for emails, calls, and routine work.",
            ],
            "low": [
                "🌱 **Start Small** - Low energy? No problem. Pick easy, satisfying tasks to build momentum.",
                "📚 **Learning Mode** - Use this time for light reading, watching tutorials, or browsing inspiration.",
                "🧘 **Self-Care First** - Consider a short break, stretch, or meditation before diving back in.",
            ],
        }
        
        # Motivational snippets
        motivational_quotes = [
            "✨ **Remember**: Progress over perfection. Any step forward is a win.",
            "💡 **Tip**: Breaking tasks into 5-minute chunks makes them less overwhelming.",
            "🌟 **Insight**: Your brain works best with regular breaks. Don't forget to rest!",
            "🎨 **Approach**: Sometimes changing your environment can boost creativity.",
            "⏰ **Strategy**: Time-blocking can help you stay focused. Try 25-minute work sessions.",
        ]
        
        # Select tips based on energy level
        energy_tips = tips_by_energy.get(energy_level.lower(), tips_by_energy["medium"])
        
        # Build fallback suggestions
        suggestions = []
        
        # Add 2 energy-specific tips
        for tip in energy_tips[:2]:
            suggestions.append({
                "task_name": "Productivity Tip",
                "task_id": "generic",
                "reasoning": tip,
                "copilot_message": tip,
                "mood_context": mood,
                "energy_context": energy_level,
                "is_generic": True,
            })
        
        # Add 1 motivational quote
        import random
        suggestions.append({
            "task_name": "Daily Motivation",
            "task_id": "generic",
            "reasoning": random.choice(motivational_quotes),
            "copilot_message": random.choice(motivational_quotes),
            "mood_context": mood,
            "energy_context": energy_level,
            "is_generic": True,
        })
        
        return suggestions
    
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

"""ViewModel for suggestion presentation and interaction.

Implements the ViewModel layer of MVVM pattern for suggestion UI.
"""

from typing import List, Optional, Dict

from PySide6.QtCore import QObject, Signal, Property

from app.modules.suggestions.services import SuggestionService


class SuggestionViewModel(QObject):
    """ViewModel for suggestion presentation.
    
    Manages suggestion UI state, user interaction, and coordination
    with the suggestion service layer.
    """
    
    # Signals (verbNoun naming convention)
    suggestionsGenerated = Signal(list)  # List of suggestion dicts
    suggestionDismissed = Signal(str)    # suggestion_id
    suggestionActedUpon = Signal(str, str)  # suggestion_id, action (e.g., "add_to_schedule")
    suggestionPresented = Signal(str)    # suggestion_id
    validationError = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None):
        """Initialize ViewModel.
        
        Args:
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._service = SuggestionService()
        self._current_suggestions: List[Dict] = []
        self._is_loading = False
        self._delivery_style = "notification"
    
    @Property(list)
    def currentSuggestions(self) -> List[Dict]:
        """Get current suggestions."""
        return self._current_suggestions.copy()
    
    @Property(bool)
    def isLoading(self) -> bool:
        """Get loading state."""
        return self._is_loading
    
    @Property(str)
    def deliveryStyle(self) -> str:
        """Get delivery style (notification, panel, chat)."""
        return self._delivery_style
    
    def generate_suggestions(
        self,
        mood: str,
        energy_level: str,
        available_tasks: List[Dict],
        user_activity_state: Optional[str] = None,
        user_preferences: Optional[Dict] = None,
    ):
        """Generate suggestions based on mood and available tasks.
        
        Args:
            mood: User's current mood
            energy_level: User's current energy level
            available_tasks: List of available tasks
            user_activity_state: Current user activity
            user_preferences: User's delivery preferences
        """
        if self._is_loading:
            return  # Prevent concurrent generation
        
        self._is_loading = True
        
        try:
            response = self._service.generate_suggestions(
                mood=mood,
                energy_level=energy_level,
                available_tasks=available_tasks,
                user_activity_state=user_activity_state,
                user_preferences=user_preferences,
                max_suggestions=3,
            )
            
            self._current_suggestions = response.suggestions
            self._delivery_style = response.delivery_style
            
            if response.suggestions:
                self.suggestionsGenerated.emit(response.suggestions)
            
        except Exception as e:
            self.validationError.emit(f"Failed to generate suggestions: {str(e)}")
        finally:
            self._is_loading = False
    
    def dismiss_suggestion(self, suggestion_id: str):
        """Dismiss a suggestion.
        
        Args:
            suggestion_id: ID of suggestion to dismiss
        """
        # Remove from current suggestions
        self._current_suggestions = [
            s for s in self._current_suggestions 
            if s.get("task_id") != suggestion_id
        ]
        
        self.suggestionDismissed.emit(suggestion_id)
    
    def act_on_suggestion(self, suggestion_id: str, action: str):
        """User acts on a suggestion.
        
        Args:
            suggestion_id: ID of suggestion
            action: Action taken (e.g., "add_to_schedule", "start_now")
        """
        # Remove from current suggestions
        self._current_suggestions = [
            s for s in self._current_suggestions 
            if s.get("task_id") != suggestion_id
        ]
        
        self.suggestionActedUpon.emit(suggestion_id, action)
    
    def clear_suggestions(self):
        """Clear all current suggestions."""
        self._current_suggestions.clear()
        self._service.reset_session_counters()

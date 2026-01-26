"""
Integration layer between Story 1.3 (Mood Check-in) and Story 1.4 (Co-Pilot Communication)

This module provides reactive mood-aware message delivery. When a user completes
a mood check-in, the co-pilot automatically generates an empathetic response
tailored to their current mood and energy level.

Architecture:
- Listens to MoodCheckInViewModel.moodCheckInCompleted signal
- Retrieves latest mood data from MoodCheckInService
- Generates mood-aware co-pilot response via CopilotCommunicationService
- Displays response with appropriate tone and context
- Stores mood context in CommunicationEvent for learning
"""

from typing import Optional
from datetime import datetime, timezone

from PySide6.QtCore import QObject, Signal, Slot

from app.modules.mood_checkin.services import MoodCheckInService
from app.modules.mood_checkin.models import MoodCheckIn
from app.modules.ai_copilot.services import CopilotCommunicationService
from app.modules.ai_copilot.view_models import CopilotViewModel
from app.modules.ai_copilot.models import UserActivityState


class MoodAwareCopilotIntegration(QObject):
    """
    Integration coordinator for mood-aware co-pilot communication.
    
    Connects the mood check-in system (Story 1.3) with the co-pilot communication
    system (Story 1.4) to provide empathetic, context-aware responses.
    
    Signal Flow:
    1. User completes mood check-in → MoodCheckInViewModel.moodCheckInCompleted
    2. This integration receives signal and retrieves mood data
    3. Generates mood-aware co-pilot response
    4. Displays response via CopilotViewModel
    5. Stores context (mood, energy) in CommunicationEvent
    
    Signals:
    - moodResponseGenerated: Emitted when mood response is generated
    - moodResponseDisplayed: Emitted when response is shown to user
    - integrationError: Emitted if any error occurs
    """
    
    # Signals
    moodResponseGenerated = Signal(str)  # response_text
    moodResponseDisplayed = Signal(str)  # message_id
    integrationError = Signal(str)  # error_message
    
    def __init__(self, mood_service: Optional[MoodCheckInService] = None,
                 copilot_service: Optional[CopilotCommunicationService] = None,
                 copilot_viewmodel: Optional[CopilotViewModel] = None):
        """
        Initialize integration coordinator.
        
        Args:
            mood_service: MoodCheckInService instance (creates new if None)
            copilot_service: CopilotCommunicationService instance (requires db_session if None)
            copilot_viewmodel: CopilotViewModel instance (requires db_session if None)
        """
        super().__init__()
        
        # Initialize services
        self._mood_service = mood_service or MoodCheckInService()
        self._copilot_service = copilot_service
        self._copilot_viewmodel = copilot_viewmodel
        
        # Track last mood for intelligent message composition
        self._last_mood: Optional[str] = None
        self._last_energy: Optional[str] = None
        self._last_response_time: Optional[datetime] = None
    
    def connect_mood_checkin_signal(self, mood_viewmodel: QObject) -> bool:
        """
        Connect to MoodCheckInViewModel signals.
        
        Args:
            mood_viewmodel: MoodCheckInViewModel instance
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Connect to moodCheckInCompleted signal (bool, str)
            if hasattr(mood_viewmodel, 'moodCheckInCompleted'):
                mood_viewmodel.moodCheckInCompleted.connect(
                    self._on_mood_checkin_completed
                )
                return True
            else:
                self.integrationError.emit(
                    "MoodCheckInViewModel does not have moodCheckInCompleted signal"
                )
                return False
        except Exception as e:
            self.integrationError.emit(f"Failed to connect mood signal: {str(e)}")
            return False
    
    @Slot(bool, str)
    def _on_mood_checkin_completed(self, success: bool, message: str):
        """
        Handle mood check-in completion.
        
        Called when user completes mood check-in dialog.
        Generates and displays mood-aware co-pilot response.
        
        Args:
            success: Whether check-in was successful
            message: Status message from dialog
        """
        if not success:
            # User cancelled or error occurred
            return
        
        try:
            # Retrieve latest mood check-in data
            mood_checkin = self._mood_service.get_last_mood_checkin()
            if not mood_checkin:
                self.integrationError.emit("No mood check-in data available")
                return
            
            # Store mood context
            self._last_mood = mood_checkin.mood_level
            self._last_energy = mood_checkin.energy_level
            self._last_response_time = datetime.now(timezone.utc)
            
            # Determine tone level based on mood/energy
            tone_level = self._determine_tone_level(
                mood_checkin.mood_level,
                mood_checkin.energy_level
            )
            
            # Generate mood-aware response
            response_text = self._generate_mood_response(
                mood_checkin.mood_level,
                mood_checkin.energy_level,
                tone_level
            )
            
            if not response_text:
                self.integrationError.emit("Failed to generate mood response")
                return
            
            # Emit signal that response was generated
            self.moodResponseGenerated.emit(response_text)
            
            # Display response via co-pilot if available
            if self._copilot_viewmodel:
                message_id = self._display_mood_response(
                    response_text,
                    mood_checkin,
                    tone_level
                )
                if message_id:
                    self.moodResponseDisplayed.emit(message_id)
            
        except Exception as e:
            self.integrationError.emit(
                f"Error processing mood check-in: {str(e)}"
            )
    
    def _determine_tone_level(self, mood: str, energy: str) -> str:
        """
        Determine appropriate tone level based on mood and energy.
        
        Args:
            mood: User's mood (happy, neutral, stressed, sad)
            energy: User's energy level (high, medium, low)
            
        Returns:
            Tone level (gentle, normal, encouraging)
        """
        # Low energy or stressed → use gentle tone
        if energy == "low" or mood in ["stressed", "sad"]:
            return "gentle"
        
        # High energy and positive mood → use encouraging tone
        if energy == "high" and mood in ["happy"]:
            return "encouraging"
        
        # Default to normal tone
        return "normal"
    
    def _generate_mood_response(self, mood: str, energy: str, tone_level: str) -> str:
        """
        Generate mood-aware co-pilot response.
        
        Args:
            mood: User's mood
            energy: User's energy level
            tone_level: Tone to use (gentle, normal, encouraging)
            
        Returns:
            Generated response text
        """
        if not self._copilot_service:
            return None
        
        try:
            # Use co-pilot service to generate mood response
            response = self._copilot_service.generate_mood_response(
                mood=mood,
                energy_level=energy,
                tone_level=tone_level
            )
            
            # Validate tone before returning
            is_valid, violations = self._copilot_service.validate_message_tone(response)
            if not is_valid:
                # Fallback to safe message if validation fails
                return self._get_fallback_mood_response(mood, energy, tone_level)
            
            return response
            
        except Exception as e:
            print(f"Error generating mood response: {e}")
            return self._get_fallback_mood_response(mood, energy, tone_level)
    
    def _get_fallback_mood_response(self, mood: str, energy: str, tone_level: str) -> str:
        """
        Get fallback mood response if generation fails.
        
        Args:
            mood: User's mood
            energy: User's energy level
            tone_level: Tone to use
            
        Returns:
            Fallback response text
        """
        # Tone-aware fallbacks
        gentle_responses = {
            "happy": "That's wonderful! Keep enjoying this positive energy. 🌟",
            "neutral": "I'm here to support you at your own pace.",
            "stressed": "I know things feel heavy right now. Remember: one step at a time.",
            "sad": "I'm sorry you're feeling down. Let's take this together.",
        }
        
        normal_responses = {
            "happy": "That's great! Ready to make the most of it? 💪",
            "neutral": "Let me know how I can help today.",
            "stressed": "You've got this. I'm here to help ease things.",
            "sad": "Better times are ahead. I'm here for support.",
        }
        
        encouraging_responses = {
            "happy": "Excellent! You're in a great state. Let's go crush some goals! 🚀",
            "neutral": "Let's turn this into a productive day together!",
            "stressed": "Your energy is amazing—let's channel it productively.",
            "sad": "Let's find something that lifts your spirits.",
        }
        
        # Select response map based on tone level
        responses = {
            "gentle": gentle_responses,
            "normal": normal_responses,
            "encouraging": encouraging_responses,
        }.get(tone_level, normal_responses)
        
        # Get response for mood, with fallback
        return responses.get(mood, "I'm here to support you. 💙")
    
    def _display_mood_response(self, response_text: str, mood_checkin: MoodCheckIn,
                               tone_level: str) -> Optional[str]:
        """
        Display mood response via co-pilot ViewModel.
        
        Args:
            response_text: Response message text
            mood_checkin: MoodCheckIn data for context
            tone_level: Tone level used
            
        Returns:
            Message ID if displayed, None otherwise
        """
        try:
            # Update co-pilot context with mood data
            if self._copilot_service:
                self._copilot_service.update_user_context(
                    activity_state=UserActivityState.ACTIVE,
                    is_in_focus_mode=False
                )
            
            # Generate unique message ID
            import uuid
            message_id = str(uuid.uuid4())
            
            # Display via co-pilot ViewModel
            self._copilot_viewmodel.display_message(
                message_text=response_text,
                message_id=message_id,
                auto_dismiss_ms=10000  # 10 seconds for mood response
            )
            
            # Store in communication history with mood context
            if self._copilot_service:
                event = self._copilot_service.save_communication_event(
                    message_text=response_text,
                    category="mood_response",
                    tone_level=tone_level,
                    message_id=message_id,
                    user_mood=mood_checkin.mood_level,
                    user_energy_level=self._energy_to_scale(mood_checkin.energy_level)
                )
            
            return message_id
            
        except Exception as e:
            self.integrationError.emit(f"Failed to display mood response: {str(e)}")
            return None
    
    def _energy_to_scale(self, energy: str) -> int:
        """
        Convert energy level string to 1-10 scale.
        
        Args:
            energy: Energy level (high, medium, low)
            
        Returns:
            Energy level as 1-10 integer
        """
        scale = {
            "high": 8,
            "medium": 5,
            "low": 2,
        }
        return scale.get(energy, 5)
    
    def get_last_mood_context(self) -> Optional[dict]:
        """
        Get context from last mood check-in.
        
        Useful for adapting behavior based on recent mood data.
        
        Returns:
            Dict with mood, energy, response_time, or None if no data
        """
        if not self._last_mood:
            return None
        
        return {
            "mood": self._last_mood,
            "energy": self._last_energy,
            "response_time": self._last_response_time,
            "tone_level": self._determine_tone_level(self._last_mood, self._last_energy),
        }
    
    def cleanup(self):
        """Clean up integration resources."""
        if self._mood_service:
            self._mood_service.close()

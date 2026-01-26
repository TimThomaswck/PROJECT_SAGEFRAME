"""
MVVM ViewModel Layer for Co-Pilot Communication

Bridges the CommunicationService (Model) and UI Components (View).
Implements Qt property system for data binding and emits signals for UI updates.

Architecture:
    Model: CommunicationService (business logic, database, message generation)
    ViewModel: CopilotViewModel (state management, properties, signal coordination)
    View: PySide6 UI Components (display, user interaction)

Signal Flow:
    User Action (dismiss) → View emits signal → ViewModel slot → Service updates → ViewModel property changes → View updates

Property Binding:
    PySide6 property system for reactive data binding (currentMessage, isMessagePending, etc.)

Context Awareness:
    Automatically defers or queues messages based on user activity state, flow mode, DND status
"""

from typing import Optional, List
from datetime import datetime
from enum import Enum

from PySide6.QtCore import QObject, Signal, Property, Slot
from sqlalchemy.orm import Session

from app.modules.ai_copilot.services import CopilotCommunicationService
from app.modules.ai_copilot.models import CommunicationEvent, UserContext


class UserActivityState(Enum):
    """Enum representing user activity states for context-aware delivery."""
    IDLE = "idle"  # No activity for >5 minutes
    ACTIVE = "active"  # Normal activity, safe to interrupt
    FLOW_STATE = "flow_state"  # Deep focus, do not interrupt


class MessageIntrusiveness(Enum):
    """Enum representing message intrusiveness level."""
    GENTLE = "gentle"  # Can deliver anytime (e.g., encouragement after task)
    SUBTLE = "subtle"  # Defer during flow state only
    IMPORTANT = "important"  # Deliver ASAP despite flow state


class CopilotViewModel(QObject):
    """
    MVVM ViewModel for co-pilot communication.
    
    Coordinates between CommunicationService (model) and PySide6 UI components (view).
    Manages state, properties, and signal emissions for reactive UI updates.
    
    Key Responsibilities:
    1. Message Generation: Delegate to service, emit signals
    2. Context Awareness: Check user state before delivery, queue if needed
    3. State Management: Track current message, pending delivery, etc.
    4. Signal Coordination: Emit signals for UI reactions (messageReady, messageDisplayed, etc.)
    5. Property Management: Qt properties for data binding (currentMessage, isMessagePending)
    """
    
    # Signals (verbNoun naming convention)
    messageReady = Signal(str)  # Emitted when message is generated and ready for display
    messageDisplayed = Signal(str)  # Emitted when message is shown to user
    messageDismissed = Signal(str)  # Emitted when user dismisses message
    messageAcknowledged = Signal(str)  # Emitted when user acknowledges message
    messageQueued = Signal(str)  # Emitted when message is queued (deferred)
    errorOccurred = Signal(str)  # Emitted when error occurs during generation/delivery
    
    # Property change signals
    currentMessageChanged = Signal(str)
    isMessagePendingChanged = Signal(bool)
    userActivityStateChanged = Signal(str)  # Activity state enum as string
    
    def __init__(self, db_session: Session):
        """
        Initialize ViewModel with database session.
        
        Args:
            db_session: SQLAlchemy Session for database operations
        """
        super().__init__()
        self.communication_service = CopilotCommunicationService(db_session)
        
        # State management
        self._current_message: Optional[str] = None
        self._current_message_id: Optional[str] = None
        self._is_message_pending: bool = False
        self._activity_state: UserActivityState = UserActivityState.ACTIVE
        self._message_queue: List[tuple[str, str]] = []  # [(message_text, message_id), ...]
        
        # Connect service signals to ViewModel slots if needed
        # (can be expanded for service-level signal integration)
    
    # ============================================================================
    # Qt Properties for Data Binding
    # ============================================================================
    
    @Property(str, notify=currentMessageChanged)
    def currentMessage(self) -> str:
        """Get current message text."""
        return self._current_message or ""
    
    @currentMessage.setter
    def currentMessage(self, value: str):
        """Set current message text and notify."""
        if self._current_message != value:
            self._current_message = value
            self.currentMessageChanged.emit(value)
    
    @Property(bool, notify=isMessagePendingChanged)
    def isMessagePending(self) -> bool:
        """Check if message is pending display."""
        return self._is_message_pending
    
    @isMessagePending.setter
    def isMessagePending(self, value: bool):
        """Set pending state and notify."""
        if self._is_message_pending != value:
            self._is_message_pending = value
            self.isMessagePendingChanged.emit(value)
    
    @Property(str, notify=userActivityStateChanged)
    def userActivityState(self) -> str:
        """Get current user activity state as string."""
        return self._activity_state.value
    
    @userActivityState.setter
    def userActivityState(self, value: str):
        """Set user activity state and notify."""
        try:
            new_state = UserActivityState(value)
            if self._activity_state != new_state:
                self._activity_state = new_state
                self.userActivityStateChanged.emit(value)
        except ValueError:
            self.errorOccurred.emit(f"Invalid activity state: {value}")
    
    # ============================================================================
    # Message Generation Methods
    # ============================================================================
    
    def generate_greeting(self, tone_level: str = "normal") -> str:
        """
        Generate a greeting message.
        
        Args:
            tone_level: Tone level ("warm", "formal", "normal")
            
        Returns:
            Generated greeting message
        """
        try:
            message = self.communication_service.generate_greeting(tone_level)
            self._set_current_message(message)
            return message
        except Exception as e:
            self.errorOccurred.emit(f"Failed to generate greeting: {str(e)}")
            return self.get_fallback_message("greeting")
    
    def generate_encouragement(self, tone_level: str = "normal") -> str:
        """
        Generate an encouragement message.
        
        Args:
            tone_level: Tone level ("warm", "formal", "normal")
            
        Returns:
            Generated encouragement message
        """
        try:
            message = self.communication_service.generate_encouragement(tone_level)
            self._set_current_message(message)
            return message
        except Exception as e:
            self.errorOccurred.emit(f"Failed to generate encouragement: {str(e)}")
            return self.get_fallback_message("encouragement")
    
    def generate_mood_response(self, mood: str, energy_level: str, tone_level: str = "normal") -> str:
        """
        Generate a mood-aware response.
        
        Args:
            mood: User mood (e.g., "focused", "stressed", "tired")
            energy_level: Energy level (e.g., "high", "normal", "low")
            tone_level: Tone level ("warm", "formal", "normal")
            
        Returns:
            Generated mood response message
        """
        try:
            message = self.communication_service.generate_mood_response(mood, energy_level, tone_level)
            self._set_current_message(message)
            return message
        except Exception as e:
            self.errorOccurred.emit(f"Failed to generate mood response: {str(e)}")
            return self.get_fallback_message("mood_response")
    
    def generate_task_suggestion(self, task_name: str, tone_level: str = "normal") -> str:
        """
        Generate a task suggestion message.
        
        Args:
            task_name: Name of the task to suggest
            tone_level: Tone level ("warm", "formal", "normal")
            
        Returns:
            Generated task suggestion message
        """
        try:
            message = self.communication_service.generate_task_suggestion(task_name, tone_level)
            self._set_current_message(message)
            return message
        except Exception as e:
            self.errorOccurred.emit(f"Failed to generate task suggestion: {str(e)}")
            return self.get_fallback_message("task_suggestion")
    
    def generate_break_suggestion(self, tone_level: str = "normal") -> str:
        """
        Generate a break suggestion message.
        
        Args:
            tone_level: Tone level ("warm", "formal", "normal")
            
        Returns:
            Generated break suggestion message
        """
        try:
            message = self.communication_service.generate_break_suggestion(tone_level)
            self._set_current_message(message)
            return message
        except Exception as e:
            self.errorOccurred.emit(f"Failed to generate break suggestion: {str(e)}")
            return self.get_fallback_message("break_suggestion")
    
    # ============================================================================
    # Message Display Coordination
    # ============================================================================
    
    def display_message(self, message_text: str, message_id: str, auto_dismiss_ms: int = 8000) -> bool:
        """
        Display a message, respecting user context.
        
        If user is in flow state or DND mode, message is queued instead.
        
        Args:
            message_text: Message text to display
            message_id: Unique message ID
            auto_dismiss_ms: Auto-dismiss timeout in milliseconds
            
        Returns:
            True if message displayed, False if queued
        """
        try:
            # Check if message should be deferred
            if self.should_defer_message():
                self._queue_message(message_text, message_id)
                self.messageQueued.emit(message_id)
                return False
            
            # Message can be displayed immediately
            self.currentMessage = message_text
            self._current_message_id = message_id
            self.isMessagePending = True
            self.messageReady.emit(message_id)
            self.messageDisplayed.emit(message_id)
            return True
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to display message: {str(e)}")
            return False
    
    def should_defer_message(self) -> bool:
        """
        Check if message should be deferred based on user context.
        
        Message is deferred if:
        1. User is in flow state (FLOW_STATE)
        2. User has do-not-disturb mode enabled
        3. User is in focus mode (future Story 1.3 integration)
        
        Returns:
            True if message should be deferred, False if safe to display
        """
        # Check activity state
        if self._activity_state == UserActivityState.FLOW_STATE:
            return True
        
        # Check DND mode via service
        if self.communication_service.should_defer_message():
            return True
        
        return False
    
    # ============================================================================
    # User Interaction Handlers
    # ============================================================================
    
    @Slot(str)
    def on_message_dismissed(self, message_id: str):
        """
        Handle message dismissal.
        
        Args:
            message_id: ID of dismissed message
        """
        try:
            self.communication_service.mark_message_dismissed(message_id)
            self.messageDismissed.emit(message_id)
            self.isMessagePending = False
            self._current_message_id = None
            
            # Process queued messages if DND ended
            self.process_message_queue()
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to handle dismissal: {str(e)}")
    
    @Slot(str)
    def on_message_acknowledged(self, message_id: str):
        """
        Handle message acknowledgment.
        
        Args:
            message_id: ID of acknowledged message
        """
        try:
            self.communication_service.mark_message_acknowledged(message_id)
            self.messageAcknowledged.emit(message_id)
            self.isMessagePending = False
            self._current_message_id = None
            
            # Process queued messages
            self.process_message_queue()
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to handle acknowledgment: {str(e)}")
    
    # ============================================================================
    # Context Awareness
    # ============================================================================
    
    def update_activity_state(self, activity_state: UserActivityState):
        """
        Update user activity state.
        
        Args:
            activity_state: New activity state
        """
        self._activity_state = activity_state
        self.userActivityState = activity_state.value
        
        # Check if we can process queued messages
        if activity_state != UserActivityState.FLOW_STATE:
            self.process_message_queue()
    
    def set_do_not_disturb(self, duration_minutes: int):
        """
        Enable do-not-disturb mode.
        
        Args:
            duration_minutes: Duration in minutes
        """
        self.communication_service.set_do_not_disturb(duration_minutes)
    
    def clear_do_not_disturb(self):
        """Disable do-not-disturb mode and process queued messages."""
        self.communication_service.clear_do_not_disturb()
        self.process_message_queue()
    
    def get_optimal_delivery_time(self, message_intrusiveness: str) -> Optional[datetime]:
        """
        Determine optimal delivery time for message based on intrusiveness.
        
        Args:
            message_intrusiveness: Intrusiveness level ("gentle", "subtle", "important")
            
        Returns:
            Optimal datetime for delivery, or None if should deliver now
        """
        try:
            intrusiveness = MessageIntrusiveness(message_intrusiveness)
            
            if intrusiveness == MessageIntrusiveness.IMPORTANT:
                # Deliver ASAP
                return None
            elif intrusiveness == MessageIntrusiveness.SUBTLE:
                # Deliver when not in flow state
                if self._activity_state == UserActivityState.FLOW_STATE:
                    return datetime.now()  # Placeholder, actual timing handled by deferral
                return None
            else:  # GENTLE
                # Can deliver anytime
                return None
                
        except ValueError:
            self.errorOccurred.emit(f"Invalid intrusiveness level: {message_intrusiveness}")
            return None
    
    # ============================================================================
    # Message Queue Management
    # ============================================================================
    
    def _queue_message(self, message_text: str, message_id: str):
        """Queue a message for later delivery."""
        self._message_queue.append((message_text, message_id))
    
    def get_queued_messages(self) -> List[tuple[str, str]]:
        """Get list of queued messages."""
        return self._message_queue.copy()
    
    def process_message_queue(self):
        """
        Process queued messages and display them if conditions allow.
        
        Called when:
        1. DND mode ends
        2. User exits flow state
        3. Message is dismissed/acknowledged
        """
        while self._message_queue and not self.should_defer_message():
            message_text, message_id = self._message_queue.pop(0)
            self.display_message(message_text, message_id)
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def _set_current_message(self, message: str):
        """Set current message and emit signal."""
        self.currentMessage = message
        self.isMessagePending = True
        self.messageReady.emit(message)
    
    def get_fallback_message(self, message_type: str) -> str:
        """
        Get fallback message if generation fails.
        
        Args:
            message_type: Type of message ("greeting", "encouragement", etc.)
            
        Returns:
            Fallback message text
        """
        fallbacks = {
            "greeting": "Hi there! 👋 Ready to get things done?",
            "encouragement": "You're doing great! Keep up the momentum! 💪",
            "mood_response": "I'm here to support you. Let me know how I can help.",
            "task_suggestion": "How about taking a quick break? You've been working hard.",
            "break_suggestion": "How about a quick stretch or some water? Your well-being matters.",
        }
        return fallbacks.get(message_type, "I'm here to help!")
    
    def cleanup(self):
        """Perform cleanup on ViewModel destruction."""
        # Clear queued messages
        self._message_queue.clear()
        
        # Reset state
        self._current_message = None
        self._current_message_id = None
        self._is_message_pending = False
    
    def destroy(self):
        """Alias for cleanup for compatibility."""
        self.cleanup()

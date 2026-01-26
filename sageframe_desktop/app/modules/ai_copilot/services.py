"""
Core AI Co-Pilot Communication Service.

Manages message generation, tone validation, context awareness,
and delivery preferences.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import random

from sqlalchemy.orm import Session

from app.modules.ai_copilot.models import (
    CommunicationEvent,
    UserContext,
    MessageStatus,
    UserActivityState,
    CommunicationEventSchema,
)
from app.modules.ai_copilot.persona import (
    JARVIS,
    MessageCategory,
    ToneLevel,
)


class CopilotCommunicationService:
    """
    Service for generating and managing co-pilot communication.
    
    Responsibilities:
    - Generate messages with enforced empathetic tone
    - Validate messages for forbidden phrases and jargon
    - Track delivery context and user interaction
    - Manage message queue and deferred delivery
    - Store communication history in SQLite
    
    Architecture note: Designed for future LLM integration. Currently
    uses template-based messages for MVP. LLM provider can be swapped
    in via dependency injection without changing core service logic.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize the communication service.
        
        Args:
            db_session: SQLAlchemy session for database operations.
        """
        self.db = db_session
        self.message_queue: List[str] = []  # message_id queue
    
    def generate_greeting(self, tone_level: ToneLevel = ToneLevel.GENTLE) -> str:
        """
        Generate a greeting message.
        
        Args:
            tone_level: Intensity of the greeting tone.
            
        Returns:
            A greeting message.
        """
        templates = JARVIS.get_templates_for_category(MessageCategory.GREETING)
        if not templates:
            return "Hello! I'm here to help."
        return random.choice(templates)
    
    def generate_mood_response(
        self,
        mood: str,
        energy_level: int,
        tone_level: ToneLevel = ToneLevel.GENTLE,
    ) -> str:
        """
        Generate an empathetic response based on user's mood and energy.
        
        Args:
            mood: User's reported mood (high_energy, low_energy, stressed, focused).
            energy_level: 1-10 scale of energy.
            tone_level: Intensity of the response tone.
            
        Returns:
            A mood-appropriate response.
        """
        templates = JARVIS.get_templates_for_category(MessageCategory.MOOD_RESPONSE)
        if not templates:
            return "I'm here for you."
        
        # In MVP, simple random selection. Future LLM could generate contextual responses.
        return random.choice(templates)
    
    def generate_task_suggestion(
        self,
        task_name: str,
        tone_level: ToneLevel = ToneLevel.GENTLE,
    ) -> str:
        """
        Generate a task suggestion message.
        
        Args:
            task_name: Name of the task to suggest.
            tone_level: Intensity of the suggestion tone.
            
        Returns:
            A task suggestion message.
        """
        templates = JARVIS.get_templates_for_category(MessageCategory.TASK_SUGGESTION)
        if not templates:
            return f"Would you like to work on {task_name}?"
        
        template = random.choice(templates)
        # Simple template substitution for MVP
        return template.format(task_name=task_name)
    
    def generate_encouragement(
        self,
        tone_level: ToneLevel = ToneLevel.ENCOURAGING,
    ) -> str:
        """
        Generate an encouragement message.
        
        Args:
            tone_level: Intensity of the encouragement.
            
        Returns:
            An encouraging message.
        """
        templates = JARVIS.get_templates_for_category(MessageCategory.ENCOURAGEMENT)
        if not templates:
            return "You're doing great!"
        return random.choice(templates)
    
    def generate_gentle_reminder(
        self,
        task_name: str,
        tone_level: ToneLevel = ToneLevel.MINIMAL,
    ) -> str:
        """
        Generate a gentle reminder (low intrusiveness).
        
        Args:
            task_name: Task to remind about.
            tone_level: Intensity (typically minimal for reminders).
            
        Returns:
            A gentle reminder message.
        """
        templates = JARVIS.get_templates_for_category(MessageCategory.GENTLE_REMINDER)
        if not templates:
            return f"Just a thought: {task_name}."
        
        template = random.choice(templates)
        return template.format(task_name=task_name, event=task_name)
    
    def generate_break_suggestion(
        self,
        tone_level: ToneLevel = ToneLevel.GENTLE,
    ) -> str:
        """
        Generate a break suggestion message.
        
        Args:
            tone_level: Intensity of the suggestion.
            
        Returns:
            A break suggestion message.
        """
        templates = JARVIS.get_templates_for_category(MessageCategory.BREAK_SUGGESTION)
        if not templates:
            return "Perhaps a short break could help."
        return random.choice(templates)
    
    def validate_message_tone(self, message: str) -> tuple[bool, Optional[str]]:
        """
        Validate message tone compliance.
        
        Checks for forbidden phrases, jargon, and anxiety-inducing language.
        
        Args:
            message: The message to validate.
            
        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is None.
        """
        # Check for forbidden phrases
        if JARVIS.is_forbidden_phrase(message):
            return False, "Message contains forbidden phrase that violates tone guidelines."
        
        # Additional jargon checks
        jargon_patterns = [
            "error",
            "failed",
            "warning",
            "critical",
            "problem",
            "mistake",
            "invalid",
            "incorrect",
        ]
        
        message_lower = message.lower()
        for pattern in jargon_patterns:
            if pattern in message_lower:
                return False, f"Message contains jargon '{pattern}' that may cause user anxiety."
        
        # Check for ALL CAPS (typically perceived as shouting)
        if len(message) > 10 and message.isupper():
            return False, "Message uses all capitals, which may seem aggressive."
        
        return True, None
    
    def save_communication_event(
        self,
        message_text: str,
        category: str,
        tone_level: str = "gentle",
        user_mood: Optional[str] = None,
        user_energy_level: Optional[int] = None,
        status: MessageStatus = MessageStatus.GENERATED,
        message_id: Optional[str] = None,
    ) -> str:
        """
        Save a communication event to the database.
        
        Args:
            message_text: The generated message.
            category: Message category (greeting, suggestion, mood_response, etc).
            tone_level: Tone intensity (minimal, gentle, encouraging, celebratory).
            user_mood: User's mood at time of generation (optional).
            user_energy_level: User's energy level 1-10 (optional).
            status: Initial status of the message.
            message_id: Optional UUID (generates new if not provided).
            
        Returns:
            The message_id (UUID).
            
        Raises:
            ValueError: If tone validation fails.
        """
        # Validate tone before saving
        is_valid, error_msg = self.validate_message_tone(message_text)
        if not is_valid:
            raise ValueError(f"Message tone validation failed: {error_msg}")
        
        # Create event with provided or generated message_id
        if not message_id:
            message_id = str(uuid.uuid4())
        
        event = CommunicationEvent(
            message_id=message_id,
            category=category,
            message_text=message_text,
            tone_level=tone_level,
            status=status,
            user_mood=user_mood,
            user_energy_level=user_energy_level,
            generated_at=datetime.now(timezone.utc),
        )
        
        self.db.add(event)
        self.db.commit()
        
        return message_id
    
    def mark_message_delivered(self, message_id: str) -> bool:
        """
        Mark a message as delivered to the user.
        
        Args:
            message_id: The message UUID.
            
        Returns:
            True if successful, False if not found.
        """
        event = self.db.query(CommunicationEvent).filter_by(message_id=message_id).first()
        if not event:
            return False
        
        event.status = MessageStatus.DELIVERED
        event.delivered_at = datetime.now(timezone.utc)
        event.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return True
    
    def mark_message_dismissed(self, message_id: str) -> bool:
        """
        Mark a message as dismissed by the user.
        
        Args:
            message_id: The message UUID.
            
        Returns:
            True if successful, False if not found.
        """
        event = self.db.query(CommunicationEvent).filter_by(message_id=message_id).first()
        if not event:
            return False
        
        event.status = MessageStatus.DISMISSED
        event.dismissed_at = datetime.now(timezone.utc)
        event.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return True
    
    def mark_message_acknowledged(self, message_id: str) -> bool:
        """
        Mark a message as acknowledged (user clicked "OK" or similar).
        
        Args:
            message_id: The message UUID.
            
        Returns:
            True if successful, False if not found.
        """
        event = self.db.query(CommunicationEvent).filter_by(message_id=message_id).first()
        if not event:
            return False
        
        event.status = MessageStatus.ACKNOWLEDGED
        event.acknowledged_at = datetime.now(timezone.utc)
        event.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return True
    
    def get_communication_history(self, limit: int = 50) -> List[CommunicationEvent]:
        """
        Retrieve recent communication history.
        
        Args:
            limit: Maximum number of events to retrieve.
            
        Returns:
            List of recent CommunicationEvent objects.
        """
        return self.db.query(CommunicationEvent).order_by(
            CommunicationEvent.generated_at.desc()
        ).limit(limit).all()
    
    def update_user_context(self, activity_state: UserActivityState, is_in_focus_mode: bool = False) -> None:
        """
        Update user's current activity context.
        
        Args:
            activity_state: Current activity state (idle, active, flow_state).
            is_in_focus_mode: Whether user is in focus mode.
        """
        context = self.db.query(UserContext).first()
        if not context:
            context = UserContext(
                activity_state=activity_state,
                is_in_focus_mode=is_in_focus_mode,
            )
            self.db.add(context)
        else:
            context.activity_state = activity_state
            is_in_focus_mode = is_in_focus_mode
            context.last_activity_at = datetime.now(timezone.utc)
            context.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
    
    def get_user_context(self) -> Optional[UserContext]:
        """
        Retrieve the current user context.
        
        Returns:
            UserContext object or None if not initialized.
        """
        return self.db.query(UserContext).first()
    
    def should_defer_message(self) -> bool:
        """
        Determine if a message should be deferred based on user context.
        
        Respects:
        - Flow state (do not interrupt)
        - Do Not Disturb mode
        - Recent activity
        
        Returns:
            True if message should be deferred, False if safe to deliver.
        """
        context = self.get_user_context()
        if not context:
            return False
        
        # Never interrupt flow state
        if context.activity_state == UserActivityState.FLOW_STATE:
            return True
        
        # Never interrupt focus mode
        if context.is_in_focus_mode:
            return True
        
        # Respect Do Not Disturb until time
        if context.do_not_disturb_until:
            now = datetime.now(timezone.utc)
            dnd_until = context.do_not_disturb_until
            
            # Handle SQLite storing naive datetimes
            if dnd_until.tzinfo is None:
                now = now.replace(tzinfo=None)
            
            if now < dnd_until:
                return True
        
        return False
    
    def set_do_not_disturb(self, duration_minutes: int) -> None:
        """
        Set Do Not Disturb mode for specified duration.
        
        Args:
            duration_minutes: Number of minutes for DND mode.
        """
        context = self.get_user_context()
        if not context:
            context = UserContext()
            self.db.add(context)
        
        context.do_not_disturb_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        context.updated_at = datetime.now(timezone.utc)
        self.db.commit()
    
    def clear_do_not_disturb(self) -> None:
        """
        Clear Do Not Disturb mode, allowing messages to be delivered immediately.
        """
        context = self.get_user_context()
        if context:
            context.do_not_disturb_until = None
            context.updated_at = datetime.now(timezone.utc)
            self.db.commit()
    
    def get_optimal_delivery_time(self) -> Optional[datetime]:
        """
        Determine optimal time to deliver next message.
        
        Considers:
        - User activity state
        - DND mode
        - Message queue status
        
        Returns:
            datetime if message should be deferred, None if deliver immediately
        """
        context = self.get_user_context()
        
        # If in DND mode, return DND end time
        if context and context.do_not_disturb_until:
            now = datetime.now(timezone.utc)
            dnd_until = context.do_not_disturb_until
            
            # Handle SQLite storing naive datetimes
            if dnd_until.tzinfo is None:
                now = now.replace(tzinfo=None)
            
            if now < dnd_until:
                return dnd_until
        
        # If in flow state, message is deferred but no specific time
        if context and context.activity_state == UserActivityState.FLOW_STATE:
            # Return a generic future time (not a specific scheduling time)
            return None  # Caller should handle deferred delivery
        
        # Safe to deliver now
        return None
    
    @property
    def delivery_preferences(self) -> dict:
        """
        Get message delivery preferences based on current context.
        
        Returns:
            Dict with preferences for tone, timing, urgency level
        """
        context = self.get_user_context()
        
        # Handle DND mode with timezone-aware comparison
        is_in_dnd = False
        if context and context.do_not_disturb_until:
            now = datetime.now(timezone.utc)
            dnd_until = context.do_not_disturb_until
            
            # Handle SQLite storing naive datetimes
            if dnd_until.tzinfo is None:
                now = now.replace(tzinfo=None)
            
            is_in_dnd = now < dnd_until
        
        preferences = {
            "can_deliver_now": not self.should_defer_message(),
            "is_in_dnd_mode": is_in_dnd,
            "activity_state": context.activity_state.value if context else "unknown",
            "tone_level": "gentle",  # Default to gentle tone
            "max_wait_minutes": 30,  # Default max deferral time
        }
        
        return preferences

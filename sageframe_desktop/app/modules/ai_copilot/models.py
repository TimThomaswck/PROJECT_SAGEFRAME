"""
SQLAlchemy and Pydantic models for AI Co-Pilot communication.

Models for:
- User context (idle, active, flow state)
- Communication events (generated messages, delivery status)
- Message schemas for validation
"""

from datetime import datetime, timezone
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, Enum
from pydantic import BaseModel, Field

from app.database import Base


class UserActivityState(str, PyEnum):
    """User's current activity state."""
    IDLE = "idle"
    ACTIVE = "active"
    FLOW_STATE = "flow_state"
    IN_FOCUS_MODE = "in_focus_mode"


class MessageStatus(str, PyEnum):
    """Status of a communication event."""
    GENERATED = "generated"
    QUEUED = "queued"
    DELIVERED = "delivered"
    DISMISSED = "dismissed"
    ACKNOWLEDGED = "acknowledged"
    DEFERRED = "deferred"


# =============================================================================
# SQLAlchemy Models (Database)
# =============================================================================

class UserContext(Base):
    """
    Stores user context for intelligent message delivery.
    
    Tracks user's current state (idle, active, flow state) to avoid
    interrupting during focus periods.
    """
    
    __tablename__ = "user_context"
    
    id = Column(Integer, primary_key=True)
    activity_state = Column(Enum(UserActivityState), default=UserActivityState.ACTIVE)
    is_in_focus_mode = Column(Boolean, default=False)
    last_activity_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    do_not_disturb_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<UserContext(id={self.id}, activity_state={self.activity_state}, focus_mode={self.is_in_focus_mode})>"


class CommunicationEvent(Base):
    """
    Stores all communication events from the co-pilot.
    
    Provides a complete history of messages for learning, refinement,
    and compliance tracking.
    """
    
    __tablename__ = "communication_events"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(36), unique=True)  # UUID
    category = Column(String(50), nullable=False)  # greeting, suggestion, encouragement, etc.
    message_text = Column(Text, nullable=False)
    tone_level = Column(String(20), default="gentle")  # minimal, gentle, encouraging, celebratory
    status = Column(Enum(MessageStatus), default=MessageStatus.GENERATED)
    
    # Context at time of generation
    user_mood = Column(String(20), nullable=True)  # high_energy, low_energy, stressed, focused
    user_energy_level = Column(Integer, nullable=True)  # 1-10 scale
    
    # Delivery metadata
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    delivered_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Feedback
    user_feedback = Column(String(20), nullable=True)  # helpful, neutral, unhelpful
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<CommunicationEvent(id={self.id}, category={self.category}, status={self.status})>"


# =============================================================================
# Pydantic Models (Validation)
# =============================================================================

class UserContextSchema(BaseModel):
    """Pydantic schema for validating UserContext data."""
    
    activity_state: UserActivityState = UserActivityState.ACTIVE
    is_in_focus_mode: bool = False
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    do_not_disturb_until: Optional[datetime] = None
    
    class Config:
        """Pydantic config."""
        use_enum_values = False


class CommunicationEventSchema(BaseModel):
    """Pydantic schema for validating CommunicationEvent data."""
    
    message_id: str  # UUID
    category: str
    message_text: str
    tone_level: str = "gentle"
    status: MessageStatus = MessageStatus.GENERATED
    user_mood: Optional[str] = None
    user_energy_level: Optional[int] = Field(None, ge=1, le=10)
    user_feedback: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        use_enum_values = False


class MessagePayloadSchema(BaseModel):
    """Schema for co-pilot message signal payloads."""
    
    message_id: str
    text: str
    category: str
    tone_level: str
    is_dismissible: bool = True
    auto_dismiss_seconds: Optional[int] = None
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "message_id": "550e8400-e29b-41d4-a716-446655440000",
                "text": "You're making great progress!",
                "category": "encouragement",
                "tone_level": "encouraging",
                "is_dismissible": True,
                "auto_dismiss_seconds": None,
            }
        }

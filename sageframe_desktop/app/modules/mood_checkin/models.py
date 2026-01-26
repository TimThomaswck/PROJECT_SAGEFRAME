"""Data models for mood check-in functionality.

This module defines the SQLAlchemy ORM model and Pydantic schema for mood check-ins.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base

# Valid mood and energy level values
VALID_MOOD_LEVELS = ["happy", "neutral", "stressed", "sad"]
VALID_ENERGY_LEVELS = ["high", "medium", "low"]


class MoodCheckIn(Base):
    """SQLAlchemy model for mood check-ins.
    
    Stores user mood and energy level data with timestamps.
    Follows snake_case naming convention as per architecture.
    """
    
    __tablename__ = 'mood_check_ins'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)  # Prepared for future multi-tenancy (no FK yet)
    mood_level = Column(String(50), nullable=False)  # e.g., "happy", "neutral", "stressed"
    energy_level = Column(String(50), nullable=False)  # e.g., "high", "medium", "low"
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    notes = Column(Text, nullable=True)  # Optional user notes
    
    def __repr__(self) -> str:
        return f"<MoodCheckIn(id={self.id}, mood={self.mood_level}, energy={self.energy_level}, timestamp={self.timestamp})>"


class MoodCheckInSchema(BaseModel):
    """Pydantic schema for mood check-in data validation.
    
    Validates mood and energy level inputs before persisting to database.
    Hybrid approach: SQLAlchemy + Pydantic as per architecture.
    """
    
    mood_level: Literal["happy", "neutral", "stressed", "sad"] = Field(..., description="User's current mood")
    energy_level: Literal["high", "medium", "low"] = Field(..., description="User's current energy level")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional user notes")
    
    @field_validator('mood_level')
    @classmethod
    def validate_mood_level(cls, v: str) -> str:
        """Validate mood level is not empty."""
        if not v or not v.strip():
            raise ValueError("Mood level cannot be empty")
        return v.strip()
    
    @field_validator('energy_level')
    @classmethod
    def validate_energy_level(cls, v: str) -> str:
        """Validate energy level is not empty."""
        if not v or not v.strip():
            raise ValueError("Energy level cannot be empty")
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True

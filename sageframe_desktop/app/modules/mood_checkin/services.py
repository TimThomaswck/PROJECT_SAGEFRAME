"""Business logic service for mood check-ins.

This module provides service layer functionality for managing mood check-in data.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.modules.mood_checkin.models import MoodCheckIn, MoodCheckInSchema


class MoodCheckInService:
    """Service class for mood check-in business logic.
    
    Handles data validation, persistence, and retrieval for mood check-ins.
    Follows the service pattern to separate business logic from UI (MVVM).
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """Initialize service with optional database session.
        
        Args:
            db_session: SQLAlchemy session (optional, creates new if not provided)
            
        Raises:
            Exception: If database session cannot be created
        """
        if db_session is not None:
            self._db = db_session
            self._owns_session = False
        else:
            try:
                self._db = SessionLocal()
                self._owns_session = True
            except Exception as e:
                raise Exception(f"Failed to initialize database session: {e}") from e
    
    def create_mood_checkin(
        self,
        mood_level: str,
        energy_level: str,
        notes: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> MoodCheckIn:
        """Create and save a new mood check-in.
        
        Args:
            mood_level: User's current mood (e.g., "happy", "neutral", "stressed")
            energy_level: User's current energy level (e.g., "high", "medium", "low")
            notes: Optional user notes
            user_id: Optional user ID (for future multi-tenancy)
        
        Returns:
            MoodCheckIn: The created mood check-in record
        
        Raises:
            ValueError: If validation fails
            Exception: If database operation fails
        """
        try:
            # Validate input using Pydantic schema (hybrid validation approach)
            validated_data = MoodCheckInSchema(
                mood_level=mood_level,
                energy_level=energy_level,
                notes=notes
            )
            
            # Create SQLAlchemy model instance
            mood_checkin = MoodCheckIn(
                mood_level=validated_data.mood_level,
                energy_level=validated_data.energy_level,
                notes=validated_data.notes,
                user_id=user_id,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Persist to database
            self._db.add(mood_checkin)
            self._db.commit()
            self._db.refresh(mood_checkin)
            
            return mood_checkin
            
        except ValidationError as e:
            # Pydantic validation failed
            raise ValueError(f"Mood check-in validation failed: {e}")
        except Exception as e:
            # Database or other error
            self._db.rollback()
            raise Exception(f"Failed to create mood check-in: {e}")
    
    def get_recent_mood_checkins(self, limit: int = 10, user_id: Optional[int] = None) -> List[MoodCheckIn]:
        """Get recent mood check-ins.
        
        Args:
            limit: Maximum number of records to return
            user_id: Optional user ID filter (for future multi-tenancy)
        
        Returns:
            List[MoodCheckIn]: List of mood check-in records, most recent first
        """
        query = self._db.query(MoodCheckIn)
        
        if user_id is not None:
            query = query.filter(MoodCheckIn.user_id == user_id)
        
        return query.order_by(MoodCheckIn.timestamp.desc()).limit(limit).all()
    
    def get_last_mood_checkin(self, user_id: Optional[int] = None) -> Optional[MoodCheckIn]:
        """Get the most recent mood check-in.
        
        Args:
            user_id: Optional user ID filter (for future multi-tenancy)
        
        Returns:
            MoodCheckIn or None: Most recent mood check-in, or None if no records exist
        """
        query = self._db.query(MoodCheckIn)
        
        if user_id is not None:
            query = query.filter(MoodCheckIn.user_id == user_id)
        
        return query.order_by(MoodCheckIn.timestamp.desc()).first()
    
    def close(self):
        """Close database session if owned by this service."""
        if self._owns_session:
            self._db.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.close()

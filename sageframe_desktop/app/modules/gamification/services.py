"""Service layer for gamification features.

Manages UserProgress data persistence and coordinates XP/leveling logic.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.modules.gamification.models import UserProgress
from app.modules.gamification.logic import XPCalculator, LevelSystem


class GamificationService:
    """Service for managing user progress, XP, and levels."""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize service with database session.
        
        Args:
            session: SQLAlchemy session (creates new if None)
        """
        self._session = session
        self._owns_session = session is None
        if self._owns_session:
            self._session = SessionLocal()
    
    def get_or_create_progress(self, user_id: int = 1) -> UserProgress:
        """Get existing progress or create new record for user.
        
        Args:
            user_id: User identifier (default 1 for single-user mode)
            
        Returns:
            UserProgress instance
        """
        progress = self._session.query(UserProgress).filter_by(user_id=user_id).first()
        
        if not progress:
            progress = UserProgress(
                user_id=user_id,
                current_xp=0,
                current_level=1,
                total_tasks_completed=0
            )
            self._session.add(progress)
            self._session.commit()
            self._session.refresh(progress)
        
        return progress
    
    def award_xp_for_task(self, complexity: str, user_id: int = 1) -> Tuple[int, bool, int, int]:
        """Award XP for completing a task and check for level up.
        
        Args:
            complexity: Task complexity level
            user_id: User identifier
            
        Returns:
            Tuple of (xp_awarded, leveled_up, old_level, new_level)
        """
        progress = self.get_or_create_progress(user_id)
        
        # Calculate XP reward
        xp_awarded = XPCalculator.calculate_xp(complexity)
        
        # Store old values
        old_xp = progress.current_xp
        old_level = progress.current_level
        
        # Update XP and task count
        progress.current_xp += xp_awarded
        progress.total_tasks_completed += 1
        progress.updated_at = datetime.now(timezone.utc)
        
        # Check for level up
        leveled_up, _, new_level = LevelSystem.check_level_up(old_xp, progress.current_xp)
        
        if leveled_up:
            progress.current_level = new_level
        
        self._session.commit()
        self._session.refresh(progress)
        
        return (xp_awarded, leveled_up, old_level, new_level)
    
    def get_progress_stats(self, user_id: int = 1) -> dict:
        """Get formatted progress statistics for UI display.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with progress stats
        """
        progress = self.get_or_create_progress(user_id)
        
        current_level, xp_in_current_level, xp_for_next_level = LevelSystem.calculate_level_from_xp(
            progress.current_xp
        )
        
        # Calculate percentage progress to next level
        if xp_for_next_level > 0:
            progress_percentage = int((xp_in_current_level / xp_for_next_level) * 100)
        else:
            progress_percentage = 0
        
        return {
            'user_id': progress.user_id,
            'current_level': current_level,
            'current_xp': progress.current_xp,
            'xp_in_current_level': xp_in_current_level,
            'xp_for_next_level': xp_for_next_level,
            'progress_percentage': progress_percentage,
            'total_tasks_completed': progress.total_tasks_completed,
            'updated_at': progress.updated_at
        }
    
    def close(self):
        """Close database session if owned by this service."""
        if self._owns_session and self._session:
            self._session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

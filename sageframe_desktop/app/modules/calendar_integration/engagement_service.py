"""Engagement suggestion service for proactive scheduling.

This module provides intelligent engagement suggestions based on calendar
availability, user tasks, and mood context.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from app.database import SessionLocal
from app.modules.calendar_integration.availability_service import AvailabilityService
from app.modules.calendar_integration.models import AvailabilitySlot


@dataclass
class EngagementSuggestion:
    """Represents a suggested engagement."""
    
    suggestion_id: str
    suggestion_type: str  # 'social', 'professional', 'task-related'
    title: str
    description: str
    suggested_time_slot: Dict[str, datetime]  # {'start': ..., 'end': ...}
    duration_minutes: int
    reasoning: str
    confidence_score: float  # 0.0 to 1.0
    related_task_id: Optional[int] = None
    related_task_name: Optional[str] = None


class EngagementSuggestionService:
    """Service for generating proactive engagement suggestions.
    
    Analyzes calendar availability, pending tasks, and user context to suggest
    social or professional engagements at optimal times.
    """
    
    def __init__(self):
        """Initialize engagement suggestion service."""
        self.session = SessionLocal()
        self.availability_service = AvailabilityService()
        self.availability_service.session = self.session  # Share session
        self._daily_suggestion_count = {}  # Track suggestions per day
        self._user_preferences = {}  # Store learned preferences
    
    def generate_engagement_suggestions(
        self,
        connection_id: int,
        user_tasks: List[Dict],
        mood: Optional[str] = None,
        energy_level: Optional[str] = None,
        lookback_days: int = 7,
        max_suggestions: int = 2
    ) -> List[EngagementSuggestion]:
        """Generate engagement suggestions based on availability and context.
        
        Args:
            connection_id: Calendar connection ID
            user_tasks: List of user tasks with 'id', 'name', 'priority', etc.
            mood: User's current mood (from Story 1.3)
            energy_level: User's current energy level
            lookback_days: Number of days to look ahead for free slots
            max_suggestions: Maximum number of suggestions to generate
        
        Returns:
            List of EngagementSuggestion objects
        """
        # Check daily suggestion limit (don't over-suggest)
        today = datetime.now(timezone.utc).date()
        if self._daily_suggestion_count.get(today, 0) >= max_suggestions:
            return []
        
        # Find free time slots (2+ hour blocks)
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=lookback_days)
        
        free_slots = self.availability_service.find_free_slots(
            connection_id,
            start_date,
            end_date,
            min_duration_minutes=120  # 2-hour minimum
        )
        
        print(f"DEBUG: Found {len(free_slots)} free slots")  # DEBUG
        
        if not free_slots:
            return []
        
        # Generate suggestions based on context
        suggestions = []
        
        # Task-related engagements
        task_suggestions = self._generate_task_related_suggestions(
            free_slots,
            user_tasks,
            mood,
            energy_level
        )
        suggestions.extend(task_suggestions)
        
        # Social engagements (if mood/energy supports it)
        if self._should_suggest_social(mood, energy_level):
            social_suggestions = self._generate_social_suggestions(
                free_slots,
                mood,
                energy_level
            )
            suggestions.extend(social_suggestions)
        
        # Professional engagements
        professional_suggestions = self._generate_professional_suggestions(
            free_slots,
            mood,
            energy_level
        )
        suggestions.extend(professional_suggestions)
        
        # Sort by confidence and limit
        suggestions.sort(key=lambda s: s.confidence_score, reverse=True)
        final_suggestions = suggestions[:max_suggestions]
        
        # Update daily count
        self._daily_suggestion_count[today] = self._daily_suggestion_count.get(today, 0) + len(final_suggestions)
        
        return final_suggestions
    
    def _generate_task_related_suggestions(
        self,
        free_slots: List[Dict],  # Changed from List[AvailabilitySlot]
        user_tasks: List[Dict],
        mood: Optional[str],
        energy_level: Optional[str]
    ) -> List[EngagementSuggestion]:
        """Generate suggestions related to pending tasks.
        
        Args:
            free_slots: Available time slots (list of dicts with 'start', 'end', 'duration_minutes')
            user_tasks: List of user tasks
            mood: User's current mood
            energy_level: User's current energy level
        
        Returns:
            List of task-related engagement suggestions
        """
        suggestions = []
        
        # Keywords that indicate social/meeting tasks
        social_keywords = ['coffee', 'lunch', 'meeting', 'call', 'catch up', 'mentor', 'networking']
        
        for task in user_tasks:
            task_name = task.get('name', '').lower()
            
            # Check if task relates to social engagement
            if any(keyword in task_name for keyword in social_keywords):
                # Find suitable time slot
                for i, slot in enumerate(free_slots[:3]):  # Check first 3 free slots
                    suggestion = EngagementSuggestion(
                        suggestion_id=f"task_{task.get('id')}_{i}",
                        suggestion_type='task-related',
                        title=task.get('name', 'Pending Task'),
                        description=f"You have '{task.get('name')}' on your task list. This would be a good time to schedule it.",
                        suggested_time_slot={
                            'start': slot['start'],
                            'end': slot['start'] + timedelta(hours=1)
                        },
                        duration_minutes=60,
                        reasoning=f"Task pending with free {int(slot['duration_minutes'] / 60)}h block available",
                        confidence_score=0.8,
                        related_task_id=task.get('id'),
                        related_task_name=task.get('name')
                    )
                    suggestions.append(suggestion)
                    break  # Only one suggestion per task
        
        return suggestions
    
    def _generate_social_suggestions(
        self,
        free_slots: List[Dict],
        mood: Optional[str],
        energy_level: Optional[str]
    ) -> List[EngagementSuggestion]:
        """Generate social engagement suggestions.
        
        Args:
            free_slots: Available time slots (list of dicts)
            mood: User's current mood
            energy_level: User's current energy level
        
        Returns:
            List of social engagement suggestions
        """
        suggestions = []
        
        # Only suggest social activities if user has energy
        if energy_level in ['low', 'exhausted']:
            return []
        
        # Find afternoon/evening slots (better for social activities)
        for i, slot in enumerate(free_slots):
            hour = slot['start'].hour
            
            # Afternoon/evening slots (2 PM - 6 PM)
            if 14 <= hour <= 18:
                suggestion = EngagementSuggestion(
                    suggestion_id=f"social_{i}",
                    suggestion_type='social',
                    title='Social Connection Time',
                    description='You have a nice free block. Consider reaching out to a friend or colleague for a catch-up.',
                    suggested_time_slot={
                        'start': slot['start'],
                        'end': slot['start'] + timedelta(hours=1.5)
                    },
                    duration_minutes=90,
                    reasoning=f"Free {int(slot['duration_minutes'] / 60)}h afternoon block, good for social connection",
                    confidence_score=0.6 if mood in ['happy', 'energized'] else 0.4
                )
                suggestions.append(suggestion)
                break  # Only one social suggestion
        
        return suggestions
    
    def _generate_professional_suggestions(
        self,
        free_slots: List[Dict],
        mood: Optional[str],
        energy_level: Optional[str]
    ) -> List[EngagementSuggestion]:
        """Generate professional engagement suggestions.
        
        Args:
            free_slots: Available time slots (list of dicts)
            mood: User's current mood
            energy_level: User's current energy level
        
        Returns:
            List of professional engagement suggestions
        """
        suggestions = []
        
        # Find morning slots (better for professional activities)
        for i, slot in enumerate(free_slots):
            hour = slot['start'].hour
            
            # Morning slots (9 AM - 11 AM)
            if 9 <= hour <= 11:
                suggestion = EngagementSuggestion(
                    suggestion_id=f"professional_{i}",
                    suggestion_type='professional',
                    title='Professional Development Time',
                    description='You have a productive morning slot available. Consider scheduling a mentor meeting or skill-building session.',
                    suggested_time_slot={
                        'start': slot['start'],
                        'end': slot['start'] + timedelta(hours=1)
                    },
                    duration_minutes=60,
                    reasoning=f"Free {int(slot['duration_minutes'] / 60)}h morning block, optimal for focused professional work",
                    confidence_score=0.7 if energy_level in ['high', 'medium'] else 0.5
                )
                suggestions.append(suggestion)
                break  # Only one professional suggestion
        
        return suggestions
    
    def _should_suggest_social(self, mood: Optional[str], energy_level: Optional[str]) -> bool:
        """Determine if social suggestions are appropriate based on mood/energy.
        
        Args:
            mood: User's current mood
            energy_level: User's current energy level
        
        Returns:
            True if social suggestions should be generated
        """
        # Don't suggest social activities when user is low energy or stressed
        if energy_level in ['low', 'exhausted']:
            return False
        
        if mood in ['stressed', 'anxious', 'sad']:
            return False
        
        return True
    
    def record_suggestion_response(
        self,
        suggestion_id: str,
        action: str,  # 'accepted', 'declined', 'dismissed'
        reason: Optional[str] = None
    ):
        """Record user's response to a suggestion for learning.
        
        Args:
            suggestion_id: ID of the suggestion
            action: User's action ('accepted', 'declined', 'dismissed')
            reason: Optional reason for decline
        """
        # Parse suggestion ID to extract context
        parts = suggestion_id.split('_')
        suggestion_type = parts[0]
        
        if action == 'declined' and reason:
            # Store preference to avoid similar suggestions
            # e.g., "don't suggest coffee meetings on Tuesdays"
            preference_key = f"{suggestion_type}_{reason}"
            self._user_preferences[preference_key] = {
                'action': 'avoid',
                'recorded_at': datetime.now(timezone.utc)
            }
        
        elif action == 'dismissed':
            # Reduce frequency of similar suggestions
            frequency_key = f"{suggestion_type}_frequency"
            current_freq = self._user_preferences.get(frequency_key, 1.0)
            self._user_preferences[frequency_key] = max(0.5, current_freq - 0.1)
        
        # TODO: Store in database for persistent learning
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get current user preferences for suggestions.
        
        Returns:
            Dictionary of user preferences
        """
        return self._user_preferences.copy()

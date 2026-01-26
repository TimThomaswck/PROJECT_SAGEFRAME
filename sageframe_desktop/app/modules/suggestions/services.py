"""Service layer for mood-aware suggestion generation and delivery.

This module implements the business logic for generating contextual suggestions
based on user mood, energy, and available tasks. Designed for future LLM
integration while providing template-based suggestions for MVP.
"""

import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.modules.suggestions.logic import (
    MoodTaskMappingStrategy,
    ContextAwarenessEngine,
    TaskDifficulty,
    SuggestionRelevance,
)


@dataclass
class Suggestion:
    """Data class representing a single suggestion."""
    task_id: str
    task_name: str
    reasoning: str
    relevance_score: int
    suggested_at: datetime
    mood_context: str
    energy_context: str


class SuggestionRequest(BaseModel):
    """Pydantic model for suggestion request validation."""
    mood: str = Field(..., description="User's current mood")
    energy_level: str = Field(..., description="User's current energy level")
    available_tasks: List[Dict] = Field(..., description="List of available tasks")
    user_activity_state: Optional[str] = Field(None, description="Current user activity")
    user_preferences: Optional[Dict] = Field(None, description="User delivery preferences")


class SuggestionResponse(BaseModel):
    """Pydantic model for suggestion response."""
    suggestions: List[Dict] = Field(..., description="List of generated suggestions")
    delivery_style: str = Field(..., description="Recommended notification style")
    should_display: bool = Field(..., description="Whether to display suggestions now")


class SuggestionService:
    """
    Service for generating mood-aware task suggestions.
    
    Responsibilities:
    - Generate contextual suggestions based on mood and energy
    - Filter and rank available tasks
    - Determine delivery timing and style
    - Integrate with CopilotCommunicationService
    - Store suggestion history (future integration)
    
    Architecture: Designed with interfaces for future LLM integration.
    Currently uses template-based strategies for MVP.
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize suggestion service.
        
        Args:
            db_session: Optional SQLAlchemy session for persistence
        """
        self.db = db_session
        self._last_suggestion_time: Optional[float] = None
        self._suggestions_shown_count: int = 0
        self._session_start_time = time.time()
        self._suggestion_history: List[Suggestion] = []
    
    def generate_suggestions(
        self,
        mood: str,
        energy_level: str,
        available_tasks: List[Dict],
        user_activity_state: Optional[str] = None,
        user_preferences: Optional[Dict] = None,
        max_suggestions: int = 3,
    ) -> SuggestionResponse:
        """
        Generate contextual suggestions based on user mood and available tasks.
        
        Args:
            mood: User's current mood (e.g., "happy", "stressed")
            energy_level: User's current energy ("high", "medium", "low")
            available_tasks: List of available tasks with 'id', 'name', 'difficulty'
            user_activity_state: Current user activity state
            user_preferences: User's delivery preferences
            max_suggestions: Maximum number of suggestions to generate
            
        Returns:
            SuggestionResponse with generated suggestions and delivery info
            
        Raises:
            ValueError: If mood, energy_level, or tasks are invalid
        """
        # Validate input
        if not mood or not energy_level:
            raise ValueError("Mood and energy level are required")
        
        if not available_tasks:
            return SuggestionResponse(
                suggestions=[],
                delivery_style="notification",
                should_display=False
            )
        
        # Check if suggestions should be shown now
        should_display = ContextAwarenessEngine.should_show_suggestion(
            user_activity_state=user_activity_state,
            last_suggestion_time=self._last_suggestion_time,
            suggestions_shown_count=self._suggestions_shown_count,
            preferences=user_preferences,
        )
        
        if not should_display and available_tasks:
            # Return empty suggestions but indicate capacity exists
            return SuggestionResponse(
                suggestions=[],
                delivery_style="panel",
                should_display=False
            )
        
        # Filter and rank tasks based on mood/energy
        relevant_tasks = MoodTaskMappingStrategy.filter_tasks(
            available_tasks,
            mood=mood,
            energy_level=energy_level,
            min_score=1,
        )
        
        # Generate suggestions for top tasks
        suggestions = []
        for task in relevant_tasks[:max_suggestions]:
            suggestion_dict = self._generate_suggestion_dict(
                task=task,
                mood=mood,
                energy_level=energy_level,
            )
            suggestions.append(suggestion_dict)
        
        # Determine delivery style
        delivery_style = ContextAwarenessEngine.get_notification_style(
            user_activity_state=user_activity_state,
            preferences=user_preferences,
        )
        
        # Update tracking
        if suggestions:
            self._last_suggestion_time = time.time()
            self._suggestions_shown_count += 1
        
        return SuggestionResponse(
            suggestions=suggestions,
            delivery_style=delivery_style,
            should_display=True if suggestions else False,
        )
    
    def _generate_suggestion_dict(
        self,
        task: Dict,
        mood: str,
        energy_level: str,
    ) -> Dict:
        """
        Generate a single suggestion dictionary.
        
        Args:
            task: Task dictionary with 'id', 'name', 'difficulty'
            mood: User's current mood
            energy_level: User's current energy level
            
        Returns:
            Dictionary with task info and reasoning
        """
        difficulty = task.get("difficulty", TaskDifficulty.MEDIUM.value)
        
        # Calculate relevance reasoning
        reasoning = self._generate_reasoning(mood, energy_level, difficulty)
        
        return {
            "task_id": task.get("id"),
            "task_name": task.get("name", "Unnamed Task"),
            "task_description": task.get("description", ""),
            "difficulty": difficulty,
            "reasoning": reasoning,
            "mood_context": mood,
            "energy_context": energy_level,
            "suggested_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def _generate_reasoning(
        self,
        mood: str,
        energy_level: str,
        task_difficulty: str,
    ) -> str:
        """
        Generate human-readable reasoning for why task is suggested.
        
        Template-based for MVP. Future LLM integration can provide
        more sophisticated reasoning.
        
        Args:
            mood: User's current mood
            energy_level: User's current energy level
            task_difficulty: Task's difficulty level
            
        Returns:
            Reasoning string
        """
        reasoning_templates = {
            ("happy", "high", "hard"): "You're in a great mood and full of energy—this challenging task could be perfect!",
            ("happy", "high", "medium"): "With your positive energy, you could tackle this task smoothly.",
            ("happy", "medium", "medium"): "A good match for your current mood and energy.",
            ("neutral", "medium", "medium"): "This task aligns well with your energy level.",
            ("stressed", "low", "easy"): "This is a manageable task that could help build momentum.",
            ("stressed", "medium", "easy"): "A lighter task might help reduce stress.",
            ("sad", "low", "easy"): "A small win could help lift your mood.",
            ("low_energy", "low", "easy"): "This task is gentle and wouldn't overwhelm you right now.",
        }
        
        # Try exact match first
        key = (mood, energy_level, task_difficulty)
        if key in reasoning_templates:
            return reasoning_templates[key]
        
        # Fallback: generate generic reasoning
        if task_difficulty == "easy":
            return "This is a lighter task that fits your current energy level."
        elif task_difficulty == "hard":
            if energy_level == "high":
                return "This is a challenging task that could benefit from your current energy."
            else:
                return "This task might be better tackled when you have more energy."
        else:
            return "This task seems like a good fit for your current state."
    
    def reset_session_counters(self):
        """Reset session suggestion counters and timers."""
        self._last_suggestion_time = None
        self._suggestions_shown_count = 0
        self._session_start_time = time.time()
    
    def get_suggestion_history(self) -> List[Suggestion]:
        """
        Get history of suggestions shown in current session.
        
        Returns:
            List of Suggestion objects
        """
        return self._suggestion_history.copy()
    
    def clear_suggestion_history(self):
        """Clear suggestion history."""
        self._suggestion_history.clear()

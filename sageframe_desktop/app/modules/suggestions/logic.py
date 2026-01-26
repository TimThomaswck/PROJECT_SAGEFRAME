"""Mood-to-task mapping and suggestion logic engine.

This module implements the core algorithms for contextual suggestion generation
based on mood, energy level, and available tasks.
"""

from typing import List, Dict, Tuple, Optional
from enum import Enum


class MoodLevel(str, Enum):
    """Enumeration of mood levels."""
    HAPPY = "happy"
    NEUTRAL = "neutral"
    STRESSED = "stressed"
    SAD = "sad"


class EnergyLevel(str, Enum):
    """Enumeration of energy levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskDifficulty(str, Enum):
    """Task difficulty classification for suggestion mapping."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SuggestionRelevance(str, Enum):
    """Relevance score for suggestions."""
    HIGHLY_RELEVANT = "highly_relevant"
    RELEVANT = "relevant"
    SOMEWHAT_RELEVANT = "somewhat_relevant"
    NOT_RELEVANT = "not_relevant"


class MoodTaskMappingStrategy:
    """
    Implements mood-to-task mapping strategies.
    
    Defines decision rules for suggesting tasks based on user's mood and energy.
    These are template-based rules for MVP. Future LLM integration can replace
    these with intelligent reasoning.
    """
    
    # Mood-to-difficulty mapping: which task difficulties are best for each mood
    MOOD_DIFFICULTY_MAP: Dict[str, List[Tuple[str, int]]] = {
        # (difficulty, weight/priority)
        MoodLevel.HAPPY.value: [
            (TaskDifficulty.HARD.value, 3),      # Happy mood: tackle challenging tasks
            (TaskDifficulty.MEDIUM.value, 2),
            (TaskDifficulty.EASY.value, 1),
        ],
        MoodLevel.NEUTRAL.value: [
            (TaskDifficulty.MEDIUM.value, 3),    # Neutral: balanced approach
            (TaskDifficulty.HARD.value, 2),
            (TaskDifficulty.EASY.value, 1),
        ],
        MoodLevel.STRESSED.value: [
            (TaskDifficulty.EASY.value, 3),      # Stressed: build confidence with easy wins
            (TaskDifficulty.MEDIUM.value, 1),
            (TaskDifficulty.HARD.value, 0),      # Avoid hard tasks when stressed
        ],
        MoodLevel.SAD.value: [
            (TaskDifficulty.EASY.value, 3),      # Sad: supportive tasks only
            (TaskDifficulty.MEDIUM.value, 1),
            (TaskDifficulty.HARD.value, 0),
        ],
    }
    
    # Energy-to-difficulty mapping
    ENERGY_DIFFICULTY_MAP: Dict[str, List[Tuple[str, int]]] = {
        EnergyLevel.HIGH.value: [
            (TaskDifficulty.HARD.value, 3),      # High energy: complex work
            (TaskDifficulty.MEDIUM.value, 2),
            (TaskDifficulty.EASY.value, 1),
        ],
        EnergyLevel.MEDIUM.value: [
            (TaskDifficulty.MEDIUM.value, 3),    # Medium energy: balanced
            (TaskDifficulty.HARD.value, 2),
            (TaskDifficulty.EASY.value, 1),
        ],
        EnergyLevel.LOW.value: [
            (TaskDifficulty.EASY.value, 3),      # Low energy: gentle tasks
            (TaskDifficulty.MEDIUM.value, 1),
            (TaskDifficulty.HARD.value, 0),
        ],
    }
    
    @classmethod
    def get_difficulty_score(
        cls,
        task_difficulty: str,
        mood: str,
        energy_level: str,
    ) -> int:
        """
        Calculate task difficulty score based on mood and energy.
        
        Args:
            task_difficulty: Task's inherent difficulty level
            mood: User's current mood
            energy_level: User's current energy level
            
        Returns:
            Score (0-6): higher score = better fit for current state
        """
        mood_score = 0
        energy_score = 0
        
        # Get mood-based score
        if mood in cls.MOOD_DIFFICULTY_MAP:
            for diff, weight in cls.MOOD_DIFFICULTY_MAP[mood]:
                if diff == task_difficulty:
                    mood_score = weight
                    break
        
        # Get energy-based score
        if energy_level in cls.ENERGY_DIFFICULTY_MAP:
            for diff, weight in cls.ENERGY_DIFFICULTY_MAP[energy_level]:
                if diff == task_difficulty:
                    energy_score = weight
                    break
        
        return mood_score + energy_score
    
    @classmethod
    def rank_tasks(
        cls,
        tasks: List[Dict],
        mood: str,
        energy_level: str,
    ) -> List[Tuple[Dict, int]]:
        """
        Rank available tasks by relevance to current mood/energy.
        
        Args:
            tasks: List of task dictionaries with 'id', 'name', 'difficulty' keys
            mood: User's current mood
            energy_level: User's current energy level
            
        Returns:
            List of (task, score) tuples sorted by relevance (descending)
        """
        ranked = []
        
        for task in tasks:
            difficulty = task.get("difficulty", TaskDifficulty.MEDIUM.value)
            score = cls.get_difficulty_score(difficulty, mood, energy_level)
            ranked.append((task, score))
        
        # Sort by score descending (highest relevance first)
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked
    
    @classmethod
    def filter_tasks(
        cls,
        tasks: List[Dict],
        mood: str,
        energy_level: str,
        min_score: int = 1,
    ) -> List[Dict]:
        """
        Filter tasks based on mood/energy relevance threshold.
        
        Args:
            tasks: List of task dictionaries
            mood: User's current mood
            energy_level: User's current energy level
            min_score: Minimum relevance score to include task
            
        Returns:
            List of relevant tasks, sorted by score
        """
        ranked = cls.rank_tasks(tasks, mood, energy_level)
        relevant_tasks = [task for task, score in ranked if score >= min_score]
        
        return relevant_tasks


class ContextAwarenessEngine:
    """
    Implements context awareness for non-intrusive suggestion delivery.
    
    Determines optimal timing and presentation based on user activity,
    suggestion history, and delivery preferences.
    """
    
    # Default delivery preferences (can be customized per user)
    DEFAULT_DELIVERY_PREFERENCES = {
        "max_suggestions_per_session": 3,
        "min_time_between_suggestions_minutes": 15,
        "preferred_notification_style": "notification",  # notification, panel, chat
        "allow_interruption_on_break": True,
        "respect_focus_mode": True,
    }
    
    @classmethod
    def should_show_suggestion(
        cls,
        user_activity_state: Optional[str] = None,
        last_suggestion_time: Optional[float] = None,
        suggestions_shown_count: int = 0,
        preferences: Optional[Dict] = None,
    ) -> bool:
        """
        Determine if a suggestion should be shown now.
        
        Args:
            user_activity_state: Current user activity ("active", "idle", "focused", "on_break")
            last_suggestion_time: Unix timestamp of last suggestion
            suggestions_shown_count: Number of suggestions shown in current session
            preferences: User's delivery preferences
            
        Returns:
            True if suggestion should be shown, False otherwise
        """
        prefs = preferences or cls.DEFAULT_DELIVERY_PREFERENCES
        
        # Check max suggestions per session
        if suggestions_shown_count >= prefs.get("max_suggestions_per_session", 3):
            return False
        
        # Check time between suggestions
        if last_suggestion_time is not None:
            import time
            current_time = time.time()
            min_interval = prefs.get("min_time_between_suggestions_minutes", 15) * 60
            if current_time - last_suggestion_time < min_interval:
                return False
        
        # Respect focus mode
        if prefs.get("respect_focus_mode") and user_activity_state == "focused":
            return False
        
        return True
    
    @classmethod
    def get_notification_style(
        cls,
        user_activity_state: Optional[str] = None,
        preferences: Optional[Dict] = None,
    ) -> str:
        """
        Determine presentation style for suggestion.
        
        Args:
            user_activity_state: Current user activity state
            preferences: User's delivery preferences
            
        Returns:
            Notification style: "notification", "panel", or "chat"
        """
        prefs = preferences or cls.DEFAULT_DELIVERY_PREFERENCES
        
        # Use notification for breaks, panel for focused work, chat for idle
        if user_activity_state == "on_break":
            return "notification"
        elif user_activity_state == "focused":
            return "panel"  # Less intrusive
        elif user_activity_state == "idle":
            return "chat"
        
        return prefs.get("preferred_notification_style", "notification")

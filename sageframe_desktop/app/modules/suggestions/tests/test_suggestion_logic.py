"""Tests for suggestion logic engine.

Tests the mood-to-task mapping and filtering algorithms.
"""

import pytest

from app.modules.suggestions.logic import (
    MoodTaskMappingStrategy,
    ContextAwarenessEngine,
    TaskDifficulty,
    MoodLevel,
    EnergyLevel,
)


class TestMoodTaskMappingStrategy:
    """Test suite for mood-to-task mapping."""
    
    def test_get_difficulty_score_happy_high_hard(self):
        """Happy mood + high energy should score high for hard tasks."""
        score = MoodTaskMappingStrategy.get_difficulty_score(
            task_difficulty=TaskDifficulty.HARD.value,
            mood=MoodLevel.HAPPY.value,
            energy_level=EnergyLevel.HIGH.value,
        )
        assert score == 6  # mood=3 + energy=3
    
    def test_get_difficulty_score_stressed_low_easy(self):
        """Stressed mood + low energy should score high for easy tasks."""
        score = MoodTaskMappingStrategy.get_difficulty_score(
            task_difficulty=TaskDifficulty.EASY.value,
            mood=MoodLevel.STRESSED.value,
            energy_level=EnergyLevel.LOW.value,
        )
        assert score == 6  # mood=3 + energy=3
    
    def test_get_difficulty_score_stressed_low_hard(self):
        """Stressed mood + low energy should score 0 for hard tasks."""
        score = MoodTaskMappingStrategy.get_difficulty_score(
            task_difficulty=TaskDifficulty.HARD.value,
            mood=MoodLevel.STRESSED.value,
            energy_level=EnergyLevel.LOW.value,
        )
        assert score == 0  # mood=0 + energy=0
    
    def test_rank_tasks_orders_by_relevance(self):
        """Tasks should be ranked by relevance score."""
        tasks = [
            {"id": "1", "name": "Hard Task", "difficulty": "hard"},
            {"id": "2", "name": "Easy Task", "difficulty": "easy"},
            {"id": "3", "name": "Medium Task", "difficulty": "medium"},
        ]
        
        ranked = MoodTaskMappingStrategy.rank_tasks(
            tasks=tasks,
            mood=MoodLevel.HAPPY.value,
            energy_level=EnergyLevel.HIGH.value,
        )
        
        # For happy+high energy, hard should be first
        assert ranked[0][0]["id"] == "1"  # Hard task first
        assert ranked[1][0]["id"] == "3"  # Medium task second
        assert ranked[2][0]["id"] == "2"  # Easy task last
    
    def test_rank_tasks_stressed_low_energy(self):
        """For stressed + low energy, easy tasks should rank first."""
        tasks = [
            {"id": "1", "name": "Hard Task", "difficulty": "hard"},
            {"id": "2", "name": "Easy Task", "difficulty": "easy"},
            {"id": "3", "name": "Medium Task", "difficulty": "medium"},
        ]
        
        ranked = MoodTaskMappingStrategy.rank_tasks(
            tasks=tasks,
            mood=MoodLevel.STRESSED.value,
            energy_level=EnergyLevel.LOW.value,
        )
        
        # Easy should be first
        assert ranked[0][0]["id"] == "2"  # Easy task first
    
    def test_filter_tasks_removes_low_score(self):
        """Filter should remove tasks below score threshold."""
        tasks = [
            {"id": "1", "name": "Hard Task", "difficulty": "hard"},
            {"id": "2", "name": "Easy Task", "difficulty": "easy"},
        ]
        
        filtered = MoodTaskMappingStrategy.filter_tasks(
            tasks=tasks,
            mood=MoodLevel.STRESSED.value,
            energy_level=EnergyLevel.LOW.value,
            min_score=3,
        )
        
        # Only easy task should remain (score 6 >= 3)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "2"
    
    def test_filter_tasks_empty_input(self):
        """Filter should handle empty task list."""
        filtered = MoodTaskMappingStrategy.filter_tasks(
            tasks=[],
            mood=MoodLevel.HAPPY.value,
            energy_level=EnergyLevel.HIGH.value,
        )
        
        assert filtered == []


class TestContextAwarenessEngine:
    """Test suite for context awareness."""
    
    def test_should_show_suggestion_respects_max_count(self):
        """Should not show suggestions over max per session."""
        should_show = ContextAwarenessEngine.should_show_suggestion(
            suggestions_shown_count=3,  # Max is typically 3
            preferences={"max_suggestions_per_session": 3},
        )
        
        assert should_show is False
    
    def test_should_show_suggestion_respects_focus_mode(self):
        """Should not show suggestions in focus mode."""
        should_show = ContextAwarenessEngine.should_show_suggestion(
            user_activity_state="focused",
            preferences={"respect_focus_mode": True},
        )
        
        assert should_show is False
    
    def test_should_show_suggestion_allows_on_break(self):
        """Should show suggestions when user is on break."""
        should_show = ContextAwarenessEngine.should_show_suggestion(
            user_activity_state="on_break",
            preferences={"respect_focus_mode": True},
        )
        
        assert should_show is True
    
    def test_get_notification_style_on_break(self):
        """Should use notification style on break."""
        style = ContextAwarenessEngine.get_notification_style(
            user_activity_state="on_break",
        )
        
        assert style == "notification"
    
    def test_get_notification_style_focused(self):
        """Should use panel style when focused."""
        style = ContextAwarenessEngine.get_notification_style(
            user_activity_state="focused",
        )
        
        assert style == "panel"
    
    def test_get_notification_style_idle(self):
        """Should use chat style when idle."""
        style = ContextAwarenessEngine.get_notification_style(
            user_activity_state="idle",
        )
        
        assert style == "chat"


class TestMoodLevelEnum:
    """Test mood level enumeration."""
    
    def test_mood_levels_are_valid(self):
        """Mood levels should have expected values."""
        assert MoodLevel.HAPPY.value == "happy"
        assert MoodLevel.NEUTRAL.value == "neutral"
        assert MoodLevel.STRESSED.value == "stressed"
        assert MoodLevel.SAD.value == "sad"


class TestEnergyLevelEnum:
    """Test energy level enumeration."""
    
    def test_energy_levels_are_valid(self):
        """Energy levels should have expected values."""
        assert EnergyLevel.HIGH.value == "high"
        assert EnergyLevel.MEDIUM.value == "medium"
        assert EnergyLevel.LOW.value == "low"

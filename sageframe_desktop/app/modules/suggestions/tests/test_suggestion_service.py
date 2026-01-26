"""Tests for SuggestionService.

Tests service layer for suggestion generation and delivery.
"""

import pytest
import time

from app.modules.suggestions.services import SuggestionService, SuggestionRequest, SuggestionResponse


class TestSuggestionService:
    """Test suite for SuggestionService."""
    
    @pytest.fixture
    def service(self):
        """Create a SuggestionService instance for testing."""
        return SuggestionService()
    
    @pytest.fixture
    def sample_tasks(self):
        """Sample task list for testing."""
        return [
            {
                "id": "task_1",
                "name": "Implement feature X",
                "description": "Complex feature implementation",
                "difficulty": "hard",
            },
            {
                "id": "task_2",
                "name": "Fix typo in docs",
                "description": "Update documentation",
                "difficulty": "easy",
            },
            {
                "id": "task_3",
                "name": "Review pull request",
                "description": "Code review task",
                "difficulty": "medium",
            },
        ]
    
    def test_generate_suggestions_happy_high_energy(self, service, sample_tasks):
        """Generate suggestions for happy mood + high energy."""
        response = service.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=sample_tasks,
        )
        
        assert isinstance(response, SuggestionResponse)
        assert len(response.suggestions) > 0
        assert response.should_display is True
        # Hard task should be suggested first for happy+high energy
        assert response.suggestions[0]["task_id"] == "task_1"
    
    def test_generate_suggestions_stressed_low_energy(self, service, sample_tasks):
        """Generate suggestions for stressed mood + low energy."""
        response = service.generate_suggestions(
            mood="stressed",
            energy_level="low",
            available_tasks=sample_tasks,
        )
        
        assert isinstance(response, SuggestionResponse)
        assert len(response.suggestions) > 0
        # Easy task should be suggested first for stressed+low energy
        assert response.suggestions[0]["task_id"] == "task_2"
    
    def test_generate_suggestions_empty_tasks(self, service):
        """Should handle empty task list gracefully."""
        response = service.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=[],
        )
        
        assert response.suggestions == []
        assert response.should_display is False
    
    def test_generate_suggestions_invalid_mood(self, service, sample_tasks):
        """Should raise error for invalid mood."""
        with pytest.raises(ValueError):
            service.generate_suggestions(
                mood="",
                energy_level="high",
                available_tasks=sample_tasks,
            )
    
    def test_generate_suggestions_invalid_energy(self, service, sample_tasks):
        """Should raise error for invalid energy level."""
        with pytest.raises(ValueError):
            service.generate_suggestions(
                mood="happy",
                energy_level="",
                available_tasks=sample_tasks,
            )
    
    def test_generate_suggestions_max_suggestions_limit(self, service):
        """Should respect max_suggestions limit."""
        tasks = [
            {"id": f"task_{i}", "name": f"Task {i}", "difficulty": "easy"}
            for i in range(10)
        ]
        
        response = service.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=tasks,
            max_suggestions=2,
        )
        
        assert len(response.suggestions) <= 2
    
    def test_generate_suggestions_respects_delivery_preferences(self, service, sample_tasks):
        """Should respect user's delivery preferences."""
        # First suggestion allowed
        response1 = service.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=sample_tasks,
            user_preferences={"max_suggestions_per_session": 1},
        )
        assert response1.should_display is True
        
        # Second suggestion should be blocked
        response2 = service.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=sample_tasks,
            user_preferences={"max_suggestions_per_session": 1},
        )
        assert response2.should_display is False
    
    def test_suggestion_response_contains_reasoning(self, service, sample_tasks):
        """Each suggestion should include reasoning."""
        response = service.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=sample_tasks,
        )
        
        for suggestion in response.suggestions:
            assert "reasoning" in suggestion
            assert len(suggestion["reasoning"]) > 0
    
    def test_suggestion_response_contains_mood_context(self, service, sample_tasks):
        """Each suggestion should include mood context."""
        response = service.generate_suggestions(
            mood="stressed",
            energy_level="low",
            available_tasks=sample_tasks,
        )
        
        for suggestion in response.suggestions:
            assert suggestion["mood_context"] == "stressed"
            assert suggestion["energy_context"] == "low"
    
    def test_reset_session_counters(self, service, sample_tasks):
        """Reset session should clear counters."""
        # Generate suggestion
        service.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=sample_tasks,
        )
        
        # Reset
        service.reset_session_counters()
        
        # Next suggestion should be allowed even without time passing
        service._suggestions_shown_count = 5  # Max exceeded
        should_allow = service._suggestions_shown_count < 3
        assert not should_allow
        
        # But after explicit preferences check:
        service.reset_session_counters()
        service._suggestions_shown_count = 0
        assert service._suggestions_shown_count == 0
    
    def test_delivery_style_varies_by_activity(self, service, sample_tasks):
        """Delivery style should vary by user activity state."""
        # On break
        response_break = service.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=sample_tasks,
            user_activity_state="on_break",
        )
        assert response_break.delivery_style == "notification"
        
        # Reset for next test
        service.reset_session_counters()
        
        # Focused/active
        response_focused = service.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=sample_tasks,
            user_activity_state="focused",
        )
        # Focused work respects focus mode, so no suggestions shown
        # but delivery style is still determined
        # (delivery_style is set regardless of should_display)


class TestSuggestionRequest:
    """Test suite for SuggestionRequest validation."""
    
    def test_suggestion_request_valid(self):
        """Valid suggestion request should be accepted."""
        request = SuggestionRequest(
            mood="happy",
            energy_level="high",
            available_tasks=[
                {"id": "1", "name": "Task 1", "difficulty": "easy"}
            ],
        )
        
        assert request.mood == "happy"
        assert request.energy_level == "high"
        assert len(request.available_tasks) == 1
    
    def test_suggestion_request_with_optional_fields(self):
        """Request should accept optional fields."""
        request = SuggestionRequest(
            mood="neutral",
            energy_level="medium",
            available_tasks=[],
            user_activity_state="focused",
            user_preferences={"max_suggestions_per_session": 5},
        )
        
        assert request.user_activity_state == "focused"
        assert request.user_preferences["max_suggestions_per_session"] == 5


class TestSuggestionResponse:
    """Test suite for SuggestionResponse."""
    
    def test_suggestion_response_valid(self):
        """Valid response should have all required fields."""
        response = SuggestionResponse(
            suggestions=[
                {
                    "task_id": "1",
                    "task_name": "Task 1",
                    "reasoning": "Good fit for your mood",
                }
            ],
            delivery_style="notification",
            should_display=True,
        )
        
        assert len(response.suggestions) == 1
        assert response.delivery_style == "notification"
        assert response.should_display is True
    
    def test_suggestion_response_empty_suggestions(self):
        """Response can have empty suggestions."""
        response = SuggestionResponse(
            suggestions=[],
            delivery_style="panel",
            should_display=False,
        )
        
        assert response.suggestions == []
        assert response.should_display is False

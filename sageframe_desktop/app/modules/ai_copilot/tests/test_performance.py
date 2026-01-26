"""Performance tests for AI Co-Pilot module.

Tests ensure NFR1 (<100ms message generation/display) is met.
"""

import pytest
import time

from app.modules.ai_copilot.services import CopilotCommunicationService
from app.modules.ai_copilot.persona import ToneLevel


@pytest.fixture
def mock_db_session(monkeypatch):
    """Mock database session for testing."""
    class MockSession:
        def add(self, obj):
            pass
        
        def commit(self):
            pass
        
        def query(self, *args):
            return self
        
        def filter_by(self, **kwargs):
            return self
        
        def first(self):
            return None
    
    return MockSession()


class TestCopilotPerformance:
    """Performance test suite for AI Co-Pilot communication service."""
    
    def test_generate_greeting_performance(self, mock_db_session):
        """Greeting generation should complete in <100ms."""
        service = CopilotCommunicationService(mock_db_session)
        
        start_time = time.time()
        message = service.generate_greeting(tone_level=ToneLevel.GENTLE)
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        # NFR1: <100ms
        assert elapsed_ms < 100, f"Greeting generation took {elapsed_ms}ms (should be <100ms)"
        assert len(message) > 0
    
    def test_generate_mood_response_performance(self, mock_db_session):
        """Mood response generation should complete in <100ms."""
        service = CopilotCommunicationService(mock_db_session)
        
        start_time = time.time()
        message = service.generate_mood_response(
            mood="high_energy",
            energy_level=8,
            tone_level=ToneLevel.GENTLE,
        )
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        # NFR1: <100ms
        assert elapsed_ms < 100, f"Mood response generation took {elapsed_ms}ms (should be <100ms)"
        assert len(message) > 0
    
    def test_generate_task_suggestion_performance(self, mock_db_session):
        """Task suggestion generation should complete in <100ms."""
        service = CopilotCommunicationService(mock_db_session)
        
        start_time = time.time()
        message = service.generate_task_suggestion(
            task_name="Implement feature X",
            tone_level=ToneLevel.GENTLE,
        )
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        # NFR1: <100ms
        assert elapsed_ms < 100, f"Task suggestion generation took {elapsed_ms}ms (should be <100ms)"
        assert len(message) > 0
    
    def test_generate_encouragement_performance(self, mock_db_session):
        """Encouragement generation should complete in <100ms."""
        service = CopilotCommunicationService(mock_db_session)
        
        start_time = time.time()
        message = service.generate_encouragement(tone_level=ToneLevel.ENCOURAGING)
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        # NFR1: <100ms
        assert elapsed_ms < 100, f"Encouragement generation took {elapsed_ms}ms (should be <100ms)"
        assert len(message) > 0
    
    def test_generate_gentle_reminder_performance(self, mock_db_session):
        """Gentle reminder generation should complete in <100ms."""
        service = CopilotCommunicationService(mock_db_session)
        
        start_time = time.time()
        message = service.generate_gentle_reminder(
            task_name="Review code",
            tone_level=ToneLevel.MINIMAL,
        )
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        # NFR1: <100ms
        assert elapsed_ms < 100, f"Gentle reminder generation took {elapsed_ms}ms (should be <100ms)"
        assert len(message) > 0
    
    def test_generate_break_suggestion_performance(self, mock_db_session):
        """Break suggestion generation should complete in <100ms."""
        service = CopilotCommunicationService(mock_db_session)
        
        start_time = time.time()
        message = service.generate_break_suggestion(tone_level=ToneLevel.GENTLE)
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        # NFR1: <100ms
        assert elapsed_ms < 100, f"Break suggestion generation took {elapsed_ms}ms (should be <100ms)"
        assert len(message) > 0
    
    def test_validate_message_tone_performance(self, mock_db_session):
        """Tone validation should complete in <50ms."""
        service = CopilotCommunicationService(mock_db_session)
        
        message = "You're doing great! Keep up the good work."
        
        start_time = time.time()
        is_valid, error = service.validate_message_tone(message)
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        # Should be very fast
        assert elapsed_ms < 50, f"Tone validation took {elapsed_ms}ms (should be <50ms)"
        assert is_valid is True
    
    def test_batch_message_generation_performance(self, mock_db_session):
        """Generating 10 messages should complete in <500ms (avg <50ms each)."""
        service = CopilotCommunicationService(mock_db_session)
        
        start_time = time.time()
        
        for i in range(10):
            service.generate_task_suggestion(
                task_name=f"Task {i}",
                tone_level=ToneLevel.GENTLE,
            )
        
        end_time = time.time()
        
        total_ms = (end_time - start_time) * 1000
        avg_ms = total_ms / 10
        
        # NFR2: Average should be well under 100ms
        assert avg_ms < 50, f"Average message generation took {avg_ms}ms (should be <50ms)"
        assert total_ms < 500, f"Batch generation took {total_ms}ms (should be <500ms)"


class TestCopilotMessageGeneration:
    """Test that message generation doesn't regress over time."""
    
    def test_message_consistency(self, mock_db_session):
        """Generated messages should be consistent and non-empty."""
        service = CopilotCommunicationService(mock_db_session)
        
        messages = []
        for _ in range(5):
            msg = service.generate_task_suggestion(
                task_name="Test task",
                tone_level=ToneLevel.GENTLE,
            )
            messages.append(msg)
            assert len(msg) > 0
        
        # All messages should be non-empty strings
        assert all(isinstance(m, str) and len(m) > 0 for m in messages)

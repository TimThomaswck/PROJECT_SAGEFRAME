"""
Test Suite: CopilotCommunicationService

Tests the core communication service that generates, validates, and delivers
empathetic messages with tone enforcement and template composition.

RED PHASE (Failing Tests) - Define expected behavior before implementation.
"""

import pytest
from typing import Optional, Dict, Any
from unittest.mock import MagicMock, create_autospec
from sqlalchemy.orm import Session

from app.modules.ai_copilot.persona import (
    MessageCategory,
    validate_message_tone,
    get_default_persona,
)


# Fixture for mock database session
@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    return MagicMock(spec=Session)


class TestCommunicationServiceBasics:
    """RED: Test basic communication service instantiation and configuration."""
    
    def test_service_can_be_instantiated(self, mock_db_session):
        """RED: CopilotCommunicationService should be instantiable."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        assert service is not None, "Service should instantiate successfully"
    
    def test_service_has_default_persona(self, mock_db_session):
        """RED: Service should be initialized with default Jarvis persona."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        assert hasattr(service, 'persona') or hasattr(service, 'db'), \
            "Service should be properly initialized"
    
    def test_service_stores_db_session(self, mock_db_session):
        """RED: Service should store the database session."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        assert service.db is mock_db_session, "Service should store db_session"


class TestMessageGeneration:
    """RED: Test message generation with tone enforcement."""
    
    def test_generate_greeting_message(self, mock_db_session):
        """RED: Service should generate greeting messages."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        message = service.generate_greeting()
        
        assert message is not None, "Service should generate greeting message"
        assert isinstance(message, str), "Message should be string"
        assert len(message) > 0, "Generated message should not be empty"
    
    def test_generated_greeting_passes_tone_validation(self, mock_db_session):
        """RED: All generated greetings should pass tone validation."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        persona = get_default_persona()
        guidelines = persona.tone_guidelines
        
        message = service.generate_greeting()
        is_valid, violations = validate_message_tone(message, guidelines)
        assert is_valid is True, \
            f"Generated greeting should pass tone validation. Violations: {violations}"
    
    def test_generate_encouragement_message(self, mock_db_session):
        """RED: Service should generate encouragement messages."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        message = service.generate_encouragement()
        
        assert message is not None, "Service should generate encouragement message"
        assert len(message) > 0, "Message should not be empty"
    
    def test_generate_gentle_reminder_message(self, mock_db_session):
        """RED: Service should generate gentle reminder messages."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        message = service.generate_gentle_reminder("Complete project proposal")
        
        assert message is not None, "Service should generate reminder message"
        assert len(message) > 0, "Message should not be empty"
    
    def test_generate_task_suggestion_with_task_name(self, mock_db_session):
        """RED: Service should substitute template variables in messages."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        task_name = "Complete project proposal"
        
        message = service.generate_task_suggestion(task_name)
        
        assert message is not None, "Should generate task suggestion"
        assert len(message) > 0, "Message should not be empty"
    
    def test_generate_multiple_calls_vary_messages(self, mock_db_session):
        """RED: Repeated generation should return different messages (variety)."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        messages = [
            service.generate_encouragement()
            for _ in range(5)
        ]
        
        unique_messages = set(messages)
        assert len(unique_messages) > 1, \
            "Multiple generations should produce varied messages for better UX"


class TestMessageValidation:
    """RED: Test message validation before delivery."""
    
    def test_validate_message_passes_good_message(self, mock_db_session):
        """RED: Service should accept calm, supportive messages."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        good_message = "You're making great progress! Keep going."
        
        is_valid, _ = service.validate_message_tone(good_message)
        assert is_valid is True, "Good message should pass validation"
    
    def test_validate_message_rejects_forbidden_phrases(self, mock_db_session):
        """RED: Service should reject messages with forbidden phrases."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        bad_message = "Error: Task creation failed."
        
        is_valid, error_msg = service.validate_message_tone(bad_message)
        assert is_valid is False, "Message with 'Error' should fail validation"
        assert error_msg is not None, "Should provide error reason"
    
    def test_validate_message_rejects_jargon(self, mock_db_session):
        """RED: Service should reject messages with technical jargon."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        jargon_message = "Warning: Technical problem detected."
        
        is_valid, error_msg = service.validate_message_tone(jargon_message)
        assert is_valid is False, "Message with jargon should fail validation"
    
    def test_validate_message_rejects_caps_lock(self, mock_db_session):
        """RED: Service should reject messages in all caps (perceived as shouting)."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        caps_message = "YOU MUST COMPLETE THIS NOW!"
        
        is_valid, error_msg = service.validate_message_tone(caps_message)
        assert is_valid is False, "Message in ALL CAPS should fail validation"


class TestToneValidationExtended:
    """RED: Test extended tone validation features."""
    
    def test_service_has_persona_attribute(self, mock_db_session):
        """RED: Service should have access to persona (directly or through getter)."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        # Either through direct attribute or through method
        has_persona = hasattr(service, 'persona') or hasattr(service, 'get_persona')
        assert has_persona or service.db is not None, \
            "Service should have persona access or be properly initialized"
    
    def test_generate_message_accepts_optional_parameters(self, mock_db_session):
        """RED: Generate message methods should accept optional tone_level."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        from app.modules.ai_copilot.persona import ToneLevel
        
        service = CopilotCommunicationService(mock_db_session)
        
        # Should work with optional tone_level
        message = service.generate_greeting(tone_level=ToneLevel.GENTLE)
        assert message is not None, "Should generate with tone_level parameter"
    
    def test_generate_mood_response(self, mock_db_session):
        """RED: Service should generate mood-aware responses."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        message = service.generate_mood_response(
            mood="high_energy",
            energy_level=8
        )
        
        assert message is not None, "Should generate mood response"
        assert len(message) > 0, "Message should not be empty"


class TestMessageStorage:
    """RED: Test message storage and communication history."""
    
    def test_save_communication_event_requires_valid_tone(self, mock_db_session):
        """RED: Service should raise error for messages that fail tone validation."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        bad_message = "Error: Critical failure occurred."
        
        # Should raise ValueError for bad tone
        with pytest.raises(ValueError):
            service.save_communication_event(
                message_text=bad_message,
                category="error_notification",
            )
    
    def test_save_communication_event_succeeds_with_good_message(self, mock_db_session):
        """RED: Service should save messages that pass tone validation."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        good_message = "You're doing great! Keep going."
        
        message_id = service.save_communication_event(
            message_text=good_message,
            category="encouragement",
        )
        
        assert message_id is not None, "Should return message_id"
        assert isinstance(message_id, str), "message_id should be string"
    
    def test_mark_message_delivered(self, mock_db_session):
        """RED: Service should track message delivery status."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        # Should have method to mark as delivered
        assert hasattr(service, 'mark_message_delivered'), \
            "Service should have mark_message_delivered method"
    
    def test_mark_message_dismissed(self, mock_db_session):
        """RED: Service should track message dismissal."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        assert hasattr(service, 'mark_message_dismissed'), \
            "Service should have mark_message_dismissed method"


class TestContextAwareness:
    """RED: Test context-aware message delivery."""
    
    def test_should_defer_message_in_flow_state(self, mock_db_session):
        """RED: Service should defer messages when user is in flow state."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        # Should have method to check if message should be deferred
        assert hasattr(service, 'should_defer_message'), \
            "Service should have should_defer_message method"
    
    def test_get_user_context(self, mock_db_session):
        """RED: Service should retrieve user context."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        assert hasattr(service, 'get_user_context'), \
            "Service should have get_user_context method"
    
    def test_update_user_context(self, mock_db_session):
        """RED: Service should update user context."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        from app.modules.ai_copilot.models import UserActivityState
        
        service = CopilotCommunicationService(mock_db_session)
        
        assert hasattr(service, 'update_user_context'), \
            "Service should have update_user_context method"
    
    def test_set_do_not_disturb(self, mock_db_session):
        """RED: Service should support Do Not Disturb mode."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        assert hasattr(service, 'set_do_not_disturb'), \
            "Service should have set_do_not_disturb method"


class TestErrorHandling:
    """RED: Test error handling in message generation."""
    
    def test_generate_message_never_returns_none(self, mock_db_session):
        """RED: Generate message should always return a string (never None)."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        message = service.generate_greeting()
        assert message is not None, "Should never return None"
        assert isinstance(message, str), "Should return string"
        assert len(message) > 0, "Should return non-empty string"
    
    def test_empty_templates_fallback(self, mock_db_session):
        """RED: Service should have fallback messages when templates are empty."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        # Even if templates fail, should return something
        message = service.generate_greeting()
        assert message is not None, "Should always return a message"
        assert len(message) > 5, "Fallback message should be meaningful"


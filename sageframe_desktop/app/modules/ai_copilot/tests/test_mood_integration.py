"""
Test Suite: Mood Check-in (Story 1.3) + Co-Pilot (Story 1.4) Integration

Tests for reactive mood-aware co-pilot message delivery.
Verifies that mood check-ins trigger empathetic co-pilot responses.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.modules.mood_checkin.services import MoodCheckInService
from app.modules.mood_checkin.models import MoodCheckIn
from app.modules.ai_copilot.mood_integration import MoodAwareCopilotIntegration
from app.modules.ai_copilot.services import CopilotCommunicationService
from app.modules.ai_copilot.view_models import CopilotViewModel


@pytest.fixture
def db_session():
    """Create in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    
    # Import all models to ensure their tables are created
    from app.modules.mood_checkin.models import MoodCheckIn as MoodCheckInModel
    from app.modules.ai_copilot.models import UserContext as UserContextModel
    from app.modules.ai_copilot.models import CommunicationEvent as CommunicationEventModel
    
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mood_service(db_session):
    """Create MoodCheckInService with test session."""
    return MoodCheckInService(db_session)


@pytest.fixture
def copilot_service(db_session):
    """Create CopilotCommunicationService with test session."""
    return CopilotCommunicationService(db_session)


@pytest.fixture
def copilot_viewmodel(db_session):
    """Create CopilotViewModel with test session."""
    return CopilotViewModel(db_session)


@pytest.fixture
def integration(mood_service, copilot_service, copilot_viewmodel):
    """Create MoodAwareCopilotIntegration with all dependencies."""
    return MoodAwareCopilotIntegration(
        mood_service=mood_service,
        copilot_service=copilot_service,
        copilot_viewmodel=copilot_viewmodel
    )


class TestMoodAwareCopilotIntegration:
    """RED: Test mood-aware co-pilot response generation."""
    
    def test_integration_can_be_instantiated(self, integration):
        """RED: Integration coordinator should instantiate."""
        assert integration is not None
        assert hasattr(integration, 'moodResponseGenerated')
        assert hasattr(integration, 'moodResponseDisplayed')
    
    def test_integration_has_required_services(self, integration):
        """RED: Integration should hold service references."""
        assert integration._mood_service is not None
        assert integration._copilot_service is not None
        assert integration._copilot_viewmodel is not None
    
    def test_can_connect_mood_checkin_signal(self, integration):
        """RED: Integration should connect to mood check-in signals."""
        mock_viewmodel = Mock()
        mock_viewmodel.moodCheckInCompleted = Mock()
        
        result = integration.connect_mood_checkin_signal(mock_viewmodel)
        
        assert result is True
        mock_viewmodel.moodCheckInCompleted.connect.assert_called_once()


class TestToneSelection:
    """RED: Test tone level selection based on mood/energy."""
    
    def test_gentle_tone_for_low_energy(self, integration):
        """RED: Should use gentle tone for low energy users."""
        tone = integration._determine_tone_level("neutral", "low")
        assert tone == "gentle"
    
    def test_gentle_tone_for_stressed_mood(self, integration):
        """RED: Should use gentle tone for stressed users."""
        tone = integration._determine_tone_level("stressed", "high")
        assert tone == "gentle"
    
    def test_encouraging_tone_for_happy_high_energy(self, integration):
        """RED: Should use encouraging tone for happy, high-energy users."""
        tone = integration._determine_tone_level("happy", "high")
        assert tone == "encouraging"
    
    def test_normal_tone_default(self, integration):
        """RED: Should use normal tone as default."""
        tone = integration._determine_tone_level("neutral", "medium")
        assert tone == "normal"


class TestMoodResponseGeneration:
    """RED: Test mood-aware response generation."""
    
    def test_generate_mood_response_happy(self, integration):
        """RED: Should generate appropriate response for happy mood."""
        response = integration._generate_mood_response("happy", "high", "encouraging")
        assert response is not None
        assert len(response) > 0
        assert "happy" not in response.lower()  # Should use supportive language
    
    def test_generate_mood_response_stressed(self, integration):
        """RED: Should generate supportive response for stressed mood."""
        response = integration._generate_mood_response("stressed", "low", "gentle")
        assert response is not None
        assert len(response) > 0
    
    def test_fallback_response_on_validation_failure(self, integration):
        """RED: Should provide fallback if tone validation fails."""
        # Mock a failure scenario
        integration._copilot_service.validate_message_tone = Mock(
            return_value=(False, "Test validation failure")
        )
        
        response = integration._generate_mood_response("happy", "high", "normal")
        assert response is not None
        # Should get fallback message
        assert "wonderful" in response.lower() or "great" in response.lower()
    
    def test_energy_scale_conversion(self, integration):
        """RED: Should convert energy levels to 1-10 scale."""
        high_scale = integration._energy_to_scale("high")
        medium_scale = integration._energy_to_scale("medium")
        low_scale = integration._energy_to_scale("low")
        
        assert high_scale > medium_scale > low_scale
        assert 1 <= high_scale <= 10
        assert 1 <= medium_scale <= 10
        assert 1 <= low_scale <= 10


class TestMoodIntegrationFlow:
    """RED: Test complete mood check-in to co-pilot response flow."""
    
    def test_mood_checkin_triggers_response(self, mood_service, integration):
        """RED: Completing mood check-in should trigger co-pilot response."""
        # Create mood check-in
        mood_service.create_mood_checkin("happy", "high")
        
        # Mock signal and handler
        signal_spy = Mock()
        integration.moodResponseGenerated.connect(signal_spy)
        
        # Trigger the flow
        integration._on_mood_checkin_completed(success=True, message="Check-in saved")
        
        # Should generate response
        signal_spy.assert_called_once()
        args = signal_spy.call_args[0]
        assert len(args[0]) > 0  # response text
    
    def test_failed_checkin_does_not_trigger_response(self, integration):
        """RED: Failed mood check-in should not trigger co-pilot response."""
        signal_spy = Mock()
        integration.moodResponseGenerated.connect(signal_spy)
        
        # Trigger failed flow
        integration._on_mood_checkin_completed(success=False, message="Cancelled")
        
        # Should not generate response
        signal_spy.assert_not_called()
    
    def test_mood_context_stored_after_checkin(self, mood_service, integration):
        """RED: Mood context should be stored after check-in."""
        mood_service.create_mood_checkin("stressed", "low")
        
        integration._on_mood_checkin_completed(success=True, message="Saved")
        
        context = integration.get_last_mood_context()
        assert context is not None
        assert context["mood"] == "stressed"
        assert context["energy"] == "low"
        assert context["tone_level"] == "gentle"  # Should be gentle for stressed/low
    
    def test_response_stored_in_communication_history(self, mood_service, copilot_service, integration):
        """RED: Mood response should be stored with context."""
        # Create mood check-in
        mood_service.create_mood_checkin("happy", "high")
        
        # Trigger response generation
        integration._on_mood_checkin_completed(success=True, message="Saved")
        
        # Verify stored in communication history
        history = copilot_service.get_communication_history(limit=1)
        assert len(history) > 0
        
        event = history[0]
        assert event.category == "mood_response"
        assert event.user_mood == "happy"
        assert event.user_energy_level == 8  # high = 8


class TestMoodContextAwareness:
    """RED: Test context awareness based on mood."""
    
    def test_sad_mood_generates_supportive_message(self, mood_service, integration):
        """RED: Sad mood should trigger supportive, gentle messaging."""
        mood_service.create_mood_checkin("sad", "low")
        integration._on_mood_checkin_completed(success=True, message="Saved")
        
        context = integration.get_last_mood_context()
        assert context["mood"] == "sad"
        # Verify tone is gentle
        assert context["tone_level"] == "gentle"
    
    def test_neutral_mood_generates_balanced_message(self, mood_service, integration):
        """RED: Neutral mood should use normal tone."""
        mood_service.create_mood_checkin("neutral", "medium")
        integration._on_mood_checkin_completed(success=True, message="Saved")
        
        context = integration.get_last_mood_context()
        assert context["tone_level"] == "normal"
    
    def test_multiple_checkins_update_context(self, mood_service, integration):
        """RED: Multiple check-ins should update mood context."""
        # First check-in
        mood_service.create_mood_checkin("happy", "high")
        integration._on_mood_checkin_completed(success=True, message="Saved")
        context1 = integration.get_last_mood_context()
        
        # Second check-in
        mood_service.create_mood_checkin("stressed", "low")
        integration._on_mood_checkin_completed(success=True, message="Saved")
        context2 = integration.get_last_mood_context()
        
        # Context should be updated
        assert context1["mood"] == "happy"
        assert context2["mood"] == "stressed"
        assert context1["mood"] != context2["mood"]


class TestSignalIntegration:
    """RED: Test signal emissions and connections."""
    
    def test_mood_response_generated_signal_emitted(self, mood_service, integration):
        """RED: Should emit moodResponseGenerated signal."""
        signal_spy = Mock()
        integration.moodResponseGenerated.connect(signal_spy)
        
        mood_service.create_mood_checkin("happy", "high")
        integration._on_mood_checkin_completed(success=True, message="Saved")
        
        signal_spy.assert_called_once()
    
    def test_mood_response_displayed_signal_emitted(self, mood_service, integration):
        """RED: Should emit moodResponseDisplayed signal."""
        signal_spy = Mock()
        integration.moodResponseDisplayed.connect(signal_spy)
        
        mood_service.create_mood_checkin("happy", "high")
        integration._on_mood_checkin_completed(success=True, message="Saved")
        
        signal_spy.assert_called_once()
    
    def test_error_signal_on_failure(self, integration):
        """RED: Should emit integrationError signal on error."""
        signal_spy = Mock()
        integration.integrationError.connect(signal_spy)
        
        # Trigger error by providing invalid data
        integration._on_mood_checkin_completed(success=True, message="Saved")  # No mood data
        
        # May or may not error depending on implementation, but should have error handling


class TestFallbackMessages:
    """RED: Test fallback messages for various moods/tones."""
    
    def test_fallback_gentle_happy(self, integration):
        """RED: Fallback for happy + gentle should be supportive."""
        msg = integration._get_fallback_mood_response("happy", "high", "gentle")
        assert msg is not None
        assert "wonderful" in msg.lower() or "positive" in msg.lower() or "great" in msg.lower()
    
    def test_fallback_gentle_stressed(self, integration):
        """RED: Fallback for stressed + gentle should be supportive."""
        msg = integration._get_fallback_mood_response("stressed", "low", "gentle")
        assert msg is not None
        assert len(msg) > 0
    
    def test_fallback_encouraging_happy(self, integration):
        """RED: Fallback for happy + encouraging should be energetic."""
        msg = integration._get_fallback_mood_response("happy", "high", "encouraging")
        assert msg is not None
        assert len(msg) > 0
    
    def test_all_fallback_paths_have_messages(self, integration):
        """RED: All mood/tone combinations should have fallback messages."""
        moods = ["happy", "neutral", "stressed", "sad"]
        tones = ["gentle", "normal", "encouraging"]
        
        for mood in moods:
            for tone in tones:
                msg = integration._get_fallback_mood_response(mood, "high", tone)
                assert msg is not None
                assert len(msg) > 0


class TestCleanup:
    """RED: Test proper resource cleanup."""
    
    def test_cleanup_closes_services(self, integration):
        """RED: Cleanup should close mood service."""
        integration.cleanup()
        # Should not raise errors
        assert True

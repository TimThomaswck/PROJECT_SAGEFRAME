"""
Test Suite: Context-Aware Delivery System

Tests for intelligent message delivery timing that respects user context:
- Flow state detection (do not interrupt focus)
- Activity state tracking (idle, active, flow state)
- Message deferral algorithms
- Do Not Disturb mode
- Communication event persistence

RED PHASE (Failing Tests) - Define expected behavior before implementation.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.modules.ai_copilot.models import UserActivityState, MessageStatus


class TestContextAwareness:
    """RED: Test user context tracking and awareness."""
    
    def test_service_tracks_user_activity_state(self, mock_db_session):
        """RED: Service should track user's current activity state."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        # Update activity state
        service.update_user_context(UserActivityState.ACTIVE, is_in_focus_mode=False)
        
        context = service.get_user_context()
        assert context is not None, "Should have user context after update"
        assert context.activity_state == UserActivityState.ACTIVE, \
            "Should track activity state"
    
    def test_service_detects_flow_state(self, mock_db_session):
        """RED: Service should detect when user is in flow state."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        # Set to flow state
        service.update_user_context(UserActivityState.FLOW_STATE, is_in_focus_mode=True)
        
        context = service.get_user_context()
        assert context.activity_state == UserActivityState.FLOW_STATE, \
            "Should detect flow state"
    
    def test_service_tracks_focus_mode(self, mock_db_session):
        """RED: Service should track focus mode status."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        service.update_user_context(UserActivityState.ACTIVE, is_in_focus_mode=True)
        
        context = service.get_user_context()
        assert context.is_in_focus_mode is True, "Should track focus mode"
    
    def test_service_records_last_activity_time(self, mock_db_session):
        """RED: Service should record when user was last active."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        from datetime import datetime, timezone
        
        service = CopilotCommunicationService(mock_db_session)
        
        before = datetime.now(timezone.utc)
        service.update_user_context(UserActivityState.ACTIVE)
        after = datetime.now(timezone.utc)
        
        context = service.get_user_context()
        assert context.last_activity_at is not None, \
            "Should record last activity time"
        
        # SQLite doesn't preserve timezone info, so compare as naive datetimes
        recorded_time = context.last_activity_at
        if recorded_time.tzinfo is None:
            # Convert UTC times to naive for comparison
            before_naive = before.replace(tzinfo=None)
            after_naive = after.replace(tzinfo=None)
            assert before_naive <= recorded_time <= after_naive, \
                "Activity time should be recent"
        else:
            assert before <= recorded_time <= after, \
                "Activity time should be recent"


class TestMessageDeferral:
    """RED: Test message deferral based on user context."""
    
    def test_should_defer_in_flow_state(self, mock_db_session):
        """RED: Should not deliver messages when user is in flow state."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        # Set user to flow state
        service.update_user_context(UserActivityState.FLOW_STATE, is_in_focus_mode=True)
        
        # Should defer message delivery
        assert service.should_defer_message() is True, \
            "Should defer messages in flow state"
    
    def test_should_defer_in_focus_mode(self, mock_db_session):
        """RED: Should defer messages when user is in focus mode."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        service.update_user_context(UserActivityState.ACTIVE, is_in_focus_mode=True)
        
        assert service.should_defer_message() is True, \
            "Should defer in focus mode"
    
    def test_should_deliver_when_idle(self, mock_db_session):
        """RED: Should deliver messages when user is idle."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        service.update_user_context(UserActivityState.IDLE, is_in_focus_mode=False)
        
        assert service.should_defer_message() is False, \
            "Should deliver when idle"
    
    def test_should_deliver_in_normal_activity(self, mock_db_session):
        """RED: Should deliver messages during normal activity."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        service.update_user_context(UserActivityState.ACTIVE, is_in_focus_mode=False)
        
        assert service.should_defer_message() is False, \
            "Should deliver during normal activity"
    
    def test_defer_respects_dnd_mode(self, mock_db_session):
        """RED: Should defer messages during Do Not Disturb mode."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        # Enable DND for 5 minutes
        service.set_do_not_disturb(300000)  # milliseconds
        
        assert service.should_defer_message() is True, \
            "Should defer during DND mode"
    
    def test_dnd_timeout_allows_delivery(self, mock_db_session):
        """RED: Should deliver messages after DND timeout expires."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        from app.modules.ai_copilot.models import UserActivityState
        from datetime import datetime, timezone, timedelta
        
        service = CopilotCommunicationService(mock_db_session)
        
        # Set DND to expire in the past
        context = service.get_user_context()
        if not context:
            service.update_user_context(UserActivityState.ACTIVE)
            context = service.get_user_context()
        
        # Manually set DND to past time
        context.do_not_disturb_until = datetime.now(timezone.utc) - timedelta(seconds=1)
        
        # Should not defer after timeout
        assert service.should_defer_message() is False, \
            "Should allow delivery after DND timeout"


class TestMessageDeliveryTiming:
    """RED: Test timing algorithm for message delivery."""
    
    def test_get_optimal_delivery_time(self, mock_db_session):
        """RED: Service should suggest optimal delivery time."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        assert hasattr(service, 'get_optimal_delivery_time'), \
            "Service should have delivery timing method"
    
    def test_respects_message_intrusiveness_level(self, mock_db_session):
        """RED: Timing should consider message intrusiveness level."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        # Minimal intrusiveness messages can be deferred longer
        # Encouraging messages can be sent sooner
        assert hasattr(service, 'delivery_preferences'), \
            "Service should have delivery preferences"


class TestCommunicationHistory:
    """RED: Test persistence of communication events."""
    
    def test_communication_events_stored_with_context(self, mock_db_session):
        """RED: Communication events should include user context."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        # Save message with context
        message_id = service.save_communication_event(
            message_text="Great work!",
            category="encouragement",
            user_mood="happy",
            user_energy_level=8,
        )
        
        assert message_id is not None, "Should save event with mood context"
    
    def test_retrieve_communication_history_with_context(self, mock_db_session):
        """RED: History should preserve user context for analysis."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        
        service = CopilotCommunicationService(mock_db_session)
        
        history = service.get_communication_history()
        
        assert history is not None, "Should retrieve history"
        assert isinstance(history, list), "History should be a list"
    
    def test_context_timestamps_recorded(self, mock_db_session):
        """RED: Context changes should be timestamped."""
        from app.modules.ai_copilot.services import CopilotCommunicationService
        from app.modules.ai_copilot.models import UserActivityState
        
        service = CopilotCommunicationService(mock_db_session)
        
        service.update_user_context(UserActivityState.ACTIVE)
        
        context = service.get_user_context()
        assert context.updated_at is not None, \
            "Context updates should be timestamped"

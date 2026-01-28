"""
Test suite for Story 4.4: Proactive Engagement Suggestions

Tests engagement suggestion generation, acceptance/decline handling,
and integration with calendar availability.
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.modules.calendar_integration.models import (
    CalendarConnection,
    CalendarEvent,
    AvailabilitySlot
)
from app.modules.calendar_integration.engagement_service import (
    EngagementSuggestionService,
    EngagementSuggestion
)
from app.modules.calendar_integration.engagement_integration import EngagementSuggestionIntegration


def setup_test_db():
    """Set up test database with sample data."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create test connection
    connection = CalendarConnection(
        connection_name="Test Calendar",
        provider="google",
        user_email="test@example.com",
        calendar_id="test@example.com",
        sync_enabled=1,
        sync_status="active"
    )
    session.add(connection)
    session.commit()
    
    # Create some busy events
    now = datetime.now(timezone.utc)
    events = [
        CalendarEvent(
            connection_id=connection.id,
            event_id="event1",
            summary="Morning Meeting",
            start_time=now.replace(hour=9, minute=0, second=0, microsecond=0),
            end_time=now.replace(hour=10, minute=0, second=0, microsecond=0),
            source="google",
            last_modified=now,
            sync_version=1
        ),
        CalendarEvent(
            connection_id=connection.id,
            event_id="event2",
            summary="Lunch",
            start_time=now.replace(hour=12, minute=0, second=0, microsecond=0),
            end_time=now.replace(hour=13, minute=0, second=0, microsecond=0),
            source="google",
            last_modified=now,
            sync_version=1
        )
    ]
    
    for event in events:
        session.add(event)
    session.commit()
    
    # Create availability slots with timezone-aware datetimes
    # Free block: 10:00 AM - 12:00 PM (2 hours)
    free_slot1 = AvailabilitySlot(
        connection_id=connection.id,
        start_time=now.replace(hour=10, minute=0, second=0, microsecond=0),
        end_time=now.replace(hour=12, minute=0, second=0, microsecond=0),
        status='free',
        computed_at=now
    )
    
    # Free block: 2:00 PM - 5:00 PM (3 hours)
    free_slot2 = AvailabilitySlot(
        connection_id=connection.id,
        start_time=now.replace(hour=14, minute=0, second=0, microsecond=0),
        end_time=now.replace(hour=17, minute=0, second=0, microsecond=0),
        status='free',
        computed_at=now
    )
    
    # Tomorrow morning: 9:00 AM - 11:00 AM (2 hours)
    tomorrow = now + timedelta(days=1)
    free_slot3 = AvailabilitySlot(
        connection_id=connection.id,
        start_time=tomorrow.replace(hour=9, minute=0, second=0, microsecond=0),
        end_time=tomorrow.replace(hour=11, minute=0, second=0, microsecond=0),
        status='free',
        computed_at=now
    )
    
    session.add_all([free_slot1, free_slot2, free_slot3])
    session.commit()
    
    return session, connection.id


def test_task_related_suggestions():
    """Test 1: Generate task-related engagement suggestions."""
    print("\n=== Test 1: Task-Related Suggestions ===")
    
    session, connection_id = setup_test_db()
    service = EngagementSuggestionService()
    service.session = session  # Use test session
    service.availability_service.session = session  # Share session
    
    # User tasks with social keywords
    user_tasks = [
        {'id': 1, 'name': 'Schedule coffee with mentor', 'priority': 'high'},
        {'id': 2, 'name': 'Call Sarah for catch up', 'priority': 'medium'},
        {'id': 3, 'name': 'Write report', 'priority': 'high'}  # Not social
    ]
    
    suggestions = service.generate_engagement_suggestions(
        connection_id=connection_id,
        user_tasks=user_tasks,
        mood='neutral',
        energy_level='medium',
        lookback_days=7,
        max_suggestions=5
    )
    
    # Should find task-related suggestions
    task_suggestions = [s for s in suggestions if s.suggestion_type == 'task-related']
    
    print(f"Generated {len(task_suggestions)} task-related suggestions")
    
    for suggestion in task_suggestions:
        print(f"  - {suggestion.title}")
        print(f"    Time: {suggestion.suggested_time_slot['start'].strftime('%I:%M %p')}")
        print(f"    Related Task: {suggestion.related_task_name}")
    
    assert len(task_suggestions) > 0, "Should generate task-related suggestions"
    return suggestion if suggestions else None


def test_social_suggestions_with_mood():
    """Test 2: Social suggestions based on mood/energy."""
    print("\n=== Test 2: Social Suggestions with Mood ===")
    
    session, connection_id = setup_test_db()
    service = EngagementSuggestionService()
    service.session = session
    service.availability_service.session = session
    
    # Test with high energy (should suggest social)
    print("\nHigh energy, happy mood:")
    suggestions_happy = service.generate_engagement_suggestions(
        connection_id=connection_id,
        user_tasks=[],
        mood='happy',
        energy_level='high',
        lookback_days=7,
        max_suggestions=5
    )
    
    social_happy = [s for s in suggestions_happy if s.suggestion_type == 'social']
    print(f"  Generated {len(social_happy)} social suggestions")
    
    # Test with low energy (should NOT suggest social)
    print("\nLow energy, exhausted mood:")
    service._daily_suggestion_count = {}  # Reset counter
    suggestions_low = service.generate_engagement_suggestions(
        connection_id=connection_id,
        user_tasks=[],
        mood='exhausted',
        energy_level='low',
        lookback_days=7,
        max_suggestions=5
    )
    
    social_low = [s for s in suggestions_low if s.suggestion_type == 'social']
    print(f"  Generated {len(social_low)} social suggestions")
    
    assert len(social_happy) > 0, "Should suggest social for happy/high energy"
    assert len(social_low) == 0, "Should NOT suggest social for low energy"
    
    return True


def test_professional_suggestions():
    """Test 3: Professional engagement suggestions."""
    print("\n=== Test 3: Professional Suggestions ===")
    
    session, connection_id = setup_test_db()
    service = EngagementSuggestionService()
    service.session = session
    service.availability_service.session = session
    
    suggestions = service.generate_engagement_suggestions(
        connection_id=connection_id,
        user_tasks=[],
        mood='neutral',
        energy_level='high',
        lookback_days=7,
        max_suggestions=5
    )
    
    professional_suggestions = [s for s in suggestions if s.suggestion_type == 'professional']
    
    print(f"Generated {len(professional_suggestions)} professional suggestions")
    
    for suggestion in professional_suggestions:
        print(f"  - {suggestion.title}")
        print(f"    Time: {suggestion.suggested_time_slot['start'].strftime('%A at %I:%M %p')}")
        print(f"    Confidence: {int(suggestion.confidence_score * 100)}%")
    
    assert len(professional_suggestions) > 0, "Should generate professional suggestions"
    return True


def test_suggestion_acceptance():
    """Test 4: Accept suggestion and create calendar event."""
    print("\n=== Test 4: Suggestion Acceptance ===")
    
    session, connection_id = setup_test_db()
    
    # Mock calendar service since we don't want actual API calls
    from unittest.mock import Mock
    
    integration = EngagementSuggestionIntegration()
    integration.engagement_service.session = session
    integration.engagement_service.availability_service.session = session
    
    # Mock the calendar service create_event method
    mock_event = Mock()
    mock_event.id = 1
    mock_event.summary = "Test Engagement"
    
    integration.calendar_service.create_event = Mock(return_value=mock_event)
    integration.calendar_service.session = session
    
    # Generate a suggestion
    user_tasks = [{'id': 1, 'name': 'Schedule coffee with mentor', 'priority': 'high'}]
    suggestions = integration.generate_suggestions_for_context(
        connection_id=connection_id,
        user_tasks=user_tasks,
        mood='neutral',
        energy_level='medium'
    )
    
    if suggestions:
        suggestion = suggestions[0]
        print(f"Generated suggestion: {suggestion.title}")
        
        # Accept the suggestion
        event = integration.accept_suggestion(suggestion.suggestion_id)
        
        print(f"Accepted suggestion and created event")
        print(f"  Event ID: {event.id if event else 'None'}")
        
        # Check that create_event was called
        assert integration.calendar_service.create_event.called, "Should call create_event"
        print(f"Calendar event creation was triggered")
        
        return True
    
    print("No suggestions generated")
    return False


def test_suggestion_decline_learning():
    """Test 5: Decline suggestion and learn preferences."""
    print("\n=== Test 5: Suggestion Decline & Learning ===")
    
    session, connection_id = setup_test_db()
    integration = EngagementSuggestionIntegration()
    integration.engagement_service.session = session
    integration.engagement_service.availability_service.session = session
    
    # Generate suggestion
    user_tasks = [{'id': 1, 'name': 'Coffee meeting', 'priority': 'high'}]
    suggestions = integration.generate_suggestions_for_context(
        connection_id=connection_id,
        user_tasks=user_tasks,
        mood='neutral',
        energy_level='medium'
    )
    
    if suggestions:
        suggestion = suggestions[0]
        print(f"Generated suggestion: {suggestion.title}")
        
        # Decline with reason
        integration.decline_suggestion(suggestion.suggestion_id, "not_on_tuesdays")
        
        print(f"Declined suggestion with reason: 'not_on_tuesdays'")
        
        # Check preferences were updated
        preferences = integration.engagement_service.get_user_preferences()
        print(f"User preferences updated: {len(preferences)} entries")
        
        for key, value in preferences.items():
            print(f"  - {key}: {value['action']}")
        
        assert len(preferences) > 0, "Should store user preferences"
        return True
    
    print("No suggestions generated")
    return False


def test_daily_suggestion_limit():
    """Test 6: Respect daily suggestion limits (non-intrusive)."""
    print("\n=== Test 6: Daily Suggestion Limit ===")
    
    session, connection_id = setup_test_db()
    service = EngagementSuggestionService()
    service.session = session
    service.availability_service.session = session
    
    user_tasks = [
        {'id': i, 'name': f'Task {i}', 'priority': 'medium'}
        for i in range(10)
    ]
    
    # First call - should generate suggestions
    suggestions1 = service.generate_engagement_suggestions(
        connection_id=connection_id,
        user_tasks=user_tasks,
        mood='neutral',
        energy_level='medium',
        max_suggestions=2
    )
    
    print(f"First call: {len(suggestions1)} suggestions")
    
    # Second call immediately - should respect limit
    suggestions2 = service.generate_engagement_suggestions(
        connection_id=connection_id,
        user_tasks=user_tasks,
        mood='neutral',
        energy_level='medium',
        max_suggestions=2
    )
    
    print(f"Second call: {len(suggestions2)} suggestions")
    
    total = len(suggestions1) + len(suggestions2)
    print(f"Total suggestions: {total}")
    
    assert total <= 2, "Should limit to max_suggestions per day"
    return True


def run_all_tests():
    """Run all test cases."""
    print("="*60)
    print("Story 4.4: Proactive Engagement Suggestions - Test Suite")
    print("="*60)
    
    tests = {
        "Task-Related Suggestions": test_task_related_suggestions,
        "Social Suggestions with Mood": test_social_suggestions_with_mood,
        "Professional Suggestions": test_professional_suggestions,
        "Suggestion Acceptance": test_suggestion_acceptance,
        "Suggestion Decline & Learning": test_suggestion_decline_learning,
        "Daily Suggestion Limit": test_daily_suggestion_limit,
    }
    
    results = {}
    for test_name, test_func in tests.items():
        try:
            result = test_func()
            results[test_name] = "PASS" if result is not False else "FAIL"
        except Exception as e:
            print(f"\nTest failed with error: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = "FAIL"
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, result in results.items():
        icon = "[PASS]" if result == "PASS" else "[FAIL]"
        print(f"{icon} {test_name}: {result}")
    
    passed = sum(1 for r in results.values() if r == "PASS")
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed!")
        return True
    else:
        print(f"\n{total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

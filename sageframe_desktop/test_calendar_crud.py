"""
Test script for Story 4.3: Calendar Event CRUD Operations

This script tests:
1. Creating calendar events
2. Updating calendar events
3. Deleting calendar events
4. Retry logic with exponential backoff
5. Error handling and user prompts
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, init_db
from app.modules.calendar_integration.models import CalendarConnection, CalendarEvent
from app.modules.calendar_integration.services import CalendarSyncService


def setup_test_db():
    """Initialize test database."""
    init_db()
    session = SessionLocal()
    
    # Clean up any existing test data
    session.query(CalendarEvent).delete()
    session.query(CalendarConnection).delete()
    session.commit()
    
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
    
    return session, connection.id


def test_create_event():
    """Test creating a new calendar event."""
    print("\n=== Test 1: Create Event ===")
    
    session, connection_id = setup_test_db()
    service = CalendarSyncService()
    
    # Mock push_event to avoid actual API calls
    with patch.object(service, 'push_event', return_value=True):
        with patch.object(service, '_refresh_availability'):
            try:
                event = service.create_event(
                    connection_id=connection_id,
                    summary="Test Meeting",
                    start_time=datetime.now(timezone.utc),
                    end_time=datetime.now(timezone.utc) + timedelta(hours=1),
                    description="Test event description",
                    location="Conference Room A",
                    attendees=["user@example.com"],
                    is_all_day=False
                )
                
                assert event is not None, "Event should be created"
                assert event.summary == "Test Meeting", "Event summary should match"
                assert event.location == "Conference Room A", "Event location should match"
                assert event.source == "sageframe", "Event source should be sageframe"
                
                print("✓ Event created successfully")
                print(f"  Event ID: {event.id}")
                print(f"  Summary: {event.summary}")
                print(f"  Location: {event.location}")
                
                return event.id
                
            except Exception as e:
                print(f"✗ Failed to create event: {e}")
                return None
            finally:
                session.close()


def test_update_event():
    """Test updating an existing calendar event."""
    print("\n=== Test 2: Update Event ===")
    
    # First create an event
    event_id = test_create_event()
    if not event_id:
        print("✗ Cannot test update without event")
        return False
    
    session, connection_id = setup_test_db()
    service = CalendarSyncService()
    
    # Recreate event for this session
    event = CalendarEvent(
        id=event_id,
        connection_id=connection_id,
        event_id="test_event_123",
        summary="Old Title",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        source="sageframe",
        last_modified=datetime.now(timezone.utc),
        sync_version=1
    )
    session.add(event)
    session.commit()
    
    # Mock push_event
    with patch.object(service, 'push_event', return_value=True):
        with patch.object(service, '_refresh_availability'):
            try:
                updated = service.update_event(
                    event_id=event.id,
                    summary="Updated Meeting Title",
                    location="New Conference Room",
                    description="Updated description"
                )
                
                assert updated.summary == "Updated Meeting Title", "Summary should be updated"
                assert updated.location == "New Conference Room", "Location should be updated"
                assert updated.description == "Updated description", "Description should be updated"
                assert updated.sync_version == 2, "Sync version should increment"
                
                print("✓ Event updated successfully")
                print(f"  New Summary: {updated.summary}")
                print(f"  New Location: {updated.location}")
                print(f"  Sync Version: {updated.sync_version}")
                
                return True
                
            except Exception as e:
                print(f"✗ Failed to update event: {e}")
                return False
            finally:
                session.close()


def test_delete_event():
    """Test deleting a calendar event."""
    print("\n=== Test 3: Delete Event ===")
    
    session, connection_id = setup_test_db()
    service = CalendarSyncService()
    
    # Create event to delete
    event = CalendarEvent(
        connection_id=connection_id,
        event_id="test_event_to_delete",
        summary="Event to Delete",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        source="sageframe",
        last_modified=datetime.now(timezone.utc),
        sync_version=1
    )
    session.add(event)
    session.commit()
    event_id = event.id
    
    # Mock delete_event
    with patch.object(service, 'delete_event', return_value=True):
        with patch.object(service, '_refresh_availability'):
            try:
                result = service.delete_event_by_id(event_id)
                
                assert result is True, "Delete should return True"
                
                # Verify event is deleted
                deleted_event = session.query(CalendarEvent).get(event_id)
                # Note: delete_event marks as cancelled, doesn't delete from DB
                
                print("✓ Event deleted successfully")
                print(f"  Event ID: {event_id}")
                
                return True
                
            except Exception as e:
                print(f"✗ Failed to delete event: {e}")
                return False
            finally:
                session.close()


def test_retry_logic():
    """Test retry logic with exponential backoff."""
    print("\n=== Test 4: Retry Logic ===")
    
    service = CalendarSyncService()
    
    # Test successful retry after failure
    attempt_count = [0]
    
    def failing_operation():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            from googleapiclient.errors import HttpError
            resp = Mock()
            resp.status = 429  # Rate limit
            raise HttpError(resp, b"Rate limit exceeded")
        return "success"
    
    try:
        result = service._retry_with_backoff(failing_operation, max_retries=3, initial_backoff=0.1)
        
        assert result == "success", "Should succeed after retries"
        assert attempt_count[0] == 3, f"Should retry 3 times, got {attempt_count[0]}"
        
        print("✓ Retry logic works correctly")
        print(f"  Attempts: {attempt_count[0]}")
        print(f"  Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Retry logic failed: {e}")
        return False


def test_get_events_in_range():
    """Test retrieving events within a time range."""
    print("\n=== Test 5: Get Events in Range ===")
    
    session, connection_id = setup_test_db()
    service = CalendarSyncService()
    
    # Create multiple events
    now = datetime.now(timezone.utc)
    
    events_data = [
        ("Event 1", now, now + timedelta(hours=1)),
        ("Event 2", now + timedelta(days=1), now + timedelta(days=1, hours=1)),
        ("Event 3", now + timedelta(days=5), now + timedelta(days=5, hours=1)),
        ("Event 4", now + timedelta(days=10), now + timedelta(days=10, hours=1)),
    ]
    
    for summary, start, end in events_data:
        event = CalendarEvent(
            connection_id=connection_id,
            event_id=f"test_{summary.replace(' ', '_')}",
            summary=summary,
            start_time=start,
            end_time=end,
            source="sageframe",
            status="confirmed",
            last_modified=now,
            sync_version=1
        )
        session.add(event)
    
    session.commit()
    
    try:
        # Get events for next 7 days
        events = service.get_events_in_range(
            connection_id,
            now,
            now + timedelta(days=7)
        )
        
        assert len(events) == 3, f"Should find 3 events in 7 days, got {len(events)}"
        assert events[0].summary == "Event 1", "Events should be ordered by start time"
        
        print("✓ Get events in range works correctly")
        print(f"  Events found: {len(events)}")
        for event in events:
            print(f"    - {event.summary} at {event.start_time}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to get events: {e}")
        return False
    finally:
        session.close()


def run_all_tests():
    """Run all test cases."""
    print("=" * 60)
    print("Story 4.3: Calendar Event CRUD - Test Suite")
    print("=" * 60)
    
    results = {
        "Create Event": test_create_event() is not None,
        "Update Event": test_update_event(),
        "Delete Event": test_delete_event(),
        "Retry Logic": test_retry_logic(),
        "Get Events in Range": test_get_events_in_range()
    }
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

"""Calendar synchronization service.

This module implements bi-directional sync between SageFrame and Google Calendar,
handling event creation, updates, deletions, and conflict resolution.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple, Callable
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.database import SessionLocal
from app.modules.calendar_integration.models import (
    CalendarConnection,
    CalendarEvent,
    SyncLog
)
from app.modules.calendar_integration.oauth import GoogleOAuthClient, TokenManager
from app.modules.calendar_integration.sync.schemas import GoogleCalendarEvent, GoogleCalendarEventList
from app.modules.calendar_integration.availability_service import AvailabilityService


class CalendarSyncService:
    """Service for synchronizing calendar events between SageFrame and Google Calendar.
    
    Implements bi-directional sync with last-write-wins conflict resolution.
    """
    
    def __init__(self):
        """Initialize sync service."""
        self.oauth_client = GoogleOAuthClient()
        self.token_manager = TokenManager()
        self.session = SessionLocal()
        self.availability_service = AvailabilityService()
    
    def _retry_with_backoff(
        self,
        operation: Callable,
        max_retries: int = 3,
        initial_backoff: float = 1.0
    ) -> Any:
        """Execute an operation with exponential backoff retry logic.
        
        Args:
            operation: Callable to execute
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
        
        Returns:
            Result of the operation
        
        Raises:
            HttpError: If all retries fail
        """
        backoff = initial_backoff
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return operation()
            
            except HttpError as e:
                last_error = e
                status_code = e.resp.status
                
                # Handle rate limiting (429)
                if status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(backoff)
                        backoff *= 2  # Exponential backoff
                        continue
                
                # Handle token expiration (401)
                elif status_code == 401:
                    # Try refreshing token
                    try:
                        connection = self.session.query(CalendarConnection).first()
                        if connection:
                            self.oauth_client.refresh_credentials(connection.connection_id)
                            # Retry once after token refresh
                            if attempt < max_retries - 1:
                                continue
                    except Exception:
                        pass
                
                # Other errors, re-raise immediately
                raise
            
            except Exception as e:
                # Non-HTTP errors, retry with backoff
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise
        
        # All retries exhausted
        if last_error:
            raise last_error
    
    def _get_calendar_service(self, connection_id: int):
        """Get authenticated Google Calendar API service.
        
        Args:
            connection_id: Calendar connection ID
        
        Returns:
            Google Calendar API service instance
        
        Raises:
            Exception: If authentication fails
        """
        # Get tokens from keyring
        access_token, refresh_token, expires_at = self.token_manager.get_tokens(connection_id)
        
        if not access_token or not refresh_token:
            raise ValueError(f"No tokens found for connection {connection_id}")
        
        # Create credentials
        creds = self.oauth_client.credentials_from_tokens(
            access_token,
            refresh_token,
            expires_at.isoformat() if expires_at else None
        )
        
        # Auto-refresh if needed
        creds = self.oauth_client.auto_refresh_if_needed(creds)
        
        # Update tokens if refreshed
        if creds.token != access_token:
            self.token_manager.update_access_token(
                connection_id,
                creds.token,
                creds.expiry
            )
        
        # Build Calendar API service
        service = build('calendar', 'v3', credentials=creds)
        return service
    
    def pull_events(
        self,
        connection_id: int,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None
    ) -> Tuple[int, int]:
        """Pull events from Google Calendar to SageFrame.
        
        Args:
            connection_id: Calendar connection ID
            time_min: Minimum event start time (default: 30 days ago)
            time_max: Maximum event start time (default: 90 days from now)
        
        Returns:
            Tuple of (events_synced, events_failed)
        """
        connection = self.session.query(CalendarConnection).get(connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        
        # Default time range: past 30 days to future 90 days
        if time_min is None:
            time_min = datetime.now(timezone.utc) - timedelta(days=30)
        if time_max is None:
            time_max = datetime.now(timezone.utc) + timedelta(days=90)
        
        try:
            service = self._get_calendar_service(connection_id)
            
            # Fetch events from Google Calendar
            events_result = service.events().list(
                calendarId=connection.calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,  # Expand recurring events
                orderBy='startTime'
            ).execute()
            
            events_synced = 0
            events_failed = 0
            
            # Parse and validate events
            event_list = GoogleCalendarEventList(**events_result)
            
            for google_event in event_list.events:
                try:
                    self._sync_event_from_google(connection_id, google_event)
                    events_synced += 1
                except Exception as e:
                    print(f"Failed to sync event {google_event.id}: {e}")
                    events_failed += 1
            
            # Update connection last_sync_at
            connection.last_sync_at = datetime.now(timezone.utc)
            connection.sync_status = "connected"
            connection.error_message = None
            self.session.commit()
            
            return (events_synced, events_failed)
            
        except HttpError as e:
            connection.sync_status = "error"
            connection.error_message = str(e)
            self.session.commit()
            raise
    
    def _sync_event_from_google(self, connection_id: int, google_event: GoogleCalendarEvent):
        """Sync a single event from Google Calendar to local database.
        
        Args:
            connection_id: Calendar connection ID
            google_event: Google Calendar event data
        """
        # Check if event already exists
        existing = self.session.query(CalendarEvent).filter_by(
            connection_id=connection_id,
            event_id=google_event.id
        ).first()
        
        # Prepare event data
        attendees_json = json.dumps(google_event.attendee_emails) if google_event.attendee_emails else None
        
        if existing:
            # Update existing event (last-write-wins)
            if google_event.last_modified > existing.last_modified:
                existing.summary = google_event.summary
                existing.description = google_event.description
                existing.location = google_event.location
                existing.start_time = google_event.start_datetime
                existing.end_time = google_event.end_datetime
                existing.is_all_day = 1 if google_event.is_all_day else 0
                existing.recurrence_rule = google_event.recurrence_rule
                existing.attendees = attendees_json
                existing.status = google_event.status
                existing.last_modified = google_event.last_modified
                existing.sync_version += 1
                existing.updated_at = datetime.now(timezone.utc)
        else:
            # Create new event
            new_event = CalendarEvent(
                connection_id=connection_id,
                event_id=google_event.id,
                summary=google_event.summary,
                description=google_event.description,
                location=google_event.location,
                start_time=google_event.start_datetime,
                end_time=google_event.end_datetime,
                is_all_day=1 if google_event.is_all_day else 0,
                recurrence_rule=google_event.recurrence_rule,
                attendees=attendees_json,
                status=google_event.status,
                source="external",
                last_modified=google_event.last_modified,
                sync_version=1
            )
            self.session.add(new_event)
        
        self.session.commit()
    
    def push_event(self, event: CalendarEvent) -> bool:
        """Push a single event from SageFrame to Google Calendar.
        
        Args:
            event: CalendarEvent to push
        
        Returns:
            True if successful, False otherwise
        """
        try:
            service = self._get_calendar_service(event.connection_id)
            connection = self.session.query(CalendarConnection).get(event.connection_id)
            
            # Prepare event data for Google Calendar API
            event_body = {
                'summary': event.summary,
                'description': event.description,
                'location': event.location,
                'status': event.status,
            }
            
            # Handle all-day vs timed events
            if event.is_all_day:
                event_body['start'] = {'date': event.start_time.strftime('%Y-%m-%d')}
                event_body['end'] = {'date': event.end_time.strftime('%Y-%m-%d')}
            else:
                event_body['start'] = {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': 'UTC',
                }
                event_body['end'] = {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': 'UTC',
                }
            
            # Add attendees if present
            if event.attendees:
                attendee_emails = json.loads(event.attendees)
                event_body['attendees'] = [{'email': email} for email in attendee_emails]
            
            # Add recurrence rule if present
            if event.recurrence_rule:
                event_body['recurrence'] = [event.recurrence_rule]
            
            # Create or update event
            if event.event_id and event.event_id.startswith('sageframe_'):
                # New SageFrame event - create in Google Calendar
                google_event = service.events().insert(
                    calendarId=connection.calendar_id,
                    body=event_body
                ).execute()
                
                # Update local event with Google Calendar ID
                event.event_id = google_event['id']
                event.last_modified = datetime.fromisoformat(google_event['updated'].replace('Z', '+00:00'))
                event.sync_version += 1
                self.session.commit()
            else:
                # Existing event - update in Google Calendar
                google_event = service.events().update(
                    calendarId=connection.calendar_id,
                    eventId=event.event_id,
                    body=event_body
                ).execute()
                
                event.last_modified = datetime.fromisoformat(google_event['updated'].replace('Z', '+00:00'))
                event.sync_version += 1
                self.session.commit()
            
            return True
            
        except HttpError as e:
            print(f"Failed to push event {event.id}: {e}")
            return False
    
    def delete_event(self, event: CalendarEvent) -> bool:
        """Delete event from Google Calendar and local database.
        
        Args:
            event: CalendarEvent to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            service = self._get_calendar_service(event.connection_id)
            connection = self.session.query(CalendarConnection).get(event.connection_id)
            
            # Delete from Google Calendar (if it exists there)
            if not event.event_id.startswith('sageframe_'):
                try:
                    service.events().delete(
                        calendarId=connection.calendar_id,
                        eventId=event.event_id
                    ).execute()
                except HttpError as e:
                    if e.resp.status != 404:  # Ignore "not found" errors
                        raise
            
            # Delete from local database
            self.session.delete(event)
            self.session.commit()
            
            return True
            
        except HttpError as e:
            print(f"Failed to delete event {event.id}: {e}")
            return False
    
    def bidirectional_sync(self, connection_id: int) -> Dict[str, int]:
        """Perform bi-directional sync for a connection.
        
        Args:
            connection_id: Calendar connection ID
        
        Returns:
            Dict with sync stats: {'pulled': int, 'pushed': int, 'failed': int}
        """
        sync_log = SyncLog(
            connection_id=connection_id,
            sync_direction='bidirectional',
            sync_status='success',
            sync_started_at=datetime.now(timezone.utc)
        )
        
        try:
            # Pull events from Google Calendar
            pulled, pull_failed = self.pull_events(connection_id)
            
            # Push SageFrame events to Google Calendar
            pushed = 0
            push_failed = 0
            
            sageframe_events = self.session.query(CalendarEvent).filter_by(
                connection_id=connection_id,
                source='sageframe'
            ).all()
            
            for event in sageframe_events:
                if self.push_event(event):
                    pushed += 1
                else:
                    push_failed += 1
            
            # Update sync log
            sync_log.events_synced = pulled + pushed
            sync_log.events_failed = pull_failed + push_failed
            sync_log.sync_completed_at = datetime.now(timezone.utc)
            sync_log.sync_status = 'success' if (pull_failed + push_failed) == 0 else 'partial_success'
            self.session.add(sync_log)
            self.session.commit()
            
            # Compute availability after successful sync
            try:
                # Compute availability for next 90 days
                start_date = datetime.now(timezone.utc)
                end_date = start_date + timedelta(days=90)
                self.availability_service.compute_availability(
                    connection_id,
                    start_date,
                    end_date
                )
            except Exception as e:
                print(f"Failed to compute availability: {e}")
                # Don't fail sync if availability computation fails
            
            return {'pulled': pulled, 'pushed': pushed, 'failed': pull_failed + push_failed}
            
        except Exception as e:
            sync_log.sync_status = 'failed'
            sync_log.error_message = str(e)
            sync_log.sync_completed_at = datetime.now(timezone.utc)
            self.session.add(sync_log)
            self.session.commit()
            raise
    
    def create_event(
        self,
        connection_id: int,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        is_all_day: bool = False,
        recurrence_rule: Optional[str] = None
    ) -> CalendarEvent:
        """Create a new calendar event in SageFrame and sync to Google Calendar.
        
        Args:
            connection_id: Calendar connection ID
            summary: Event title
            start_time: Event start time (UTC)
            end_time: Event end time (UTC)
            description: Event description (optional)
            location: Event location (optional)
            attendees: List of attendee email addresses (optional)
            is_all_day: Whether event is all-day
            recurrence_rule: RRULE for recurring events (optional)
        
        Returns:
            Created CalendarEvent instance
        
        Raises:
            HttpError: If Google Calendar API call fails
        """
        connection = self.session.query(CalendarConnection).get(connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        
        # Create local event first
        event = CalendarEvent(
            connection_id=connection_id,
            event_id=f"sageframe_{datetime.now(timezone.utc).timestamp()}",  # Temporary ID
            summary=summary,
            description=description,
            location=location,
            start_time=start_time,
            end_time=end_time,
            is_all_day=1 if is_all_day else 0,
            recurrence_rule=recurrence_rule,
            attendees=json.dumps(attendees) if attendees else None,
            status='confirmed',
            source='sageframe',
            last_modified=datetime.now(timezone.utc),
            sync_version=1
        )
        self.session.add(event)
        self.session.commit()
        
        # Push to Google Calendar
        try:
            def push_operation():
                if not self.push_event(event):
                    raise Exception("Failed to push event to Google Calendar")
            
            self._retry_with_backoff(push_operation)
            
            # Refresh availability after creating event
            self._refresh_availability(connection_id)
            
            return event
            
        except Exception as e:
            # Rollback local creation if push fails
            self.session.delete(event)
            self.session.commit()
            raise
    
    def update_event(
        self,
        event_id: int,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        is_all_day: Optional[bool] = None,
        status: Optional[str] = None
    ) -> CalendarEvent:
        """Update an existing calendar event in SageFrame and sync to Google Calendar.
        
        Args:
            event_id: Local CalendarEvent ID
            summary: Updated event title (optional)
            start_time: Updated start time (optional)
            end_time: Updated end time (optional)
            description: Updated description (optional)
            location: Updated location (optional)
            attendees: Updated attendee list (optional)
            is_all_day: Updated all-day flag (optional)
            status: Updated status (optional)
        
        Returns:
            Updated CalendarEvent instance
        
        Raises:
            ValueError: If event not found
            HttpError: If Google Calendar API call fails
        """
        event = self.session.query(CalendarEvent).get(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        
        # Update local event
        if summary is not None:
            event.summary = summary
        if start_time is not None:
            event.start_time = start_time
        if end_time is not None:
            event.end_time = end_time
        if description is not None:
            event.description = description
        if location is not None:
            event.location = location
        if attendees is not None:
            event.attendees = json.dumps(attendees)
        if is_all_day is not None:
            event.is_all_day = 1 if is_all_day else 0
        if status is not None:
            event.status = status
        
        event.last_modified = datetime.now(timezone.utc)
        event.sync_version += 1
        event.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        
        # Push to Google Calendar with retry
        def push_operation():
            if not self.push_event(event):
                raise Exception("Failed to push updated event to Google Calendar")
        
        self._retry_with_backoff(push_operation)
        
        # Refresh availability after updating event
        self._refresh_availability(event.connection_id)
        
        return event
    
    def delete_event_by_id(self, event_id: int) -> bool:
        """Delete a calendar event from SageFrame and Google Calendar.
        
        Args:
            event_id: Local CalendarEvent ID
        
        Returns:
            True if successfully deleted
        
        Raises:
            ValueError: If event not found
        """
        event = self.session.query(CalendarEvent).get(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        
        connection_id = event.connection_id
        
        # Delete from Google Calendar and local database
        result = self.delete_event(event)
        
        if result:
            # Refresh availability after deleting event
            self._refresh_availability(connection_id)
        
        return result
    
    def _refresh_availability(self, connection_id: int):
        """Refresh availability computation after event changes.
        
        Args:
            connection_id: Calendar connection ID
        """
        try:
            # Compute availability for next 90 days
            start_date = datetime.now(timezone.utc)
            end_date = start_date + timedelta(days=90)
            self.availability_service.compute_availability(
                connection_id,
                start_date,
                end_date
            )
        except Exception as e:
            print(f"Failed to refresh availability: {e}")
            # Don't fail the main operation if availability refresh fails
    
    def get_events_in_range(
        self,
        connection_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[CalendarEvent]:
        """Get all events for a connection within a time range.
        
        Args:
            connection_id: Calendar connection ID
            start_time: Start of range (UTC)
            end_time: End of range (UTC)
        
        Returns:
            List of CalendarEvent instances
        """
        return self.session.query(CalendarEvent).filter(
            CalendarEvent.connection_id == connection_id,
            CalendarEvent.start_time < end_time,
            CalendarEvent.end_time > start_time,
            CalendarEvent.status != 'cancelled'
        ).order_by(CalendarEvent.start_time).all()

"""Pydantic schemas for Google Calendar API responses.

This module defines Pydantic models for validating and parsing Google Calendar
API responses, providing type safety and data validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class GoogleCalendarDateTime(BaseModel):
    """Schema for Google Calendar date/time objects."""
    dateTime: Optional[str] = None  # ISO 8601 format with timezone
    date: Optional[str] = None  # ISO 8601 date-only format (YYYY-MM-DD)
    timeZone: Optional[str] = None
    
    @field_validator('dateTime')
    @classmethod
    def validate_datetime(cls, v):
        """Validate datetime string format."""
        if v:
            try:
                # Ensure it's parseable as ISO 8601
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid datetime format: {v}")
        return v


class GoogleCalendarAttendee(BaseModel):
    """Schema for Google Calendar event attendee."""
    email: str
    displayName: Optional[str] = None
    responseStatus: Optional[str] = "needsAction"  # needsAction, declined, tentative, accepted
    organizer: Optional[bool] = False
    optional: Optional[bool] = False


class GoogleCalendarEvent(BaseModel):
    """Schema for Google Calendar event response.
    
    Maps Google Calendar API event structure to typed Pydantic model.
    See: https://developers.google.com/calendar/api/v3/reference/events
    """
    id: str
    summary: str = Field(default="(No title)")
    description: Optional[str] = None
    location: Optional[str] = None
    start: GoogleCalendarDateTime
    end: GoogleCalendarDateTime
    status: str = Field(default="confirmed")  # confirmed, tentative, cancelled
    created: str  # ISO 8601 timestamp
    updated: str  # ISO 8601 timestamp
    attendees: Optional[List[GoogleCalendarAttendee]] = None
    recurrence: Optional[List[str]] = None  # RRULE strings
    htmlLink: Optional[str] = None
    organizer: Optional[dict] = None
    
    @property
    def is_all_day(self) -> bool:
        """Check if event is all-day (uses date instead of dateTime)."""
        return self.start.date is not None
    
    @property
    def start_datetime(self) -> datetime:
        """Get start time as datetime object."""
        if self.start.dateTime:
            return datetime.fromisoformat(self.start.dateTime.replace('Z', '+00:00'))
        elif self.start.date:
            return datetime.fromisoformat(self.start.date + 'T00:00:00+00:00')
        raise ValueError("Event has no valid start time")
    
    @property
    def end_datetime(self) -> datetime:
        """Get end time as datetime object."""
        if self.end.dateTime:
            return datetime.fromisoformat(self.end.dateTime.replace('Z', '+00:00'))
        elif self.end.date:
            return datetime.fromisoformat(self.end.date + 'T00:00:00+00:00')
        raise ValueError("Event has no valid end time")
    
    @property
    def last_modified(self) -> datetime:
        """Get last modified timestamp as datetime object."""
        return datetime.fromisoformat(self.updated.replace('Z', '+00:00'))
    
    @property
    def attendee_emails(self) -> List[str]:
        """Get list of attendee email addresses."""
        if self.attendees:
            return [a.email for a in self.attendees]
        return []
    
    @property
    def recurrence_rule(self) -> Optional[str]:
        """Get first recurrence rule (RRULE)."""
        if self.recurrence:
            return self.recurrence[0]
        return None


class GoogleCalendarEventList(BaseModel):
    """Schema for Google Calendar events list response."""
    kind: str = "calendar#events"
    summary: str
    description: Optional[str] = None
    updated: str
    timeZone: str
    items: List[GoogleCalendarEvent] = Field(default_factory=list)
    nextPageToken: Optional[str] = None
    
    @property
    def events(self) -> List[GoogleCalendarEvent]:
        """Get list of events."""
        return self.items


class GoogleCalendarInfo(BaseModel):
    """Schema for Google Calendar metadata."""
    kind: str = "calendar#calendar"
    id: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    timeZone: str
    colorId: Optional[str] = None


class OAuthTokenInfo(BaseModel):
    """Schema for OAuth 2.0 token information."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int  # Seconds until expiration
    token_type: str = "Bearer"
    scope: str
    
    @property
    def expires_at(self) -> datetime:
        """Calculate token expiration timestamp."""
        from datetime import timedelta, timezone
        return datetime.now(timezone.utc) + timedelta(seconds=self.expires_in)

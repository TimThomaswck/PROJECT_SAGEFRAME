"""SQLAlchemy models for calendar integration.

This module defines the data models for calendar connections, events, and sync logs,
supporting bi-directional synchronization with external calendars (Google Calendar).
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class CalendarConnection(Base):
    """Model for external calendar connections (e.g., Google Calendar).
    
    Stores OAuth connection details and sync status. OAuth tokens are stored
    securely in keyring, not in this database table.
    
    Attributes:
        id: Primary key
        provider: Calendar provider name ('google_calendar')
        connection_name: User-friendly name (e.g., "Work Calendar")
        user_email: Connected calendar email address
        calendar_id: Provider's calendar ID (e.g., "primary" for Google)
        sync_enabled: Whether sync is active (boolean 0/1)
        last_sync_at: Timestamp of last successful sync (ISO 8601 UTC)
        sync_status: Current status ('connected', 'syncing', 'error', 'disconnected')
        error_message: Last error details if sync_status is 'error'
        created_at: Timestamp of creation (ISO 8601 UTC)
        updated_at: Timestamp of last update (ISO 8601 UTC)
        events: Relationship to CalendarEvent entries
        sync_logs: Relationship to SyncLog entries
    """
    
    __tablename__ = "calendar_connections"
    
    id = Column(Integer, primary_key=True)
    provider = Column(String(50), nullable=False, default="google_calendar")
    connection_name = Column(String(200), nullable=False)
    user_email = Column(String(255), nullable=False, index=True)
    calendar_id = Column(String(255), nullable=False)
    sync_enabled = Column(Integer, nullable=False, default=1)  # Boolean: 1=enabled, 0=disabled
    last_sync_at = Column(DateTime, nullable=True)
    sync_status = Column(String(50), nullable=False, default="connected")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Unique constraint: one connection per provider + email + calendar_id
    __table_args__ = (UniqueConstraint("provider", "user_email", "calendar_id", name="uq_calendar_connection"),)
    
    # Relationships
    events = relationship("CalendarEvent", back_populates="connection", cascade="all, delete-orphan")
    sync_logs = relationship("SyncLog", back_populates="connection", cascade="all, delete-orphan")
    availability_slots = relationship("AvailabilitySlot", back_populates="connection", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CalendarConnection(id={self.id}, provider={self.provider}, email={self.user_email})>"


class CalendarEvent(Base):
    """Model for synchronized calendar events.
    
    Stores events from both SageFrame and external calendars, tracking source
    and sync metadata for conflict resolution.
    
    Attributes:
        id: Primary key
        connection_id: Foreign key to CalendarConnection
        event_id: Provider's event ID (e.g., Google Calendar event ID)
        summary: Event title
        description: Event description
        location: Event location
        start_time: Event start time (ISO 8601 UTC)
        end_time: Event end time (ISO 8601 UTC)
        is_all_day: Whether event is all-day (boolean 0/1)
        recurrence_rule: Recurrence rule (RRULE format per RFC 5545)
        attendees: JSON array of attendee email addresses
        status: Event status ('confirmed', 'tentative', 'cancelled')
        source: Event origin ('sageframe' or 'external')
        last_modified: Event's last modification timestamp from provider
        sync_version: Incrementing version for conflict detection
        created_at: Timestamp of creation (ISO 8601 UTC)
        updated_at: Timestamp of last update (ISO 8601 UTC)
        connection: Relationship to parent CalendarConnection
    """
    
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("calendar_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(255), nullable=False)  # Google Calendar event ID
    summary = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    is_all_day = Column(Integer, nullable=False, default=0)  # Boolean
    recurrence_rule = Column(Text, nullable=True)  # RRULE format
    attendees = Column(Text, nullable=True)  # JSON array
    status = Column(String(50), nullable=False, default="confirmed")
    source = Column(String(50), nullable=False, default="external")  # 'sageframe' or 'external'
    last_modified = Column(DateTime, nullable=False)
    sync_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Unique constraint: one event per connection + event_id
    __table_args__ = (UniqueConstraint("connection_id", "event_id", name="uq_calendar_event"),)
    
    # Relationship to connection
    connection = relationship("CalendarConnection", back_populates="events")
    
    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, event_id={self.event_id}, summary={self.summary})>"


class SyncLog(Base):
    """Log entries for calendar synchronization operations.
    
    Tracks sync history, success/failure status, and error details for debugging
    and user visibility.
    
    Attributes:
        id: Primary key
        connection_id: Foreign key to CalendarConnection
        sync_direction: Sync direction ('push', 'pull', 'bidirectional')
        sync_status: Sync result ('success', 'partial_success', 'failed')
        events_synced: Number of events successfully synced
        events_failed: Number of events that failed to sync
        error_message: Error details if sync_status is 'failed'
        sync_started_at: Sync start timestamp (ISO 8601 UTC)
        sync_completed_at: Sync completion timestamp (ISO 8601 UTC)
        created_at: Timestamp of log entry creation (ISO 8601 UTC)
        connection: Relationship to parent CalendarConnection
    """
    
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("calendar_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    sync_direction = Column(String(50), nullable=False)  # 'push', 'pull', 'bidirectional'
    sync_status = Column(String(50), nullable=False)  # 'success', 'partial_success', 'failed'
    events_synced = Column(Integer, nullable=False, default=0)
    events_failed = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    sync_started_at = Column(DateTime, nullable=False)
    sync_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to connection
    connection = relationship("CalendarConnection", back_populates="sync_logs")
    
    def __repr__(self):
        return f"<SyncLog(id={self.id}, connection_id={self.connection_id}, status={self.sync_status})>"


class AvailabilitySlot(Base):
    """Model for computed availability slots (free/busy periods).
    
    Stores pre-calculated free and busy time slots for efficient querying.
    Computed from calendar events and refreshed on sync completion.
    
    Attributes:
        id: Primary key
        connection_id: Foreign key to CalendarConnection
        start_time: Slot start time (ISO 8601 UTC)
        end_time: Slot end time (ISO 8601 UTC)
        status: Slot status ('free' or 'busy')
        event_id: Foreign key to calendar_events.id (if status is 'busy')
        event_summary: Event title (denormalized for quick display)
        computed_at: Timestamp when slot was computed (ISO 8601 UTC)
        connection: Relationship to parent CalendarConnection
    """
    
    __tablename__ = "availability_slots"
    
    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("calendar_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # 'free' or 'busy'
    event_id = Column(Integer, ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=True)
    event_summary = Column(Text, nullable=True)  # Denormalized for performance
    computed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to connection
    connection = relationship("CalendarConnection", back_populates="availability_slots")
    
    def __repr__(self):
        return f"<AvailabilitySlot(id={self.id}, status={self.status}, start={self.start_time}, end={self.end_time})>"

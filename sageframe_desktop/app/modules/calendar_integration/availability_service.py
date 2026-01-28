"""Availability analysis service for calendar integration.

This module provides services for analyzing calendar events to determine
free and busy time slots, enabling intelligent scheduling features.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dateutil.rrule import rrulestr

from app.database import SessionLocal
from app.modules.calendar_integration.models import (
    CalendarConnection,
    CalendarEvent,
    AvailabilitySlot
)


class AvailabilityService:
    """Service for computing and querying calendar availability (free/busy times).
    
    Analyzes calendar events to identify busy periods and compute free slots
    for intelligent scheduling and time blocking features.
    """
    
    def __init__(self):
        """Initialize availability service."""
        self.session = SessionLocal()
    
    def compute_availability(
        self,
        connection_id: int,
        start_date: datetime,
        end_date: datetime,
        working_hours: Optional[Tuple[int, int]] = None
    ) -> int:
        """Compute availability slots for a connection within a date range.
        
        Analyzes all events (including expanded recurring events) and creates
        availability slot records for efficient querying.
        
        Args:
            connection_id: Calendar connection ID
            start_date: Start of analysis range (UTC)
            end_date: End of analysis range (UTC)
            working_hours: Optional tuple of (start_hour, end_hour) in 24h format
                          e.g., (9, 17) for 9 AM to 5 PM
        
        Returns:
            Number of availability slots computed
        """
        # Delete existing availability slots in this range
        self.session.query(AvailabilitySlot).filter(
            AvailabilitySlot.connection_id == connection_id,
            AvailabilitySlot.start_time >= start_date,
            AvailabilitySlot.end_time <= end_date
        ).delete()
        self.session.commit()
        
        # Get all events in range
        events = self.session.query(CalendarEvent).filter(
            CalendarEvent.connection_id == connection_id,
            CalendarEvent.start_time < end_date,
            CalendarEvent.end_time > start_date,
            CalendarEvent.status != 'cancelled'
        ).order_by(CalendarEvent.start_time).all()
        
        # Expand recurring events
        expanded_events = []
        for event in events:
            if event.recurrence_rule:
                expanded_events.extend(self._expand_recurring_event(event, start_date, end_date))
            else:
                expanded_events.append(event)
        
        # Sort by start time
        expanded_events.sort(key=lambda e: e.start_time)
        
        # Create busy slots from events
        slots_created = 0
        computed_at = datetime.now(timezone.utc)
        
        for event in expanded_events:
            # Ensure event times are within range
            event_start = max(event.start_time, start_date)
            event_end = min(event.end_time, end_date)
            
            if event_start < event_end:
                busy_slot = AvailabilitySlot(
                    connection_id=connection_id,
                    start_time=event_start,
                    end_time=event_end,
                    status='busy',
                    event_id=event.id if hasattr(event, 'id') and not isinstance(event.id, property) else None,
                    event_summary=event.summary,
                    computed_at=computed_at
                )
                self.session.add(busy_slot)
                slots_created += 1
        
        # Create free slots (gaps between busy periods)
        if working_hours:
            free_slots = self._compute_free_slots_with_working_hours(
                connection_id,
                expanded_events,
                start_date,
                end_date,
                working_hours,
                computed_at
            )
            slots_created += free_slots
        else:
            free_slots = self._compute_free_slots(
                connection_id,
                expanded_events,
                start_date,
                end_date,
                computed_at
            )
            slots_created += free_slots
        
        self.session.commit()
        return slots_created
    
    def _expand_recurring_event(
        self,
        event: CalendarEvent,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Expand a recurring event into individual occurrences.
        
        Args:
            event: Recurring event to expand
            start_date: Start of expansion range
            end_date: End of expansion range
        
        Returns:
            List of CalendarEvent instances (not persisted to DB)
        """
        if not event.recurrence_rule:
            return [event]
        
        try:
            # Parse RRULE
            rrule = rrulestr(event.recurrence_rule, dtstart=event.start_time)
            
            # Get occurrences within range
            occurrences = []
            event_duration = event.end_time - event.start_time
            
            for dt in rrule.between(start_date, end_date, inc=True):
                # Create event occurrence (transient, not saved to DB)
                occurrence = CalendarEvent(
                    connection_id=event.connection_id,
                    event_id=f"{event.event_id}_occurrence_{dt.isoformat()}",
                    summary=event.summary,
                    description=event.description,
                    location=event.location,
                    start_time=dt,
                    end_time=dt + event_duration,
                    is_all_day=event.is_all_day,
                    status=event.status,
                    source=event.source,
                    last_modified=event.last_modified
                )
                occurrences.append(occurrence)
            
            return occurrences if occurrences else [event]
            
        except Exception as e:
            print(f"Failed to expand recurring event {event.id}: {e}")
            return [event]  # Fall back to original event
    
    def _compute_free_slots(
        self,
        connection_id: int,
        busy_events: List[CalendarEvent],
        start_date: datetime,
        end_date: datetime,
        computed_at: datetime
    ) -> int:
        """Compute free slots as gaps between busy periods.
        
        Args:
            connection_id: Calendar connection ID
            busy_events: Sorted list of busy events
            start_date: Start of range
            end_date: End of range
            computed_at: Computation timestamp
        
        Returns:
            Number of free slots created
        """
        slots_created = 0
        current_time = start_date
        
        for event in busy_events:
            # Gap before this event
            if event.start_time > current_time:
                free_slot = AvailabilitySlot(
                    connection_id=connection_id,
                    start_time=current_time,
                    end_time=event.start_time,
                    status='free',
                    event_id=None,
                    event_summary=None,
                    computed_at=computed_at
                )
                self.session.add(free_slot)
                slots_created += 1
            
            # Move current time past this event
            current_time = max(current_time, event.end_time)
        
        # Final free slot after last event
        if end_date > current_time:
            free_slot = AvailabilitySlot(
                connection_id=connection_id,
                start_time=current_time,
                end_time=end_date,
                status='free',
                event_id=None,
                event_summary=None,
                computed_at=computed_at
            )
            self.session.add(free_slot)
            slots_created += 1
        
        return slots_created
    
    def _compute_free_slots_with_working_hours(
        self,
        connection_id: int,
        busy_events: List[CalendarEvent],
        start_date: datetime,
        end_date: datetime,
        working_hours: Tuple[int, int],
        computed_at: datetime
    ) -> int:
        """Compute free slots only within working hours.
        
        Args:
            connection_id: Calendar connection ID
            busy_events: Sorted list of busy events
            start_date: Start of range
            end_date: End of range
            working_hours: Tuple of (start_hour, end_hour) in 24h format
            computed_at: Computation timestamp
        
        Returns:
            Number of free slots created
        """
        slots_created = 0
        work_start_hour, work_end_hour = working_hours
        
        # Iterate through each day in range
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            # Define working hours for this day
            day_start = datetime.combine(current_date, datetime.min.time()).replace(
                hour=work_start_hour, tzinfo=timezone.utc
            )
            day_end = datetime.combine(current_date, datetime.min.time()).replace(
                hour=work_end_hour, tzinfo=timezone.utc
            )
            
            # Get events for this day
            day_events = [
                e for e in busy_events
                if e.start_time < day_end and e.end_time > day_start
            ]
            
            # Compute free slots within working hours
            current_time = day_start
            for event in day_events:
                event_start = max(event.start_time, day_start)
                event_end = min(event.end_time, day_end)
                
                # Gap before this event
                if event_start > current_time:
                    free_slot = AvailabilitySlot(
                        connection_id=connection_id,
                        start_time=current_time,
                        end_time=event_start,
                        status='free',
                        event_id=None,
                        event_summary=None,
                        computed_at=computed_at
                    )
                    self.session.add(free_slot)
                    slots_created += 1
                
                current_time = max(current_time, event_end)
            
            # Final free slot for the day
            if day_end > current_time:
                free_slot = AvailabilitySlot(
                    connection_id=connection_id,
                    start_time=current_time,
                    end_time=day_end,
                    status='free',
                    event_id=None,
                    event_summary=None,
                    computed_at=computed_at
                )
                self.session.add(free_slot)
                slots_created += 1
            
            # Move to next day
            current_date += timedelta(days=1)
        
        return slots_created
    
    def find_free_slots(
        self,
        connection_id: int,
        start_time: datetime,
        end_time: datetime,
        min_duration_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """Find available free time slots within a date range.
        
        Args:
            connection_id: Calendar connection ID
            start_time: Start of search range (UTC)
            end_time: End of search range (UTC)
            min_duration_minutes: Minimum slot duration in minutes
        
        Returns:
            List of dicts with 'start', 'end', 'duration_minutes' keys
        """
        free_slots = self.session.query(AvailabilitySlot).filter(
            AvailabilitySlot.connection_id == connection_id,
            AvailabilitySlot.status == 'free',
            AvailabilitySlot.start_time < end_time,
            AvailabilitySlot.end_time > start_time
        ).order_by(AvailabilitySlot.start_time).all()
        
        results = []
        for slot in free_slots:
            # Ensure datetimes are timezone-aware
            slot_start_time = slot.start_time
            slot_end_time = slot.end_time
            
            # Convert naive datetimes to timezone-aware (UTC)
            if slot_start_time.tzinfo is None:
                slot_start_time = slot_start_time.replace(tzinfo=timezone.utc)
            if slot_end_time.tzinfo is None:
                slot_end_time = slot_end_time.replace(tzinfo=timezone.utc)
            
            # Clip slot to search range
            slot_start = max(slot_start_time, start_time)
            slot_end = min(slot_end_time, end_time)
            
            duration_minutes = (slot_end - slot_start).total_seconds() / 60
            
            if duration_minutes >= min_duration_minutes:
                results.append({
                    'start': slot_start,
                    'end': slot_end,
                    'duration_minutes': duration_minutes
                })
        
        return results
    
    def is_time_available(
        self,
        connection_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Check if a specific time range is available (not busy).
        
        Args:
            connection_id: Calendar connection ID
            start_time: Start of time range to check (UTC)
            end_time: End of time range to check (UTC)
        
        Returns:
            True if time is fully available, False if any conflict exists
        """
        busy_slots = self.session.query(AvailabilitySlot).filter(
            AvailabilitySlot.connection_id == connection_id,
            AvailabilitySlot.status == 'busy',
            AvailabilitySlot.start_time < end_time,
            AvailabilitySlot.end_time > start_time
        ).count()
        
        return busy_slots == 0
    
    def get_busy_periods(
        self,
        connection_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get all busy periods within a time range.
        
        Args:
            connection_id: Calendar connection ID
            start_time: Start of range (UTC)
            end_time: End of range (UTC)
        
        Returns:
            List of dicts with 'start', 'end', 'event_summary' keys
        """
        busy_slots = self.session.query(AvailabilitySlot).filter(
            AvailabilitySlot.connection_id == connection_id,
            AvailabilitySlot.status == 'busy',
            AvailabilitySlot.start_time < end_time,
            AvailabilitySlot.end_time > start_time
        ).order_by(AvailabilitySlot.start_time).all()
        
        return [
            {
                'start': slot.start_time,
                'end': slot.end_time,
                'event_summary': slot.event_summary
            }
            for slot in busy_slots
        ]

# Story 4.1: Connect External Calendar for Bi-Directional Synchronization

Status: ready-for-dev

## Epic Context

**Epic 4: Intelligent Calendar & Proactive Scheduling**

Users can connect their existing calendars, have Sageframe intelligently identify free time, and proactively suggest social and professional engagements, reducing scheduling friction.

This epic covers:
- Connect external calendar for bi-directional synchronization (THIS STORY)
- Read calendar to identify free/busy times (Story 4.2)
- Create, update, and delete calendar events (Story 4.3)
- Proactively suggest engagements based on availability (Story 4.4)
- Time blocking with Google Calendar integration (Story 4.5)
- Intelligent scheduling lite (Story 4.6)

## Story

As a user,
I want to connect my external calendar (e.g., Google Calendar) for bi-directional synchronization, including the ability to push SageFrame events one-way to the external calendar,
so that Sageframe can have an accurate, up-to-date view of my schedule and help manage my time, and I can see all my SageFrame events in my external calendar.

## Acceptance Criteria

1. **Given** I am in the application's settings,  
   **When** I select the option to connect a new calendar,  
   **Then** I am guided through a secure OAuth 2.0 flow to authenticate with my chosen calendar provider (e.g., Google).

2. **Given** I have successfully authenticated my external calendar,  
   **When** the connection is established,  
   **Then** Sageframe performs an initial synchronization of my calendar events.

3. **Given** the calendar is connected,  
   **When** a new event is created or updated in Sageframe,  
   **Then** the change is reflected in my external calendar (one-way sync from Sageframe to external calendar, fulfilling FR35).

4. **Given** the calendar is connected,  
   **When** a new event is created or updated in my external calendar,  
   **Then** the change is reflected in Sageframe.

5. **Given** any synchronization issue occurs (as per NFR8),  
   **Then** the system handles the error gracefully, attempts to retry, and provides a clear prompt for manual intervention if necessary (NFR9).

## Business Value & Context

**Primary User Need:** Users need Sageframe to understand their full schedule without manual data entry, enabling intelligent AI suggestions and reducing double-booking.

**Why This Matters:**
- Foundation for all other Epic 4 features (free/busy detection, intelligent scheduling)
- Eliminates manual event duplication between Sageframe and external calendar
- Enables AI Co-Pilot to make context-aware suggestions based on real availability
- Supports "local-first" philosophy with cloud sync as user-controlled feature
- Critical for time blocking (Story 4.5) and proactive scheduling (Story 4.4)

**Related FRs:**
- FR20: Connect external calendar for bi-directional synchronization
- FR35: Sync events from SageFrame to Google Calendar (one-way)

## Tasks / Subtasks

- [ ] Implement OAuth 2.0 authentication flow (AC: #1)
  - [ ] Create Google Calendar OAuth client configuration
  - [ ] Implement authorization URL generation and redirect handling
  - [ ] Handle OAuth callback and token exchange
  - [ ] Store access/refresh tokens securely (keyring library per architecture)
  
- [ ] Build calendar sync service (AC: #2, #3, #4)
  - [ ] Create `CalendarSyncService` class
  - [ ] Implement initial calendar event fetch (pull from Google Calendar)
  - [ ] Implement push sync (Sageframe → Google Calendar)
  - [ ] Implement pull sync (Google Calendar → Sageframe)
  - [ ] Handle sync conflicts (last-write-wins strategy)
  
- [ ] Design calendar data model (AC: #2, #3, #4)
  - [ ] Create `calendar_connections` table (store OAuth tokens, connection status)
  - [ ] Create `calendar_events` table (store synced events)
  - [ ] Create `sync_log` table (track sync operations, errors)
  - [ ] Add migration using Alembic
  
- [ ] Implement sync scheduling and triggers (AC: #3, #4)
  - [ ] Create background sync worker (periodic sync every 5-15 minutes)
  - [ ] Implement event change detection (compare local vs. remote events)
  - [ ] Add manual sync trigger (user-initiated)
  - [ ] Implement webhook support for instant push notifications (optional/future)
  
- [ ] Build calendar settings UI (AC: #1)
  - [ ] Create calendar connection settings panel
  - [ ] Implement "Connect Google Calendar" button with OAuth flow
  - [ ] Show connection status (connected, syncing, error)
  - [ ] Add disconnect/remove calendar option
  
- [ ] Implement error handling and retry logic (AC: #5)
  - [ ] Implement exponential backoff for failed sync operations (NFR8)
  - [ ] Handle OAuth token refresh (when access token expires)
  - [ ] Detect and handle rate limit errors from Google Calendar API
  - [ ] Provide manual intervention prompts for persistent errors (NFR9)
  
- [ ] Testing and validation (AC: all)
  - [ ] Unit tests for OAuth flow
  - [ ] Integration tests for calendar sync service
  - [ ] Mock Google Calendar API for testing
  - [ ] Test error scenarios (network offline, token expired, rate limit)
  - [ ] Test conflict resolution (same event modified in both places)

## Dev Notes

### Architecture Compliance

**Authentication & Security (from architecture.md):**
- **OAuth 2.0 with User-Controlled Cloud Providers** (per architecture decision)
- **API Key Storage:** Windows Credential Manager via `keyring` library
- **Data Encryption:** HTTPS/TLS for data in transit
- **Privacy:** User controls their own OAuth tokens, no central backend

**Data Architecture:**
- SQLAlchemy ORM for all database interactions
- Pydantic models for Google Calendar API response validation
- Alembic for database migrations
- SQLite for local storage (local-first)

**API Integration Pattern:**
- User-provided OAuth credentials (privacy-preserving, no backend)
- Async API calls (don't block UI thread per NFR1/NFR2)
- Retry logic with exponential backoff (per NFR8)
- Manual intervention prompts for persistent failures (NFR9)

**Frontend Architecture:**
- MVVM pattern with PySide6
- Qt Signals & Slots for sync events (e.g., `syncCompleted`, `syncFailed`, `connectionEstablished`)
- Atomic Design for settings UI components

**Naming Conventions (CRITICAL):**
- Database: `snake_case` (tables: `calendar_connections`, columns: `access_token`, `refresh_token`)
- Python code: PEP 8 (functions: `sync_events()`, classes: `CalendarSyncService`)
- Signals: `verbNoun` camelCase (e.g., `syncCompleted`, `connectionEstablished`)

### Performance Requirements (NFR1, NFR2, NFR8, NFR9)

- **OAuth flow must not block UI** - Open browser in separate process
- **Initial sync must be async** - Show progress indicator, don't freeze app
- **Background sync every 5-15 minutes** - Configurable, non-intrusive
- **Retry logic:** Exponential backoff (1s, 2s, 4s, 8s) for failed operations
- **Token refresh must be transparent** - Auto-refresh access tokens when expired
- **Sync latency:** Target <30s for pulling/pushing changes

### Project Structure

Create new module for calendar integration:

```
src/modules/calendar_integration/
  ├── __init__.py
  ├── models.py                 # SQLAlchemy models for calendar data
  ├── services.py               # CalendarSyncService, OAuth service
  ├── oauth/
  │   ├── __init__.py
  │   ├── google_oauth.py       # Google OAuth 2.0 client
  │   ├── token_manager.py      # Secure token storage/refresh
  │   └── callback_handler.py   # OAuth callback handling
  ├── sync/
  │   ├── __init__.py
  │   ├── sync_engine.py        # Core sync logic
  │   ├── conflict_resolver.py  # Handle sync conflicts
  │   ├── workers.py            # Background sync workers
  │   └── schemas.py            # Pydantic models for API responses
  ├── views.py                  # PySide6 widgets for settings UI
  ├── signals.py                # Calendar-related signals
  └── tests/
      ├── test_oauth.py
      ├── test_sync_service.py
      ├── test_conflict_resolution.py
      └── test_token_manager.py
```

### Data Model Design

**`calendar_connections` table:**
```sql
id                  INTEGER PRIMARY KEY
provider            TEXT NOT NULL         -- 'google_calendar' (extensible for future providers)
connection_name     TEXT NOT NULL         -- User-friendly name (e.g., "Work Calendar")
access_token        TEXT NOT NULL         -- OAuth access token (encrypted via keyring)
refresh_token       TEXT NOT NULL         -- OAuth refresh token (encrypted via keyring)
token_expires_at    TEXT NOT NULL         -- ISO 8601 UTC
user_email          TEXT NOT NULL         -- Connected calendar email
calendar_id         TEXT NOT NULL         -- Google Calendar ID (e.g., "primary")
sync_enabled        INTEGER DEFAULT 1     -- Boolean: is sync active?
last_sync_at        TEXT                  -- ISO 8601 UTC (last successful sync)
sync_status         TEXT NOT NULL         -- 'connected', 'syncing', 'error', 'disconnected'
error_message       TEXT                  -- Last error details
created_at          TEXT NOT NULL
updated_at          TEXT NOT NULL

UNIQUE(provider, user_email, calendar_id)
```

**`calendar_events` table:**
```sql
id                  INTEGER PRIMARY KEY
connection_id       INTEGER NOT NULL      -- FK to calendar_connections.id
event_id            TEXT NOT NULL         -- Google Calendar Event ID
summary             TEXT NOT NULL         -- Event title
description         TEXT                  -- Event description
location            TEXT                  -- Event location
start_time          TEXT NOT NULL         -- ISO 8601 UTC
end_time            TEXT NOT NULL         -- ISO 8601 UTC
is_all_day          INTEGER DEFAULT 0     -- Boolean
recurrence_rule     TEXT                  -- RRULE for recurring events (RFC 5545)
attendees           TEXT                  -- JSON array of attendee emails
status              TEXT NOT NULL         -- 'confirmed', 'tentative', 'cancelled'
source              TEXT NOT NULL         -- 'sageframe' or 'external'
last_modified       TEXT NOT NULL         -- ISO 8601 UTC (event's last update time)
sync_version        INTEGER DEFAULT 1     -- Incrementing version for conflict detection
created_at          TEXT NOT NULL
updated_at          TEXT NOT NULL

UNIQUE(connection_id, event_id)
```

**`sync_log` table:**
```sql
id                  INTEGER PRIMARY KEY
connection_id       INTEGER NOT NULL      -- FK to calendar_connections.id
sync_direction      TEXT NOT NULL         -- 'push', 'pull', 'bidirectional'
sync_status         TEXT NOT NULL         -- 'success', 'partial_success', 'failed'
events_synced       INTEGER DEFAULT 0     -- Number of events successfully synced
events_failed       INTEGER DEFAULT 0     -- Number of events that failed
error_message       TEXT                  -- Error details if failed
sync_started_at     TEXT NOT NULL         -- ISO 8601 UTC
sync_completed_at   TEXT                  -- ISO 8601 UTC
created_at          TEXT NOT NULL
```

### Google Calendar OAuth 2.0 Implementation

**OAuth Flow:**

1. User clicks "Connect Google Calendar" button
2. App generates authorization URL with scopes
3. Open browser to Google consent screen (separate process - don't block UI)
4. User grants permissions
5. Google redirects to callback URL with authorization code
6. App exchanges code for access/refresh tokens
7. Store tokens securely in Windows Credential Manager via `keyring`
8. Save connection details in `calendar_connections` table

**Required OAuth Scopes:**
```python
GOOGLE_CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar",  # Full calendar access
    "https://www.googleapis.com/auth/calendar.events"  # Events read/write
]
```

**OAuth Client Setup:**

User must create Google Cloud Project and OAuth 2.0 credentials:
1. Go to Google Cloud Console
2. Create new project (or use existing)
3. Enable Google Calendar API
4. Create OAuth 2.0 Client ID (Desktop App)
5. Download client secrets JSON
6. Configure in Sageframe settings

**Implementation Example:**

```python
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import keyring

class GoogleOAuthService:
    def __init__(self, client_secrets_file: str):
        self.client_secrets_file = client_secrets_file
        self.scopes = [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events"
        ]
    
    def initiate_oauth_flow(self):
        """Start OAuth flow."""
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file,
            scopes=self.scopes
        )
        # Opens browser for user consent
        creds = flow.run_local_server(port=0)
        return creds
    
    def store_tokens(self, connection_id: int, creds):
        """Store tokens securely in keyring."""
        keyring.set_password(
            "sageframe_calendar",
            f"connection_{connection_id}_access",
            creds.token
        )
        keyring.set_password(
            "sageframe_calendar",
            f"connection_{connection_id}_refresh",
            creds.refresh_token
        )
    
    def refresh_access_token(self, connection_id: int):
        """Refresh expired access token."""
        refresh_token = keyring.get_password(
            "sageframe_calendar",
            f"connection_{connection_id}_refresh"
        )
        # Use Google's auth library to refresh
        creds.refresh(Request())
        # Store new access token
        self.store_tokens(connection_id, creds)
```

### Calendar Sync Logic

**Sync Strategies:**

1. **Initial Sync (Pull):** Fetch all events from Google Calendar for past 30 days and future 90 days
2. **Periodic Sync (Bidirectional):** Every 5-15 minutes, sync changes in both directions
3. **Push Sync (Sageframe → Google):** When user creates/updates event in Sageframe, immediately push to Google
4. **Pull Sync (Google → Sageframe):** Periodic check for changes in Google Calendar

**Conflict Resolution Strategy:**

Use "last-write-wins" approach:
- Compare `last_modified` timestamp from Google Calendar API with local `updated_at`
- If remote is newer, overwrite local (pull wins)
- If local is newer, overwrite remote (push wins)
- Log conflicts in `sync_log` for user review

**Change Detection:**

```python
def detect_changes(local_events: List[Event], remote_events: List[Event]):
    """Detect changes between local and remote events."""
    local_by_id = {e.event_id: e for e in local_events}
    remote_by_id = {e['id']: e for e in remote_events}
    
    # New remote events (not in local)
    new_from_remote = [e for e_id, e in remote_by_id.items() if e_id not in local_by_id]
    
    # Deleted remote events (in local but not remote)
    deleted_from_remote = [e for e_id, e in local_by_id.items() if e_id not in remote_by_id]
    
    # Modified events (compare last_modified timestamps)
    modified_events = []
    for e_id in set(local_by_id.keys()) & set(remote_by_id.keys()):
        local = local_by_id[e_id]
        remote = remote_by_id[e_id]
        if remote['updated'] > local.last_modified:
            modified_events.append(('remote_newer', remote))
        elif local.updated_at > remote['updated']:
            modified_events.append(('local_newer', local))
    
    return new_from_remote, deleted_from_remote, modified_events
```

### Google Calendar API Integration

**Library:** Use official `google-api-python-client` library

**Installation:**
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**API Methods:**

```python
from googleapiclient.discovery import build

def get_calendar_service(credentials):
    """Build Google Calendar API service."""
    return build('calendar', 'v3', credentials=credentials)

def fetch_events(service, calendar_id='primary', time_min=None, time_max=None):
    """Fetch events from Google Calendar."""
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,  # Expand recurring events
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

def create_event(service, calendar_id, event_data):
    """Create event in Google Calendar."""
    event = service.events().insert( calendarId=calendar_id,
        body=event_data
    ).execute()
    return event

def update_event(service, calendar_id, event_id, event_data):
    """Update event in Google Calendar."""
    event = service.events().update(
        calendarId=calendar_id,
        eventId=event_id,
        body=event_data
    ).execute()
    return event

def delete_event(service, calendar_id, event_id):
    """Delete event from Google Calendar."""
    service.events().delete(
        calendarId=calendar_id,
        eventId=event_id
    ).execute()
```

### Error Handling (NFR8, NFR9)

**Retry Logic:**

```python
import time

def sync_with_retry(sync_fn, max_retries=3):
    """Execute sync function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return sync_fn()
        except HttpError as e:
            if e.resp.status == 429:  # Rate limit
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            elif e.resp.status == 401:  # Token expired
                refresh_access_token()
                continue
            else:
                raise
    # Max retries exceeded
    raise SyncError("Failed after max retries")
```

**Error Scenarios:**

1. **OAuth Token Expired:** Auto-refresh using refresh token
2. **Rate Limit Exceeded (429):** Exponential backoff, retry
3. **Network Offline:** Queue sync for later, notify user
4. **Calendar Deleted:** Prompt user to reconnect or remove connection
5. **Permission Revoked:** Prompt user to re-authorize OAuth

**Manual Intervention (NFR9):**

If sync fails after retries, show user-friendly prompt:
- "Unable to sync calendar. Check your internet connection and try again."
- Provide "Retry Now" button
- Provide "Disconnect Calendar" button (if persistent issues)

### Security & Privacy

**Token Security:**
- Store OAuth tokens in Windows Credential Manager (not database)
- Never log tokens in debug logs or error messages
- Use HTTPS for all Google Calendar API calls
- Implement token rotation (refresh access tokens regularly)

**Privacy Considerations:**
- User owns OAuth credentials (not Sageframe)
- Calendar data stays local (SQLite database)
- No Sageframe backend intermediary for calendar sync
- User can disconnect calendar at any time (deletes local data)

**Data Isolation (NFR3):**
- Calendar data isolated per user (single-user MVP)
- SQLite database protected by OS-level permissions

### Testing Standards

**Unit Tests:**
- Test OAuth flow (mock Google OAuth endpoints)
- Test token refresh logic
- Test sync conflict resolution
- Test API request/response parsing (Pydantic validation)

**Integration Tests:**
- Test full sync cycle (pull → process → push)
- Use Google Calendar API test environment (sandbox)
- Test error scenarios (token expired, rate limit, network offline)

**Performance Tests:**
- Test initial sync performance (1000+ events)
- Test periodic sync latency (target <30s)
- Test UI responsiveness during sync (non-blocking)

### UI/UX Considerations

**Settings UI:**
- Clear "Connect Google Calendar" button
- Show connection status: "Connected to user@gmail.com"
- Show last sync time: "Last synced 5 minutes ago"
- Provide manual "Sync Now" button
- Show sync errors with actionable messages

**Sync Indicators:**
- Subtle sync icon in system tray or status bar
- Non-intrusive sync progress (don't interrupt user)
- Notifications only for errors (not every successful sync)

**Accessibility:**
- Keyboard navigation for settings panel
- Screen reader support for connection status
- High contrast for error messages

### Common LLM Mistakes to AVOID

- ❌ Don't store OAuth tokens in SQLite database - use keyring library
- ❌ Don't make synchronous API calls - always use async or background workers
- ❌ Don't block UI during OAuth flow - open browser in separate process
- ❌ Don't ignore token refresh - access tokens expire, implement refresh logic
- ❌ Don't forget conflict resolution - same event can be modified in both places
- ❌ Don't ignore rate limits - implement exponential backoff and retry logic
- ❌ Don't expose tokens in logs or error messages
- ❌ Don't forget to handle network offline scenarios gracefully
- ❌ Don't implement custom OAuth - use official Google libraries

### References

- [Source: architecture.md#Authentication & Security] - OAuth 2.0 with user-controlledproviders, keyring for API keys
- [Source: architecture.md#Data Architecture] - SQLAlchemy + Pydantic + Alembic
- [Source: architecture.md#Process Patterns] - Global error handling, retry logic (NFR8/NFR9)
- [Source: epics.md#Epic 4] - Full epic context
- [Source: epics.md#Story 4.1 Acceptance Criteria] - Original acceptance criteria
- [Source: epics.md#NFR8, NFR9] - Integration failure handling and retry logic

### Future Enhancements (Post-MVP)

- Support multiple calendar connections (work + personal)
- Support other calendar providers (Outlook, iCloud, CalDAV)
- Implement webhook support for instant notifications
- Add selective sync (only sync specific calendars)
- Implement calendar sharing and collaboration features
- Add sync analytics dashboard (sync history, conflict resolution stats)

## Dev Agent Record

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent during implementation_

### Completion Notes List

_To be filled by dev agent with implementation learnings_

### File List

_To be filled by dev agent with all files created/modified_

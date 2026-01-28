# Story 5.1: Implement Local-First Data Storage as Default

Status: ready-for-dev

## Epic Context

**Epic 5: Secure Data Management & Portability**

Users have control over their personal data, knowing it's stored locally by default, ensuring privacy.

This epic focuses on data sovereignty, privacy, and local-first architecture as a core principle.

## Story

As a user,
I want my data to be stored on my local device by default,
so that I have complete control over my information and can ensure my privacy.

## Acceptance Criteria

1. **Given** I am using the application, **When** any data is created or modified (e.g., tasks, notes, projects), **Then** this data is written to a local database (SQLite as per Architecture) on my device.

2. **Given** the application is running without an internet connection, **Then** all core functionalities that rely on my data (e.g., viewing tasks, creating notes) remain fully operational.

3. **Given** my data is stored locally, **Then** the application adheres to standard operating system security measures to protect the data from unauthorized access (as per NFR3).

4. **Given** I am using the application, **Then** the local data storage is efficient and does not negatively impact application performance (NFR1, NFR2).

## Business Value & Context

**Primary User Need:** Users want data privacy and control without relying on cloud services or third-party backends.

**Why This Matters:**
- Core architectural principle: local-first, privacy-preserving
- Enables offline functionality (no internet required for core features)
- User owns their data (not stored on external servers)
- Foundation for future data portability features
- Aligns with NFR3 (data privacy and security)

**Related FRs:**
- FR24: Local-first data storage as default

## Tasks / Subtasks

- [ ] Implement SQLite database setup (AC: #1)
  - [ ] Create database initialization service
  - [ ] Define database schema for all entities (tasks, notes, projects, tags, etc.)
  - [ ] Implement Alembic for database migrations
  - [ ] Set database file location (`AppData\Local\SageFrame\sageframe.db` on Windows)
  
- [ ] Implement data access layer (AC: #1)
  - [ ] Create SQLAlchemy ORM models for all entities
  - [ ] Implement repository pattern (or service layer) for CRUD operations
  - [ ] Ensure all data writes go to local SQLite database
  - [ ] Implement transaction management for data consistency
  
- [ ] Implement offline functionality (AC: #2)
  - [ ] Ensure no network calls required for core features
  - [ ] Handle graceful degradation when internet unavailable (e.g., skip sync, show cached data)
  - [ ] Add offline status indicator in UI
  
- [ ] Implement database security (AC: #3)
  - [ ] Set restrictive file permissions on database file (Windows: owner read/write only)
  - [ ] Use OS-level encryption for database file (Windows: BitLocker, EFS support)
  - [ ] Validate SQL queries to prevent injection attacks
  
- [ ] Performance optimization (AC: #4)
  - [ ] Add database indexes for frequently queried fields
  - [ ] Implement connection pooling
  - [ ] Use lazy loading for large datasets
  - [ ] Benchmark query performance (target <50ms for simple queries)
  
- [ ] Testing (AC: all)
  - [ ] Unit tests for CRUD operations
  - [ ] Integration tests for database transactions
  - [ ] Test offline functionality (network disabled)
  - [ ] Test database security (file permissions, access control)
  - [ ] Performance tests (large datasets, concurrent access)

## Dev Notes

### Architecture Compliance

**Data Architecture (from architecture.md):**
- **Local-First:** SQLite as primary data store, no backend required
- **SQLAlchemy ORM:** All database interactions use SQLAlchemy
- **Alembic:** Database migrations for schema changes
- **Pydantic:** Data validation at service layer

**Database Location:**
- Windows: `%LOCALAPPDATA%\SageFrame\sageframe.db`
- Path: `C:\Users\<username>\AppData\Local\SageFrame\sageframe.db`

**Security (NFR3):**
- File permissions: Owner read/write only
- OS-level encryption: Support BitLocker, Windows EFS
- No plaintext sensitive data in database (use encryption for API keys via `keyring`)

**Performance (NFR1, NFR2):**
- Query execution <50ms for simple queries
- UI remains responsive during database operations
- Use async database operations where possible (SQLAlchemy async support)

### Project Structure

```
src/
  ├── database/
  │   ├── __init__.py
  │   ├── connection.py        # Database connection and session management
  │   ├── models.py             # SQLAlchemy ORM models (all entities)
  │   ├── repositories.py       # Repository pattern for data access
  │   ├── migrations/           # Alembic migrations
  │   │   ├── alembic.ini
  │   │   ├── env.py
  │   │   └── versions/
  │   └── tests/
  │       ├── test_models.py
  │       ├── test_repositories.py
  │       └── test_migrations.py
```

### Database Schema (Consolidated)

All entities from previous epics should be in the database:

**Tasks (Epic 2):**
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,  -- 'pending', 'in_progress', 'completed'
    priority TEXT,          -- 'low', 'medium', 'high', 'critical'
    due_date TEXT,
    project_id INTEGER,     -- FK to projects.id
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**Projects (Epic 2):**
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**Tags (Epic 3):**
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    tag_name TEXT NOT NULL UNIQUE,
    category TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE tagged_items (
    id INTEGER PRIMARY KEY,
    tag_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    content TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(tag_id, item_id)
);
```

**Calendar (Epic 4):**
```sql
CREATE TABLE calendar_connections (
    id INTEGER PRIMARY KEY,
    provider TEXT NOT NULL,
    connection_name TEXT NOT NULL,
    user_email TEXT NOT NULL,
    calendar_id TEXT NOT NULL,
    sync_enabled INTEGER DEFAULT 1,
    last_sync_at TEXT,
    sync_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE calendar_events (
    id INTEGER PRIMARY KEY,
    connection_id INTEGER NOT NULL,
    event_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**Habits (Epic 7):**
```sql
CREATE TABLE habits (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE habit_completions (
    id INTEGER PRIMARY KEY,
    habit_id INTEGER NOT NULL,
    completion_date TEXT NOT NULL,  -- ISO 8601 date (YYYY-MM-DD)
    created_at TEXT NOT NULL,
    UNIQUE(habit_id, completion_date)
);
```

### Database Connection Management

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

class DatabaseService:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default: %LOCALAPPDATA%\SageFrame\sageframe.db
            db_path = os.path.join(
                os.getenv('LOCALAPPDATA'),
                'SageFrame',
                'sageframe.db'
            )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Set restrictive file permissions (Windows)
        self._set_secure_permissions(db_path)
        
        # Create SQLAlchemy engine
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _set_secure_permissions(self, db_path: str):
        """Set restrictive file permissions on Windows."""
        if os.path.exists(db_path):
            import win32security
            import ntsecuritycon as con
            
            # Get current user SID
            user = win32security.GetTokenInformation(
                win32security.OpenProcessToken(
                    win32api.GetCurrentProcess(),
                    con.TOKEN_QUERY
                ),
                win32security.TokenUser
            )
            
            # Set ACL: Owner full control only
            sd = win32security.SECURITY_DESCRIPTOR()
            dacl = win32security.ACL()
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_ALL_ACCESS,
                user[0]
            )
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                db_path,
                win32security.DACL_SECURITY_INFORMATION,
                sd
            )
    
    @contextmanager
    def get_session(self) -> Session:
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
```

### Offline Functionality

**Design Principle:** All core features work offline. Only external integrations (calendar sync, AI enrichment) require internet.

**Offline Mode Handling:**
```python
def is_online() -> bool:
    """Check if internet connection is available."""
    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

# In calendar sync service
if is_online():
    sync_calendar()
else:
    logger.info("Offline - skipping calendar sync")
    show_offline_indicator()
```

### Performance Optimization

**Required Indexes:**
```sql
-- Task queries
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);

-- Tag queries
CREATE INDEX idx_tags_tag_name ON tags(tag_name);
CREATE INDEX idx_tagged_items_tag_id ON tagged_items(tag_id);
CREATE INDEX idx_tagged_items_item_id ON tagged_items(item_id);

-- Calendar queries
CREATE INDEX idx_calendar_events_start_time ON calendar_events(start_time);
CREATE INDEX idx_calendar_events_connection_id ON calendar_events(connection_id);
```

**Query Optimization:**
- Use `select_related()` / `joinedload()` for eager loading
- Implement pagination for large datasets (100 items per page)
- Cache frequently accessed data (e.g., user preferences)

### Common LLM Mistakes to AVOID

- ❌ Don't use cloud database - always SQLite local file
- ❌ Don't require internet for core features - offline-first architecture
- ❌ Don't forget database migrations - use Alembic for schema changes
- ❌ Don't ignore file permissions - secure database file properly
- ❌ Don't forget indexes - query performance is critical
- ❌ Don't use raw SQL - always use SQLAlchemy ORM
- ❌ Don't forget transaction management - use sessions properly

### References

- [Source: architecture.md#Data Architecture] - SQLite, SQLAlchemy, Alembic
- [Source: architecture.md#Security Architecture] - NFR3 data privacy requirements
- [Source: epics.md#Story 5.1 Acceptance Criteria]
- [Source: epics.md#NFR1, NFR2] - Performance requirements

## Dev Agent Record

### Agent Model Used
_To be filled by dev agent_

### Completion Notes List
_To be filled by dev agent_

### File List
_To be filled by dev agent_

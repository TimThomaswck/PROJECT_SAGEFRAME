"""Database configuration and session management.

This module provides SQLAlchemy database configuration and session management
for the Sageframe desktop application. Implements local-first data storage with
security features and offline support.
"""

import os
import stat
import socket
import logging
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# Get application data directory (configurable via environment variable)
db_path_env = os.getenv("SAGEFRAME_DB_PATH")
if db_path_env:
    DATABASE_PATH = Path(db_path_env)
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
else:
    APP_DATA_DIR = Path.home() / ".sageframe"
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH = APP_DATA_DIR / "sageframe.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging during development
    connect_args={"check_same_thread": False}  # SQLite specific
)

# Create session factory
SessionLocal = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))

# Base class for declarative models
Base = declarative_base()


def get_db():
    """Get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database schema.
    
    Creates all tables defined in the models. Implements local-first data storage
    with security hardening for AC1, AC3, and AC4 from Story 5.1.
    """
    # Import all models here to ensure they're registered
    from app.modules.mood_checkin.models import MoodCheckIn
    from app.modules.ai_copilot.models import UserContext, CommunicationEvent
    from app.modules.projects.models import Project
    from app.modules.tasks.models import Task
    from app.modules.tag_management.models import Tag, TaggedItem, TagEnrichment
    from app.modules.file_ingestion.models import ImportedFile, ExtractionResult
    from app.modules.gamification.models import UserProgress
    from app.modules.calendar_integration.models import CalendarConnection, CalendarEvent, SyncLog, AvailabilitySlot
    from app.modules.notes.models import Note, note_links
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Apply security hardening to database file (AC3 - NFR3 compliance)
    _set_database_security()
    
    logger.info(f"Database initialized at: {DATABASE_PATH}")


def _set_database_security():
    """Apply security hardening to database file.
    
    Implements AC3 (database security) and NFR3 (data privacy):
    - Sets restrictive file permissions (owner read/write only)
    - Validates database file exists
    
    This ensures the database file can only be accessed by the current user.
    """
    if not DATABASE_PATH.exists():
        return
    
    try:
        # Set restrictive permissions on Windows
        # stat.S_IRUSR (user read) | stat.S_IWUSR (user write)
        # Remove all other permissions
        os.chmod(DATABASE_PATH, stat.S_IRUSR | stat.S_IWUSR)
        logger.debug(f"Database file permissions secured: {DATABASE_PATH}")
    except Exception as e:
        logger.warning(f"Could not set database file permissions: {e}")


def is_online() -> bool:
    """Check if internet connection is available.
    
    Implements AC2 (offline functionality) - checks for network connectivity.
    Returns True if the system can reach 8.8.8.8:53 (Google DNS).
    
    Returns:
        bool: True if internet is available, False otherwise
    """
    try:
        # Try to reach Google DNS (public, reliable)
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except (OSError, socket.timeout):
        return False


def get_offline_status() -> dict:
    """Get current offline status information.
    
    Implements AC2 (offline functionality detection) - provides UI with
    current connection status.
    
    Returns:
        dict: Dictionary with keys:
            - 'is_online': bool indicating network status
            - 'database_available': bool indicating database access
            - 'message': str with status message for UI
    """
    online = is_online()
    db_available = DATABASE_PATH.exists()
    
    if online:
        status_msg = "Online - Full features available"
    elif db_available:
        status_msg = "Offline - Local data available"
    else:
        status_msg = "Offline - No data available"
    
    return {
        'is_online': online,
        'database_available': db_available,
        'message': status_msg
    }

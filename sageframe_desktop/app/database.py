"""Database configuration and session management.

This module provides SQLAlchemy database configuration and session management
for the Sageframe desktop application.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

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
    
    Creates all tables defined in the models.
    """
    # Import all models here to ensure they're registered
    from app.modules.mood_checkin.models import MoodCheckIn
    from app.modules.ai_copilot.models import UserContext, CommunicationEvent
    
    Base.metadata.create_all(bind=engine)

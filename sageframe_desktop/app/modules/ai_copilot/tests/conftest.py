"""
Pytest Configuration and Fixtures for AI Co-Pilot Tests

Provides shared fixtures for database mocking, Qt testing, and service initialization.
"""

import pytest
from unittest.mock import MagicMock, create_autospec
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.modules.ai_copilot.models import Base, UserContext, CommunicationEvent


@pytest.fixture
def mock_db_session():
    """
    Provide a real in-memory SQLite session for testing.
    
    Uses a real SQLAlchemy session with in-memory database,
    allowing tests to validate actual database operations without file I/O.
    """
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)

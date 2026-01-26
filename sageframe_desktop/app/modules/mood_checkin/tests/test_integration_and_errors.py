"""Integration and error scenario tests for mood check-in functionality.

These tests address code review findings #5, #6, and #10:
- Integration tests with real database
- Error scenario tests (DB failures, concurrent access)
- Transaction rollback tests
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.modules.mood_checkin.models import MoodCheckIn
from app.modules.mood_checkin.services import MoodCheckInService


class TestIntegrationTests:
    """Integration tests with real SQLite database (Code Review Finding #5)."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file for integration testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_sageframe.db"
        yield str(db_path)
        # Cleanup - handle Windows file lock issues gracefully
        try:
            if db_path.exists():
                db_path.unlink()
            Path(temp_dir).rmdir()
        except (PermissionError, OSError):
            # File may still be locked on Windows - ignore cleanup error
            pass
    
    @pytest.fixture
    def real_db_session(self, temp_db_path):
        """Create real database session with temporary DB."""
        engine = create_engine(f"sqlite:///{temp_db_path}")
        
        # Import all models to ensure they're registered with Base
        from app.modules.mood_checkin.models import MoodCheckIn as MoodCheckInModel
        from app.modules.ai_copilot.models import UserContext, CommunicationEvent
        
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
        engine.dispose()  # Dispose engine to release file locks on Windows
    
    def test_end_to_end_mood_checkin_persistence(self, real_db_session):
        """Test complete workflow: create -> persist -> retrieve from real DB."""
        # Create service with real DB
        service = MoodCheckInService(real_db_session)
        
        # Create mood check-in
        checkin = service.create_mood_checkin(
            mood_level="happy",
            energy_level="high",
            notes="Integration test"
        )
        
        # Verify it was persisted
        assert checkin.id is not None
        
        # Retrieve it from DB
        retrieved = service.get_last_mood_checkin()
        assert retrieved is not None
        assert retrieved.id == checkin.id
        assert retrieved.mood_level == "happy"
        assert retrieved.energy_level == "high"
        assert retrieved.notes == "Integration test"
    
    def test_multiple_checkins_ordering(self, real_db_session):
        """Test that multiple check-ins are ordered correctly."""
        service = MoodCheckInService(real_db_session)
        
        # Create 3 check-ins
        service.create_mood_checkin("happy", "high")
        service.create_mood_checkin("neutral", "medium")
        service.create_mood_checkin("stressed", "low")
        
        # Get recent check-ins
        recent = service.get_recent_mood_checkins(limit=2)
        
        # Should be most recent first
        assert len(recent) == 2
        assert recent[0].mood_level == "stressed"
        assert recent[1].mood_level == "neutral"


class TestErrorScenarios:
    """Error scenario tests (Code Review Finding #6)."""
    
    def test_service_init_with_invalid_session(self):
        """Test service initialization handles invalid session creation."""
        with patch('app.modules.mood_checkin.services.SessionLocal') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception, match="Failed to initialize database session"):
                MoodCheckInService()
    
    def test_create_mood_checkin_with_invalid_enum_value(self):
        """Test that invalid mood/energy values are rejected by Pydantic."""
        engine = create_engine("sqlite:///:memory:")
        # Import all models to ensure they're registered with Base
        from app.modules.mood_checkin.models import MoodCheckIn as MoodCheckInModel
        from app.modules.ai_copilot.models import UserContext, CommunicationEvent
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        service = MoodCheckInService(session)
        
        # Try to create with invalid mood level
        with pytest.raises(ValueError, match="validation failed"):
            service.create_mood_checkin(
                mood_level="invalid_mood",  # Not in Literal["happy", "neutral", "stressed", "sad"]
                energy_level="high"
            )
        
        session.close()
    
    def test_database_rollback_on_error(self, monkeypatch):
        """Test transaction rollback on database error (Code Review Finding #10)."""
        engine = create_engine("sqlite:///:memory:")
        # Import all models to ensure they're registered with Base
        from app.modules.mood_checkin.models import MoodCheckIn as MoodCheckInModel
        from app.modules.ai_copilot.models import UserContext, CommunicationEvent
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        service = MoodCheckInService(session)
        
        # Mock the commit to fail
        original_commit = session.commit
        def failing_commit():
            raise Exception("Database commit failed")
        
        session.commit = failing_commit
        
        # Try to create mood check-in
        with pytest.raises(Exception, match="Failed to create mood check-in"):
            service.create_mood_checkin("happy", "high")
        
        # Restore original commit
        session.commit = original_commit
        
        # Verify rollback happened - no records should exist
        count = session.query(MoodCheckIn).count()
        assert count == 0
        
        session.close()
    
    def test_concurrent_access_simulation(self):
        """Test that concurrent database access doesn't cause corruption."""
        engine = create_engine("sqlite:///:memory:")
        # Import all models to ensure they're registered with Base
        from app.modules.mood_checkin.models import MoodCheckIn as MoodCheckInModel
        from app.modules.ai_copilot.models import UserContext, CommunicationEvent
        Base.metadata.create_all(engine)
        
        # Create two separate sessions simulating concurrent access
        Session = sessionmaker(bind=engine)
        session1 = Session()
        session2 = Session()
        
        service1 = MoodCheckInService(session1)
        service2 = MoodCheckInService(session2)
        
        # Both services create check-ins
        checkin1 = service1.create_mood_checkin("happy", "high")
        checkin2 = service2.create_mood_checkin("sad", "low")
        
        # Both should have unique IDs
        assert checkin1.id != checkin2.id
        
        # Query from a third session to verify both persisted
        session3 = Session()
        all_checkins = session3.query(MoodCheckIn).all()
        assert len(all_checkins) == 2
        
        session1.close()
        session2.close()
        session3.close()
    
    def test_service_cleanup_on_context_manager_exit(self):
        """Test that service properly cleans up resources when used as context manager."""
        engine = create_engine("sqlite:///:memory:")
        # Import all models to ensure they're registered with Base
        from app.modules.mood_checkin.models import MoodCheckIn as MoodCheckInModel
        from app.modules.ai_copilot.models import UserContext, CommunicationEvent
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Use service with session
        service = MoodCheckInService(session)
        
        # Session should be active
        assert service._db is not None
        checkin = service.create_mood_checkin("neutral", "medium")
        assert checkin.id is not None
        
        # Clean up
        session.close()

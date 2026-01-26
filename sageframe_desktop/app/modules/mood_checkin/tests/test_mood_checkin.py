"""Tests for mood check-in functionality.

Comprehensive test suite covering models, services, viewmodels, and views.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from PySide6.QtCore import Qt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.modules.mood_checkin.models import MoodCheckIn, MoodCheckInSchema
from app.modules.mood_checkin.services import MoodCheckInService


class TestMoodCheckInModels:
    """Test suite for mood check-in data models."""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        
        # Import all models to ensure they're registered with Base
        from app.modules.mood_checkin.models import MoodCheckIn as MoodCheckInModel
        from app.modules.ai_copilot.models import UserContext, CommunicationEvent
        
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_mood_checkin_model_creation(self, db_session):
        """Test creating a MoodCheckIn model instance."""
        mood_checkin = MoodCheckIn(
            mood_level="happy",
            energy_level="high",
            notes="Feeling great today!",
            timestamp=datetime.utcnow()
        )
        
        db_session.add(mood_checkin)
        db_session.commit()
        
        assert mood_checkin.id is not None
        assert mood_checkin.mood_level == "happy"
        assert mood_checkin.energy_level == "high"
        assert mood_checkin.notes == "Feeling great today!"
    
    def test_mood_checkin_schema_validation_success(self):
        """Test Pydantic schema validation with valid data."""
        data = {
            "mood_level": "neutral",
            "energy_level": "medium",
            "notes": "Just okay"
        }
        
        schema = MoodCheckInSchema(**data)
        
        assert schema.mood_level == "neutral"
        assert schema.energy_level == "medium"
        assert schema.notes == "Just okay"
    
    def test_mood_checkin_schema_validation_empty_mood(self):
        """Test Pydantic schema rejects empty mood level."""
        with pytest.raises(ValueError):
            MoodCheckInSchema(
                mood_level="",
                energy_level="low"
            )
    
    def test_mood_checkin_schema_validation_whitespace_energy(self):
        """Test Pydantic schema strips and validates energy level."""
        with pytest.raises(ValueError):
            MoodCheckInSchema(
                mood_level="sad",
                energy_level="   "
            )


class TestMoodCheckInService:
    """Test suite for mood check-in service layer."""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        
        # Import all models to ensure they're registered with Base
        from app.modules.mood_checkin.models import MoodCheckIn as MoodCheckInModel
        from app.modules.ai_copilot.models import UserContext, CommunicationEvent
        
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    @pytest.fixture
    def service(self, db_session):
        """Create service instance with test database session."""
        return MoodCheckInService(db_session)
    
    def test_create_mood_checkin_success(self, service, db_session):
        """Test creating a mood check-in via service."""
        mood_checkin = service.create_mood_checkin(
            mood_level="happy",
            energy_level="high",
            notes="Test note"
        )
        
        assert mood_checkin.id is not None
        assert mood_checkin.mood_level == "happy"
        assert mood_checkin.energy_level == "high"
        assert mood_checkin.notes == "Test note"
        
        # Verify it's in database
        result = db_session.query(MoodCheckIn).first()
        assert result is not None
        assert result.mood_level == "happy"
    
    def test_create_mood_checkin_validation_error(self, service):
        """Test service handles validation errors."""
        with pytest.raises(ValueError, match="validation failed"):
            service.create_mood_checkin(
                mood_level="",  # Empty mood should fail validation
                energy_level="low"
            )
    
    def test_get_recent_mood_checkins(self, service):
        """Test retrieving recent mood check-ins."""
        # Create multiple check-ins with valid moods
        moods = ["happy", "neutral", "stressed", "sad", "happy"]
        energies = ["high", "medium", "low", "high", "medium"]
        
        for mood, energy in zip(moods, energies):
            service.create_mood_checkin(
                mood_level=mood,
                energy_level=energy
            )
        
        recent = service.get_recent_mood_checkins(limit=3)
        
        assert len(recent) == 3
        # Should be in reverse chronological order (most recent first)
        assert recent[0].mood_level == "happy"
        assert recent[1].mood_level == "sad"
        assert recent[2].mood_level == "stressed"
    
    def test_get_last_mood_checkin(self, service):
        """Test getting the most recent mood check-in."""
        # Create check-ins with valid moods
        service.create_mood_checkin(mood_level="happy", energy_level="high")
        service.create_mood_checkin(mood_level="neutral", energy_level="medium")
        service.create_mood_checkin(mood_level="stressed", energy_level="low")
        
        last = service.get_last_mood_checkin()
        
        assert last is not None
        assert last.mood_level == "stressed"
    
    def test_get_last_mood_checkin_empty(self, service):
        """Test getting last check-in when none exist."""
        last = service.get_last_mood_checkin()
        assert last is None


class TestMoodCheckInViewModel:
    """Test suite for mood check-in ViewModel."""
    
    @pytest.fixture
    def view_model(self):
        """Create ViewModel instance for testing."""
        from app.modules.mood_checkin.view_models import MoodCheckInViewModel
        vm = MoodCheckInViewModel()
        yield vm
        vm.cleanup()
    
    def test_viewmodel_properties(self, view_model):
        """Test ViewModel property getters/setters."""
        view_model.moodLevel = "happy"
        view_model.energyLevel = "high"
        view_model.notes = "Test notes"
        
        assert view_model.moodLevel == "happy"
        assert view_model.energyLevel == "high"
        assert view_model.notes == "Test notes"
    
    @patch('app.modules.mood_checkin.view_models.MoodCheckInService')
    def test_submit_checkin_success(self, mock_service_class, view_model):
        """Test successful mood check-in submission."""
        # Setup mock
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Recreate ViewModel with mocked service
        from app.modules.mood_checkin.view_models import MoodCheckInViewModel
        vm = MoodCheckInViewModel()
        vm._service = mock_service
        
        # Set data
        vm.moodLevel = "neutral"
        vm.energyLevel = "medium"
        
        # Connect signal spy
        success_spy = Mock()
        vm.moodCheckInCompleted.connect(success_spy)
        
        # Submit
        vm.submit_checkin()
        
        # Verify service was called
        mock_service.create_mood_checkin.assert_called_once()
        
        # Verify signal emitted
        success_spy.assert_called_once()
        args = success_spy.call_args[0]
        assert args[0] is True  # success=True
    
    def test_submit_checkin_validation_error(self, view_model):
        """Test submission with missing required fields."""
        # Don't set mood/energy
        error_spy = Mock()
        view_model.validationError.connect(error_spy)
        
        view_model.submit_checkin()
        
        # Should emit validation error
        error_spy.assert_called_once()


class TestMoodCheckInDialog:
    """Test suite for mood check-in dialog UI."""
    
    @pytest.fixture
    def dialog(self, qtbot):
        """Create dialog instance for testing."""
        from app.modules.mood_checkin.views import MoodCheckInDialog
        dlg = MoodCheckInDialog()
        qtbot.addWidget(dlg)
        return dlg
    
    def test_dialog_creation(self, dialog):
        """Test dialog can be created."""
        assert dialog.windowTitle() == "Mood Check-in"
        assert dialog.isModal() is True
    
    def test_dialog_ui_elements_exist(self, dialog):
        """Test all expected UI elements are present."""
        assert dialog.mood_button_group is not None
        assert dialog.energy_button_group is not None
        assert dialog.notes_edit is not None
        assert dialog.submit_button is not None
        assert dialog.cancel_button is not None
    
    def test_dialog_submit_with_selection(self, dialog, qtbot):
        """Test submitting dialog with valid selections."""
        # Select first mood button
        mood_buttons = dialog.mood_button_group.buttons()
        assert len(mood_buttons) > 0
        mood_buttons[0].setChecked(True)
        
        # Select first energy button
        energy_buttons = dialog.energy_button_group.buttons()
        assert len(energy_buttons) > 0
        energy_buttons[0].setChecked(True)
        
        # Click submit button (should not crash)
        qtbot.mouseClick(dialog.submit_button, Qt.MouseButton.LeftButton)

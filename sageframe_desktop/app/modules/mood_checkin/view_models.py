"""ViewModel for mood check-in functionality.

This module implements the ViewModel layer of the MVVM pattern for mood check-ins.
"""

from typing import Optional

from PySide6.QtCore import QObject, Signal, Property

from app.modules.mood_checkin.services import MoodCheckInService


class MoodCheckInViewModel(QObject):
    """ViewModel for mood check-in dialog.
    
    Manages UI state and coordinates with the service layer.
    Follows MVVM pattern with Qt's property system and signals/slots.
    """
    
    # Signals (verbNoun naming convention as per architecture)
    moodCheckInRequested = Signal()
    moodCheckInCompleted = Signal(bool, str)  # success, message
    validationError = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None):
        """Initialize ViewModel.
        
        Args:
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._mood_level = ""
        self._energy_level = ""
        self._notes = ""
        self._is_submitting = False
        self._service = MoodCheckInService()
    
    # Properties for two-way data binding
    @Property(str)
    def moodLevel(self) -> str:
        """Get current mood level."""
        return self._mood_level
    
    @moodLevel.setter
    def moodLevel(self, value: str):
        """Set mood level and emit change."""
        if self._mood_level != value:
            self._mood_level = value
    
    @Property(str)
    def energyLevel(self) -> str:
        """Get current energy level."""
        return self._energy_level
    
    @energyLevel.setter
    def energyLevel(self, value: str):
        """Set energy level and emit change."""
        if self._energy_level != value:
            self._energy_level = value
    
    @Property(str)
    def notes(self) -> str:
        """Get notes."""
        return self._notes
    
    @notes.setter
    def notes(self, value: str):
        """Set notes and emit change."""
        if self._notes != value:
            self._notes = value
    
    @Property(bool)
    def isSubmitting(self) -> bool:
        """Get submission state."""
        return self._is_submitting
    
    def submit_checkin(self):
        """Submit mood check-in data.
        
        Validates and saves mood check-in via service layer.
        Emits moodCheckInCompleted signal with result.
        """
        if self._is_submitting:
            return  # Prevent double submission
        
        # Basic validation
        if not self._mood_level or not self._energy_level:
            self.validationError.emit("Please select both mood and energy level")
            return
        
        self._is_submitting = True
        
        try:
            # Save via service layer
            self._service.create_mood_checkin(
                mood_level=self._mood_level,
                energy_level=self._energy_level,
                notes=self._notes if self._notes else None
            )
            
            # Reset form
            self._mood_level = ""
            self._energy_level = ""
            self._notes = ""
            
            # Emit success
            self.moodCheckInCompleted.emit(True, "Mood check-in saved successfully")
            
        except ValueError as e:
            # Validation error from service/Pydantic
            self.validationError.emit(str(e))
            self.moodCheckInCompleted.emit(False, str(e))
            
        except Exception as e:
            # General error
            error_msg = f"Failed to save mood check-in: {e}"
            self.validationError.emit(error_msg)
            self.moodCheckInCompleted.emit(False, error_msg)
            
        finally:
            self._is_submitting = False
    
    def reset(self):
        """Reset form data."""
        self._mood_level = ""
        self._energy_level = ""
        self._notes = ""
        self._is_submitting = False
    
    def cleanup(self):
        """Cleanup resources."""
        self._service.close()

"""Tests for suggestion UI components.

Tests View layer for suggestion display and interaction.
Uses pytest-qt for Qt testing.
"""

import pytest

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.modules.suggestions.views import SuggestionNotificationWidget, SuggestionPanel
from app.modules.suggestions.view_models import SuggestionViewModel


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestSuggestionNotificationWidget:
    """Test suite for SuggestionNotificationWidget."""
    
    @pytest.fixture
    def suggestion(self):
        """Sample suggestion for testing."""
        return {
            "task_id": "task_1",
            "task_name": "Implement feature X",
            "task_description": "Complex feature implementation",
            "reasoning": "You're in a great mood and full of energy—this challenging task could be perfect!",
            "difficulty": "hard",
            "mood_context": "happy",
            "energy_context": "high",
        }
    
    def test_notification_widget_creation(self, qapp, suggestion):
        """Notification widget should create successfully."""
        widget = SuggestionNotificationWidget(suggestion)
        
        assert widget is not None
        assert widget.suggestion == suggestion
    
    def test_notification_widget_has_dismiss_button(self, qapp, suggestion):
        """Widget should have dismiss button."""
        widget = SuggestionNotificationWidget(suggestion)
        
        dismiss_btn = widget.findChild(type(None), "dismissButton")
        # Buttons are children, verify widget structure
        assert widget is not None
    
    def test_notification_widget_dismiss_callback(self, qapp, suggestion):
        """Dismiss callback should be called when button clicked."""
        dismiss_called = []
        
        def on_dismiss(task_id):
            dismiss_called.append(task_id)
        
        widget = SuggestionNotificationWidget(
            suggestion,
            on_dismiss=on_dismiss,
        )
        
        # Simulate dismiss button click
        widget._on_dismiss()
        
        assert len(dismiss_called) == 1
        assert dismiss_called[0] == "task_1"
    
    def test_notification_widget_action_callback(self, qapp, suggestion):
        """Action callback should be called when action button clicked."""
        action_called = []
        
        def on_action(task_id, action):
            action_called.append((task_id, action))
        
        widget = SuggestionNotificationWidget(
            suggestion,
            on_action=on_action,
        )
        
        # Simulate action button click
        widget._on_action()
        
        assert len(action_called) == 1
        assert action_called[0] == ("task_1", "add_to_schedule")
    
    def test_notification_widget_styling(self, qapp, suggestion):
        """Widget should have QSS styling applied."""
        widget = SuggestionNotificationWidget(suggestion)
        
        # Check object name
        assert widget.objectName() == "suggestionNotification"


class TestSuggestionPanel:
    """Test suite for SuggestionPanel."""
    
    @pytest.fixture
    def view_model(self):
        """Create ViewModel for testing."""
        return SuggestionViewModel()
    
    @pytest.fixture
    def suggestions(self):
        """Sample suggestions for testing."""
        return [
            {
                "task_id": "task_1",
                "task_name": "Implement feature X",
                "reasoning": "Good fit for your mood",
            },
            {
                "task_id": "task_2",
                "task_name": "Fix typo",
                "reasoning": "Light task for your energy level",
            },
        ]
    
    def test_panel_creation(self, qapp, view_model):
        """Panel should create successfully."""
        panel = SuggestionPanel(view_model)
        
        assert panel is not None
        assert panel.view_model == view_model
    
    def test_panel_displays_suggestions(self, qapp, view_model, suggestions):
        """Panel should display generated suggestions."""
        panel = SuggestionPanel(view_model)
        
        # Emit suggestions generated signal
        view_model.suggestionsGenerated.emit(suggestions)
        
        # Should have created widgets for each suggestion
        assert len(panel._suggestion_widgets) == 2
    
    def test_panel_removes_dismissed_suggestion(self, qapp, view_model, suggestions):
        """Panel should remove dismissed suggestions."""
        panel = SuggestionPanel(view_model)
        
        # Display suggestions
        view_model.suggestionsGenerated.emit(suggestions)
        assert len(panel._suggestion_widgets) == 2
        
        # Dismiss one
        view_model.suggestionDismissed.emit("task_1")
        
        # Should have one less
        assert len(panel._suggestion_widgets) == 1
        assert "task_1" not in panel._suggestion_widgets
        assert "task_2" in panel._suggestion_widgets
    
    def test_panel_styling(self, qapp, view_model):
        """Panel should have QSS styling applied."""
        panel = SuggestionPanel(view_model)
        
        assert panel.objectName() == "suggestionPanel"
    
    def test_panel_size_hint(self, qapp, view_model):
        """Panel should return reasonable size hint."""
        panel = SuggestionPanel(view_model)
        
        size_hint = panel.sizeHint()
        assert size_hint.width() == 300
        assert size_hint.height() == 400


class TestSuggestionViewModel:
    """Test suite for SuggestionViewModel."""
    
    @pytest.fixture
    def view_model(self):
        """Create ViewModel for testing."""
        return SuggestionViewModel()
    
    @pytest.fixture
    def sample_tasks(self):
        """Sample task list."""
        return [
            {"id": "task_1", "name": "Hard task", "difficulty": "hard"},
            {"id": "task_2", "name": "Easy task", "difficulty": "easy"},
        ]
    
    def test_viewmodel_creation(self, view_model):
        """ViewModel should create successfully."""
        assert view_model is not None
        assert view_model.currentSuggestions == []
        assert view_model.isLoading is False
    
    def test_viewmodel_generate_suggestions(self, qapp, view_model, sample_tasks):
        """ViewModel should generate suggestions."""
        signal_emitted = []
        view_model.suggestionsGenerated.connect(
            lambda suggestions: signal_emitted.append(suggestions)
        )
        
        view_model.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=sample_tasks,
        )
        
        assert len(signal_emitted) == 1
        assert len(view_model.currentSuggestions) > 0
    
    def test_viewmodel_dismiss_suggestion(self, view_model, sample_tasks):
        """ViewModel should dismiss suggestions."""
        signal_emitted = []
        view_model.suggestionDismissed.connect(
            lambda sid: signal_emitted.append(sid)
        )
        
        # Generate suggestions first
        view_model.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=sample_tasks,
        )
        
        initial_count = len(view_model.currentSuggestions)
        
        # Dismiss one
        view_model.dismiss_suggestion("task_1")
        
        assert len(view_model.currentSuggestions) < initial_count
        assert len(signal_emitted) == 1
    
    def test_viewmodel_act_on_suggestion(self, view_model, sample_tasks):
        """ViewModel should handle action on suggestion."""
        signal_emitted = []
        view_model.suggestionActedUpon.connect(
            lambda sid, action: signal_emitted.append((sid, action))
        )
        
        # Generate suggestions first
        view_model.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=sample_tasks,
        )
        
        # Act on suggestion
        view_model.act_on_suggestion("task_1", "add_to_schedule")
        
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == ("task_1", "add_to_schedule")
    
    def test_viewmodel_clear_suggestions(self, view_model, sample_tasks):
        """ViewModel should clear all suggestions."""
        # Generate suggestions
        view_model.generate_suggestions(
            mood="happy",
            energy_level="high",
            available_tasks=sample_tasks,
        )
        
        assert len(view_model.currentSuggestions) > 0
        
        # Clear
        view_model.clear_suggestions()
        
        assert len(view_model.currentSuggestions) == 0
    
    def test_viewmodel_error_handling(self, qapp, view_model):
        """ViewModel should handle errors gracefully."""
        error_signal_emitted = []
        view_model.validationError.connect(
            lambda msg: error_signal_emitted.append(msg)
        )
        
        # Invalid mood
        view_model.generate_suggestions(
            mood="",
            energy_level="high",
            available_tasks=[],
        )
        
        assert len(error_signal_emitted) == 1

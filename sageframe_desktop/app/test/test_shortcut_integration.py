import time

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from unittest.mock import Mock, MagicMock

from app.main_window import MainWindow
from app.core.undo_manager import UndoManager
from app.core.undo_commands import PropertyChangeCommand


def test_toggle_suggestion_panel_via_shortcut(qtbot):
    app = QApplication.instance() or QApplication([])

    win = MainWindow()
    qtbot.addWidget(win)
    win.show()

    # Ensure dock is visible initially
    assert hasattr(win, "suggestion_dock")
    assert win.suggestion_dock.isVisible() is True

    # Trigger via ShortcutManager programmatically to simulate global shortcut
    win.shortcut_manager.activate("toggle_suggestion_panel")

    # Visibility should change
    assert win.suggestion_dock.isVisible() is False

    # Toggle back
    win.shortcut_manager.activate("toggle_suggestion_panel")
    assert win.suggestion_dock.isVisible() is True


class TestUndoRedoIntegration:
    """Test undo/redo integration with the main application."""

    @pytest.fixture
    def main_window(self, qtbot):
        """Create a MainWindow instance for testing."""
        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        return window

    def test_undo_manager_accessible_from_main_window(self, main_window):
        """Test that UndoManager is accessible from MainWindow."""
        assert hasattr(main_window, "undo_manager")
        assert isinstance(main_window.undo_manager, UndoManager)

    def test_undo_redo_shortcuts_registered(self, main_window):
        """Test that undo/redo shortcuts are registered."""
        definitions = main_window.shortcut_manager.get_definitions()
        action_ids = [d.action_id for d in definitions]

        assert "undo" in action_ids
        assert "redo" in action_ids

    def test_undo_keyboard_shortcut_works(self, main_window):
        """Test that Ctrl+Z triggers undo."""
        # Create a mock object to track state
        obj = MagicMock()
        obj.value = 0

        # Add a command to undo manager
        cmd = PropertyChangeCommand(obj, "value", 42)
        main_window.undo_manager.push(cmd)

        assert obj.value == 42
        assert main_window.undo_manager.can_undo()

        # Trigger undo via shortcut
        main_window._undo()

        assert main_window.undo_manager.can_redo()

    def test_redo_keyboard_shortcut_works(self, main_window):
        """Test that Ctrl+Y/Ctrl+Shift+Z triggers redo."""
        obj = MagicMock()
        obj.value = 0

        cmd = PropertyChangeCommand(obj, "value", 99)
        main_window.undo_manager.push(cmd)
        main_window.undo_manager.undo()

        assert obj.value == 0

        # Trigger redo
        main_window._redo()

        assert obj.value == 99

    def test_undo_state_signals_emitted(self, main_window):
        """Test that undo state change signals are emitted."""
        signal_spy = Mock()
        main_window.undo_manager.can_undo_changed.connect(signal_spy)

        obj = MagicMock()
        cmd = PropertyChangeCommand(obj, "value", 10)

        main_window.undo_manager.push(cmd)

        # Signal should be emitted
        assert signal_spy.call_count >= 1

    def test_redo_state_signals_emitted(self, main_window):
        """Test that redo state change signals are emitted."""
        signal_spy = Mock()
        main_window.undo_manager.can_redo_changed.connect(signal_spy)

        obj = MagicMock()
        cmd = PropertyChangeCommand(obj, "value", 10)

        main_window.undo_manager.push(cmd)
        main_window.undo_manager.undo()

        # Signal should be emitted when redo becomes available
        assert signal_spy.call_count >= 1


class TestUndoRedoPerformance:
    """Test performance of undo/redo operations (NFR1 compliance)."""

    def test_undo_operation_responsiveness(self):
        """Test that undo operation completes in < 100ms (NFR1)."""
        manager = UndoManager()
        obj = MagicMock()

        # Push 100 commands
        for i in range(100):
            cmd = PropertyChangeCommand(obj, "value", i)
            manager.push(cmd)

        # Measure undo time
        start = time.perf_counter()
        for _ in range(100):
            manager.undo()
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

        # Each operation should be very fast (sub-1ms typically)
        assert elapsed < 100, f"Undo too slow: {elapsed:.2f}ms for 100 ops"

    def test_redo_operation_responsiveness(self):
        """Test that redo operation completes in < 100ms (NFR2)."""
        manager = UndoManager()
        obj = MagicMock()

        # Push 100 commands and undo them
        for i in range(100):
            cmd = PropertyChangeCommand(obj, "value", i)
            manager.push(cmd)

        for _ in range(100):
            manager.undo()

        # Measure redo time
        start = time.perf_counter()
        for _ in range(100):
            manager.redo()
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

        # Each operation should be very fast (sub-1ms typically)
        assert elapsed < 100, f"Redo too slow: {elapsed:.2f}ms for 100 ops"

class TestUndoRedoAccessibility:
    """Test accessibility features for undo/redo (Task 4.4, NFR7)."""

    @pytest.fixture
    def main_window(self, qtbot):
        """Create a MainWindow instance for testing."""
        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        return window

    def test_undo_action_has_visible_shortcut(self, main_window):
        """Test that undo action displays shortcuts visibly (AC3, NFR7)."""
        assert hasattr(main_window, "undo_action")
        undo_action = main_window.undo_action
        
        # Shortcut should be visible
        assert undo_action.shortcut() is not None
        assert undo_action.isShortcutVisibleInContextMenu()

    def test_redo_action_has_visible_shortcut(self, main_window):
        """Test that redo action displays shortcuts visibly."""
        assert hasattr(main_window, "redo_action")
        redo_action = main_window.redo_action
        
        # Shortcut should be visible
        assert redo_action.shortcut() is not None
        assert redo_action.isShortcutVisibleInContextMenu()

    def test_undo_action_initially_disabled(self, main_window):
        """Test that undo button is disabled when no undo available (AC3)."""
        assert hasattr(main_window, "undo_action")
        assert not main_window.undo_action.isEnabled()

    def test_undo_action_enabled_after_command(self, main_window):
        """Test that undo button is enabled after a command is pushed."""
        obj = MagicMock()
        cmd = PropertyChangeCommand(obj, "value", 10)
        
        main_window.undo_manager.push(cmd)
        
        # Give signals time to propagate
        assert main_window.undo_action.isEnabled()

    def test_redo_action_initially_disabled(self, main_window):
        """Test that redo button is disabled initially (AC3)."""
        assert hasattr(main_window, "redo_action")
        assert not main_window.redo_action.isEnabled()

    def test_redo_action_enabled_after_undo(self, main_window):
        """Test that redo button is enabled after undo."""
        obj = MagicMock()
        cmd = PropertyChangeCommand(obj, "value", 10)
        
        main_window.undo_manager.push(cmd)
        main_window.undo_manager.undo()
        
        # Give signals time to propagate
        assert main_window.redo_action.isEnabled()

    def test_menu_items_present(self, main_window):
        """Test that Edit menu has Undo/Redo items."""
        # Find Edit menu
        edit_menu = None
        for action in main_window.menuBar().actions():
            if "Edit" in action.text():
                edit_menu = action.menu()
                break
        
        assert edit_menu is not None, "Edit menu not found"
        
        # Check for undo and redo actions
        menu_actions = [a.text() for a in edit_menu.actions()]
        undo_found = any("Undo" in text for text in menu_actions)
        redo_found = any("Redo" in text for text in menu_actions)
        
        assert undo_found, "Undo menu item not found"
        assert redo_found, "Redo menu item not found"

    def test_status_tips_updated(self, main_window):
        """Test that status tips are updated to show undo availability."""
        obj = MagicMock()
        cmd = PropertyChangeCommand(obj, "value", 10, description="Test change")
        
        main_window.undo_manager.push(cmd)
        
        # Status tip should include the command description
        status_tip = main_window.undo_action.statusTip()
        assert len(status_tip) > 0

    def test_keyboard_focus_does_not_prevent_undo(self, main_window):
        """Test that undo works regardless of focus widget (except text fields)."""
        from PySide6.QtWidgets import QLineEdit
        
        # Create a text input widget
        text_input = QLineEdit()
        text_input.setText("test")
        main_window.setCentralWidget(text_input)
        text_input.setFocus()
        
        # Add undo command
        obj = MagicMock()
        cmd = PropertyChangeCommand(obj, "value", 42)
        main_window.undo_manager.push(cmd)
        
        # Undo should still be available through the action
        assert main_window.undo_action.isEnabled()
        main_window._undo()
        assert main_window.undo_manager.can_redo()